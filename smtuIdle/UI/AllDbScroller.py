import sys

from PySide6.QtWidgets import *
from peewee import SqliteDatabase

from smtuIdle.BD.models import *
from PySide6.QtCore import Qt, QTimer, QSize,QEvent
from PySide6.QtGui import QIcon,QFont
from PySide6.QtCore import QDate
from peewee import JOIN
from smtuIdle.InsertWidgetCurrency import InsertWidgetCurrency
from smtuIdle.parserV3 import delete_records_by_id, export_to_excel,export_to_excel_contract
from PySide6.QtWidgets import QSizePolicy
from peewee import fn
from locale import format_string
import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

db = SqliteDatabase('database.db')
cursor = db.cursor()

class _FlexTabBar(QTabBar):
    def __init__(self, spacer_index: int, parent=None):
        super().__init__(parent)
        self._spacer_index = spacer_index

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        if index == self._spacer_index:
            # Берем доступную ширину от родительского QTabWidget
            if self.parentWidget():
                total = self.parentWidget().width()
                # Считаем ширину всех остальных (настоящих) вкладок
                used = sum(
                    super(_FlexTabBar, self).tabSizeHint(i).width()
                    for i in range(self.count())
                    if i != self._spacer_index
                )
                # Вычитаем 5px на отступы, чтобы не появлялись стрелки прокрутки
                size.setWidth(max(0, total - used - 5))
        return size

    def eventFilter(self, watched, event):
        # Отлавливаем изменение размера самого QTabWidget, чтобы обновлять спейсер
        if watched == self.parentWidget() and event.type() == QEvent.Type.Resize:
            if self.count() > self._spacer_index:
                # Трюк: обновление текста принудительно пересчитывает размеры вкладок
                self.setTabText(self._spacer_index, '')
        return super().eventFilter(watched, event)
class PurchasesWidgetAll(QWidget):
    def __init__(self,main, role):
        super().__init__()
        # self.main_win = main_window
        self.selected_text = None
        self.selected_text_contract = None
        self.main_window = main
        self.role = role
        self.purchases_list = []
        self.contracts_list = []
        self.contracts = Contract.select()  # ← добавить эту строку

        # Создаем компонент вкладок
        tab_widget = QTabWidget()

        # Передаем tab_widget как parent и устанавливаем EventFilter
        flex_bar = _FlexTabBar(spacer_index=2, parent=tab_widget)
        tab_widget.setTabBar(flex_bar)
        tab_widget.installEventFilter(flex_bar)

        tab_widget.addTab(self.create_purch_tab(), 'Закупки')  # 0
        tab_widget.addTab(self.create_cont_tab(), 'Контракты')  # 1

        # Индекс 2 — невидимая вкладка-спейсер
        tab_widget.addTab(QWidget(), '')
        tab_widget.setTabEnabled(2, False)
        tab_widget.setStyleSheet('QTabBar::tab:disabled { background: transparent; border: none; }')

        tab_widget.addTab(self.create_supplier_tab(), 'Поставщики')  # 3
        tab_widget.addTab(self.create_customer_tab(), 'Заказчики')  # 4
        tab_widget.addTab(self.create_vessel_tab(), 'Данные по объекту закупки')  # 5

        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def create_purch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(10)

        self.table.setColumnWidth(9, 120)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)

        # Устанавливаем заголовки колонок
        column_headers = ["№ПП", "Закон", "Реестровый номер", "Дата размещения",
                          "Наименование закупки", "Предмет аукциона", "НМЦК",
                          "Валюта", "Наименование заказчика","Ссылка на контракт"]
        self.table.resizeColumnsToContents()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalHeaderLabels(column_headers)
        self.table.setColumnWidth(4, 600)
        self.table.setColumnWidth(8, 600)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Затем устанавливаем режим изменения размера колонки "Наименование закупки" на фиксированный размер
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setTextElideMode(Qt.ElideRight)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.setWordWrap(True)
        
     
        self.current_position = 0   
        self.label = QLabel("Всего записей", self)
        self.table.cellClicked.connect(self.handle_cell_click)
         
         # Создаем выпадающее меню
        self.sort_options = QComboBox()
        self.sort_options.addItems(["Сортировать по цене (возрастание)", "Сортировать по цене (убывание)",
                                    
                                    "Сортировать по дате (от старых к новым)","Сортировать по дате (от новых к старым)"])
         # Устанавливаем обработчик событий для выпадающего меню
       
        self.sort_options.setFixedWidth(250)
        self.sort_options.currentIndexChanged.connect(self.highlight_current_item)
        unique_purchase_orders = Purchase.select(Purchase.PurchaseOrder).distinct()
        self.sort_by_putch_order = QComboBox()
        self.sort_by_putch_order.addItem("Фильтрация по закону")
        self.sort_by_putch_order.setFixedWidth(250)
        self.sort_by_putch_order.currentIndexChanged.connect(self.highlight_current_item)
        for order in unique_purchase_orders:
            self.sort_by_putch_order.addItem(str(order.PurchaseOrder))


      
        unique_purchase_OKPD2 = Purchase.select(Purchase.OKPD2Classification).distinct().order_by(fn.Lower(Purchase.OKPD2Classification))
        self.sort_by_putch_okpd2 = QComboBox()
        self.sort_by_putch_okpd2.addItem("Фильтрация по ОКПД2")
        self.sort_by_putch_okpd2.setFixedWidth(250)
        for order in unique_purchase_OKPD2:
            self.sort_by_putch_okpd2.addItem(str(order.OKPD2Classification))

        unique_purchase_CustomerName = Purchase.select(Purchase.CustomerName).distinct().order_by(fn.Lower(Purchase.CustomerName))
        self.sort_by_putch_CustomerName = QComboBox()
        self.sort_by_putch_CustomerName.addItem("Фильтрация по заказчикам")
        self.sort_by_putch_CustomerName.setFixedWidth(500)
        for order in unique_purchase_CustomerName:
            self.sort_by_putch_CustomerName.addItem(str(order.CustomerName))

        self.transparent_style = "QDateEdit { color: transparent; }"

        unique_purchase_ProcurementMethod = Purchase.select(Purchase.ProcurementMethod).distinct().order_by(fn.Lower(Purchase.ProcurementMethod))
        self.sort_by_putch_ProcurementMethod = QComboBox()
        self.sort_by_putch_ProcurementMethod.addItem("Фильтрация по методу закупки")
        self.sort_by_putch_ProcurementMethod.setFixedWidth(250)
        for order in unique_purchase_ProcurementMethod:
            self.sort_by_putch_ProcurementMethod.addItem(str(order.ProcurementMethod))
        # Создаем метки и поля для ввода минимальной и максимальной цены
        self.sort_by_putch_okpd2.currentIndexChanged.connect(self.highlight_current_item)
        self.min_price_label = QLabel("Минимальная цена")
        self.min_price_input = QLineEdit()
        self.min_price_input.setFixedWidth(100)
        self.max_price_label = QLabel("Максимальная цена (в рублях)")
        self.max_price_input = QLineEdit()
        self.max_price_input.setFixedWidth(100)
        self.toExcel = QPushButton("Экспорт в Excel данных по закупке", self)
        self.toExcel.clicked.connect(self.export_to_excel_clicked)
        self.toExcel.setFixedWidth(400)

        self.min_data_label = QLabel("Начальная дата")
        self.min_data_input = QDateEdit()
        self.min_data_input.setCalendarPopup(False)
        self.min_data_input.setStyleSheet(self.transparent_style)
        # self.min_data_input.setDate(self.min_data_input.date().currentDate())

        self.min_data_input.clear()
        self.min_data_input.setFixedWidth(150)
        self.min_data_input.setCalendarPopup(True)
        self.max_data_label = QLabel("Конечная дата")
        self.max_data_input = QDateEdit()
        self.max_data_input.setCalendarPopup(True)
        self.max_data_input.setDate(self.max_data_input.date().currentDate())
        self.max_data_input.setStyleSheet(self.transparent_style) 
        button_layout3 = QHBoxLayout()
        button_layout3.addWidget(self.toExcel)
        button_layout3.setAlignment(Qt.AlignHCenter)
        self.max_data_input.setFixedWidth(150)
         #  кнопка "Сбросить фильтры" 
        self.reset_filters_button = QPushButton("Сбросить фильтры", self)
        self.reset_filters_button.setFixedWidth(150)
        self.reset_filters_button.clicked.connect(self.resetFilters)
        # Создаем поле ввода для поиска
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по Реестровому номеру, заказчику, наименованию объекта или организации")
        self.unique_values_query = self.findUnic()
        self.search_input.setFixedWidth(600)
        completer = QCompleter(self.unique_values_query )
        # self.search_input.textChanged.connect(completer.filter)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated.connect(self.handleActivated)
        self.search_input.setCompleter(completer)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.label)
        icon_path = "../Pics/icons8-фильтр-ios-17-32.png"
        self.label.setAlignment(Qt.AlignHCenter)
        icon = QIcon(icon_path)
        # Добавляем горизонтальную линию
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)  # Форма линии (горизонтальная)
        line.setFrameShadow(QFrame.Shadow.Sunken)  # Тень линии
        line.setStyleSheet("background-color: grey;")  # Цвет фона
        line.setFixedHeight(2)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setStyleSheet("background-color: grey;")
        line1.setFixedHeight(2)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setStyleSheet("background-color: grey;")
        line2.setFixedHeight(2)

        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        line3.setStyleSheet("background-color: grey;")
        line3.setFixedHeight(2)
        # Добавляем кнопку "Применить фильтр"
        self.apply_filter_button = QPushButton("Применить фильтр", self)
        self.apply_filter_button.setIcon(icon)
        self.apply_filter_button.clicked.connect(self.apply_filter)
        self.apply_filter_button.setFixedWidth(150)
        # Добавляем кнопку выпадающего меню по ключевому слову
        self.QwordFinder = QPushButton("Поиск по ключевому слову")
        self.QwordFinder.setIcon(QIcon("../Pics/right-arrow.png"))
        self.QwordFinder.setMaximumWidth(300)
        self.QwordFinder.clicked.connect(self.toggle_menu)
        # Добавляем кнопку выпадающего меню по фильтрам
        self.FilterCollapse = QPushButton("Фильтры")
        self.FilterCollapse.setIcon(QIcon("../Pics/right-arrow.png"))
        self.FilterCollapse.setMaximumWidth(300)
        self.FilterCollapse.clicked.connect(self.toggle_menu_filters)
         # Добавляем кнопку выпадающего меню по цене
        self.FilterPrice = QPushButton("Цена")
        self.FilterPrice.setIcon(QIcon("../Pics/right-arrow.png"))
        self.FilterPrice.setMaximumWidth(300)
        self.FilterPrice.clicked.connect(self.toggle_menu_price)
        # Добавляем кнопку выпадающего меню по дате
        self.FilterDate = QPushButton("Дата")
        self.FilterDate.setIcon(QIcon("../Pics/right-arrow.png"))
        self.FilterDate.setMaximumWidth(300)
        self.FilterDate.clicked.connect(self.toggle_menu_date)
        #меню по ключевому слову
        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        self.Qword = QLabel("Поиск по ключевому слову")
        menu_layout.addWidget(line)
        menu_layout.addWidget(self.Qword)
        menu_layout.addWidget(self.search_input)
        
        self.menu_content.setLayout(menu_layout)
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(QVBoxLayout())
        self.menu_frame.layout().addWidget(self.menu_content)
        self.menu_frame.setVisible(False)
        self.sort_by_putch_ProcurementMethod.currentIndexChanged.connect(self.highlight_current_item)
        self.sort_by_putch_CustomerName.currentIndexChanged.connect(self.highlight_current_item)
        #меню по ключевому фильтрам
        self.menu_content_filters = QWidget()
        menu_layout_filters = QHBoxLayout()
        self.FilterLable = QLabel("Расшириная фильтрация по справочникам")
        menu_layout_filtersH = QVBoxLayout()
        menu_layout_filtersH.addWidget(line1)
        menu_layout_filtersH.addWidget(self.FilterLable)
        menu_layout_filters.addWidget(self.sort_options)
        menu_layout_filters.addWidget(self.sort_by_putch_order)
        menu_layout_filters.addWidget(self.sort_by_putch_okpd2)
        menu_layout_filters.addWidget(self.sort_by_putch_ProcurementMethod)
        menu_layout_filters.addWidget(self.sort_by_putch_CustomerName)
        menu_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        menu_layout_filtersH.addLayout(menu_layout_filters)
        self.menu_content_filters.setLayout(menu_layout_filtersH)
        self.menu_frame_filters = QFrame()
        self.menu_frame_filters.setLayout(QVBoxLayout())
        self.menu_frame_filters.layout().addWidget(self.menu_content_filters)
        self.menu_frame_filters.setVisible(False)
        #меню по  фильтрам цена
        self.menu_content_price = QWidget()
        menu_layout_price = QHBoxLayout()
        menu_layout_priceV = QVBoxLayout()
        self.PriceLabel = QLabel("Фильтрация по НМЦК")
        menu_layout_priceV.addWidget( self.PriceLabel)
        menu_layout_priceV.addWidget(line2)
        menu_layout_price.addWidget(self.min_price_label)
        menu_layout_price.addWidget(self.min_price_input)
        menu_layout_price.addWidget(self.max_price_label)
        menu_layout_price.addWidget(self.max_price_input)
        menu_layout_priceV.addLayout(menu_layout_price)
        menu_layout_price.setAlignment(Qt.AlignmentFlag.AlignLeft)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        menu_layout_price.addItem(spacer)
        self.menu_content_price.setLayout(menu_layout_priceV)
        self.menu_frame_price = QFrame()
        self.menu_frame_price.setLayout(QVBoxLayout())
        self.menu_frame_price.layout().addWidget(self.menu_content_price)
        self.menu_frame_price.setVisible(False)
        #меню по  фильтрам дата
        self.menu_content_data = QWidget()
        menu_layout_data = QHBoxLayout()
        DataLabel = QLabel("Фильтрация по дате размещения")
        menu_layout_dataV = QVBoxLayout()
        menu_layout_dataV.addWidget(DataLabel)
        menu_layout_dataV.addWidget(line3)
        menu_layout_data.addWidget(self.min_data_label)
        menu_layout_data.addWidget(self.min_data_input)
        menu_layout_data.addWidget(self.max_data_label)
        menu_layout_data.addWidget(self.max_data_input)
        menu_layout_data.setAlignment(Qt.AlignmentFlag.AlignLeft)
        menu_layout_dataV.addLayout(menu_layout_data)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        menu_layout_data.addItem(spacer)
        self.menu_content_data.setLayout(menu_layout_dataV)
        self.menu_frame_data = QFrame()
        self.menu_frame_data.setLayout(QVBoxLayout())
        self.menu_frame_data.layout().addWidget(self.menu_content_data)
        self.menu_frame_data.setVisible(False)
       # Создаем горизонтальный макет и добавляем элементы
        
        self.All_parametrs_finder = QLabel("Все параметры поиска")
        font = QFont()
        font.setPointSize(16)
        
        # Устанавливаем созданный шрифт для QLabel
        self.All_parametrs_finder.setFont(font)
        # layout.addWidget(self.search_input)
        button_layout_filters = QHBoxLayout()
        button_layout_filters.addWidget(self.QwordFinder)
        button_layout_filters.addWidget(self.FilterCollapse)
        button_layout_filters.addWidget(self.FilterPrice)
        button_layout_filters.addWidget(self.FilterDate)
        button_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.All_parametrs_finder,alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(button_layout_filters)
        layout.addWidget(self.menu_frame)
        layout.addWidget(self.menu_frame_filters)
        layout.addWidget(self.menu_frame_price)
        layout.addWidget(self.menu_frame_data)


        # Добавляем кнопку "Применить фильтр"
        button_layout_filters = QHBoxLayout()
        button_layout_filters.addWidget(self.apply_filter_button)
        button_layout_filters.addWidget(self.reset_filters_button)
        button_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(button_layout_filters)
        # Добавляем таблицу и остальные элементы в макет
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addLayout(button_layout3)
        # Получаем данные из базы данных и отображаем первую запись
        self.reload_data()
        self.min_price_input.textChanged.connect(self.highlight_input)
        self.max_price_input.textChanged.connect(self.highlight_input)
        self.min_data_input.dateChanged.connect(self.highlight_input)
        self.max_data_input.dateChanged.connect(self.highlight_input)
        self.search_input.textChanged.connect(self.highlight_input)
        self.apply_filter_button.clicked.connect(self.highlight_apply_filter_button)


        if self.role == "Гость":
            self.toExcel.hide()
        else:
            self.toExcel.show()
        return tab

    def create_cont_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.table_cont = QTableWidget(self)
        self.table_cont.setColumnCount(13)
        column_headers = [
            "№ПП",
            "Рееестр. № договора",
            "Рееестр. № закупки",
            "Номер контракта",
            "Дата начала",
            "Дата окончания",
            "Цена контракта",
            "НМЦК",
            "Разница",
            "Снижение %",
            "Заказчик по контракту",
            "Исполнитель",
            "Наименование закупки",
        ]
        self.table_cont.setHorizontalHeaderLabels(column_headers)
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for col in (10, 11, 12):
            self.table_cont.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
            self.table_cont.setColumnWidth(col, 400)
        self.table_cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_cont.setShowGrid(True)
        self.table_cont.verticalHeader().setVisible(False)
        self.table_cont.setWordWrap(True)
        self.table_cont.setTextElideMode(Qt.ElideRight)
        self.table_cont.cellClicked.connect(self.handle_cell_click_contract)

        self.label_cont = QLabel("Всего записей", self)
        self.label_cont.setAlignment(Qt.AlignHCenter)
        self.transparent_style = "QDateEdit { color: transparent; }"

        # ── Поиск ────────────────────────────────────────────
        self.search_input_contract = QLineEdit()
        self.search_input_contract.setPlaceholderText(
            "Поиск по исполнителю, заказчику, реестровому номеру"
        )

        self.search_input_contract.setFixedWidth(500)
        self.search_input_contract.textChanged.connect(self.highlight_input_contract)
        completer = QCompleter(self.findUnicContract())
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.activated.connect(self.handleActivatedContract)
        self.search_input_contract.setCompleter(completer)

        # ── Фильтры ───────────────────────────────────────────
        self.sort_options_contract = QComboBox()
        self.sort_options_contract.addItems([
            "Сортировать по цене (возрастание)",
            "Сортировать по цене (убывание)",
            "Сортировать по дате (от старых к новым)",
            "Сортировать по дате (от новых к старым)",
        ])
        self.sort_options_contract.setFixedWidth(250)
        self.sort_options_contract.currentIndexChanged.connect(self.highlight_current_item_contract)

        self.sort_by_putch_winner = QComboBox()
        self.sort_by_putch_winner.addItem("Фильтрация по исполнителю")
        self.sort_by_putch_winner.setFixedWidth(250)
        for s in (
                Supplier
                        .select(Supplier.organization)
                        .join(SupplierContract, on=(SupplierContract.supplier == Supplier.id))
                        .distinct()
                        .order_by(fn.Lower(Supplier.organization))
        ):
            if s.organization:
                self.sort_by_putch_winner.addItem(str(s.organization))
        self.sort_by_putch_winner.currentIndexChanged.connect(self.highlight_current_item_contract)

        # ── Цена ──────────────────────────────────────────────
        self.min_price_input_contrac = QLineEdit()
        self.min_price_input_contrac.setFixedWidth(120)
        self.min_price_input_contrac.setPlaceholderText("Мин. цена")
        self.max_price_input_contrac = QLineEdit()
        self.max_price_input_contrac.setFixedWidth(120)
        self.max_price_input_contrac.setPlaceholderText("Макс. цена")
        self.min_price_input_contrac.textChanged.connect(self.highlight_input_contract)
        self.max_price_input_contrac.textChanged.connect(self.highlight_input_contract)

        # ── Дата ──────────────────────────────────────────────
        self.min_data_input_contrac = QDateEdit()
        self.min_data_input_contrac.setCalendarPopup(True)
        self.min_data_input_contrac.setStyleSheet(self.transparent_style)
        self.min_data_input_contrac.setFixedWidth(150)
        self.max_data_input_contrac = QDateEdit()
        self.max_data_input_contrac.setCalendarPopup(True)
        self.max_data_input_contrac.setDate(self.max_data_input_contrac.date().currentDate())
        self.max_data_input_contrac.setStyleSheet(self.transparent_style)
        self.max_data_input_contrac.setFixedWidth(150)
        self.min_data_input_contrac.dateChanged.connect(self.highlight_input_contract)
        self.max_data_input_contrac.dateChanged.connect(self.highlight_input_contract)

        # ── Кнопки ────────────────────────────────────────────
        self.apply_filter_button_contract = QPushButton("Применить фильтры")
        self.apply_filter_button_contract.setIcon(QIcon("../Pics/icons8-фильтр-ios-17-32.png"))
        self.apply_filter_button_contract.setFixedWidth(200)
        self.apply_filter_button_contract.clicked.connect(self.apply_filter_contract)
        self.apply_filter_button_contract.clicked.connect(self.highlight_apply_filter_button_contract)

        self.reset_filters_button_contract = QPushButton("Сбросить фильтры")
        self.reset_filters_button_contract.setFixedWidth(200)
        self.reset_filters_button_contract.clicked.connect(self.resetFiltersContract)

        self.toExcel_contract = QPushButton("Экспорт в Excel данных по контракту")
        self.toExcel_contract.setFixedWidth(400)
        self.toExcel_contract.clicked.connect(self.export_to_excel_clicked_contract)

        # ── Сворачиваемые панели ──────────────────────────────
        icon_right = QIcon("../Pics/right-arrow.png")
        icon_down = QIcon("../Pics/arrow-down.png")

        def make_toggle_btn(label):
            btn = QPushButton(label)
            btn.setIcon(icon_right)
            btn.setMaximumWidth(300)
            return btn

        self.QwordFinderContract = make_toggle_btn("Поиск по ключевому слову")
        self.FilterCollapseContract = make_toggle_btn("Фильтры")
        self.FilterPriceContract = make_toggle_btn("Цена")
        self.FilterDateContract = make_toggle_btn("Дата")

        # Панель: поиск
        panel_search = QWidget()
        pl = QVBoxLayout(panel_search)
        pl.addWidget(QLabel("Поиск по ключевому слову"))
        pl.addWidget(self.search_input_contract)
        self.menu_frame_contract = QFrame()
        self.menu_frame_contract.setLayout(QVBoxLayout())
        self.menu_frame_contract.layout().addWidget(panel_search)
        self.menu_frame_contract.setVisible(False)

        # Панель: фильтры
        panel_filters = QWidget()
        pfl = QHBoxLayout(panel_filters)
        pfl.addWidget(self.sort_options_contract)
        pfl.addWidget(self.sort_by_putch_winner)
        pfl.setAlignment(Qt.AlignLeft)
        self.menu_frame_filters_contract = QFrame()
        self.menu_frame_filters_contract.setLayout(QVBoxLayout())
        self.menu_frame_filters_contract.layout().addWidget(panel_filters)
        self.menu_frame_filters_contract.setVisible(False)

        # Панель: цена
        panel_price = QWidget()
        ppr = QHBoxLayout(panel_price)
        ppr.addWidget(QLabel("Мин. цена:"));
        ppr.addWidget(self.min_price_input_contrac)
        ppr.addWidget(QLabel("Макс. цена:"));
        ppr.addWidget(self.max_price_input_contrac)
        ppr.setAlignment(Qt.AlignLeft)
        self.menu_frame_price_contrac = QFrame()
        self.menu_frame_price_contrac.setLayout(QVBoxLayout())
        self.menu_frame_price_contrac.layout().addWidget(panel_price)
        self.menu_frame_price_contrac.setVisible(False)

        # Панель: дата
        panel_date = QWidget()
        pdt = QHBoxLayout(panel_date)
        pdt.addWidget(QLabel("Начало:"));
        pdt.addWidget(self.min_data_input_contrac)
        pdt.addWidget(QLabel("Конец:"));
        pdt.addWidget(self.max_data_input_contrac)
        pdt.setAlignment(Qt.AlignLeft)
        self.menu_frame_data_contrac = QFrame()
        self.menu_frame_data_contrac.setLayout(QVBoxLayout())
        self.menu_frame_data_contrac.layout().addWidget(panel_date)
        self.menu_frame_data_contrac.setVisible(False)

        # Подключаем toggle
        self.QwordFinderContract.clicked.connect(self.toggle_menu_contract)
        self.FilterCollapseContract.clicked.connect(self.toggle_menu_filters_contract)
        self.FilterPriceContract.clicked.connect(self.toggle_menu_price_contract)
        self.FilterDateContract.clicked.connect(self.toggle_menu_date_contract)

        # ── Сборка layout ─────────────────────────────────────
        header_lbl = QLabel("Все параметры поиска")
        font = QFont();
        font.setPointSize(16)
        header_lbl.setFont(font)
        layout.addWidget(header_lbl, alignment=Qt.AlignLeft)

        btn_row = QHBoxLayout()
        for b in (self.QwordFinderContract, self.FilterCollapseContract,
                  self.FilterPriceContract, self.FilterDateContract):
            btn_row.addWidget(b)
        btn_row.setAlignment(Qt.AlignLeft)
        layout.addLayout(btn_row)

        layout.addWidget(self.menu_frame_contract)
        layout.addWidget(self.menu_frame_filters_contract)
        layout.addWidget(self.menu_frame_price_contrac)
        layout.addWidget(self.menu_frame_data_contrac)

        action_row = QHBoxLayout()
        action_row.addWidget(self.apply_filter_button_contract)
        action_row.addWidget(self.reset_filters_button_contract)
        action_row.setAlignment(Qt.AlignLeft)
        layout.addLayout(action_row)

        layout.addWidget(self.table_cont)
        layout.addWidget(self.label_cont)

        excel_row = QHBoxLayout()
        excel_row.addWidget(self.toExcel_contract)
        excel_row.setAlignment(Qt.AlignHCenter)
        layout.addLayout(excel_row)

        if self.role == "Гость":
            self.toExcel_contract.hide()

        self.reload_data_cont()
        return tab

    def create_supplier_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.tablesupplier = QTableWidget(self)
        self.tablesupplier.setColumnCount(10)  # было 9
        headers = ["ID", "Организация", "ИНН", "КПП", "Страна",
                   "Адрес", "Телефон", "Email", "Статус", "Контракты"]  # добавлена колонка
        self.tablesupplier.setHorizontalHeaderLabels(headers)
        self.tablesupplier.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablesupplier.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tablesupplier.setColumnWidth(1, 400)
        self.tablesupplier.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)  # для новой колонки
        self.tablesupplier.setColumnWidth(9, 350)
        self.tablesupplier.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tablesupplier.setShowGrid(True)
        self.tablesupplier.verticalHeader().setVisible(False)
        self.tablesupplier.setWordWrap(True)
        self.labelsupplier = QLabel("", self)
        self.labelsupplier.setAlignment(Qt.AlignHCenter)

        self.searchsupplier = QLineEdit()
        self.searchsupplier.setPlaceholderText("Поиск по организации, ИНН, КПП или номеру контракта")
        self.searchsupplier.setFixedWidth(400)
        self.searchsupplier.textChanged.connect(self.apply_filter_supplier)

        btnresetsupplier = QPushButton("Сброс")
        btnresetsupplier.setFixedWidth(150)
        btnresetsupplier.clicked.connect(self.reset_supplier)

        searchlayout = QHBoxLayout()
        searchlayout.addWidget(QLabel("Поиск:"))
        searchlayout.addWidget(self.searchsupplier)
        searchlayout.addWidget(btnresetsupplier)
        searchlayout.setAlignment(Qt.AlignLeft)

        layout.addLayout(searchlayout)
        layout.addWidget(self.tablesupplier)
        layout.addWidget(self.labelsupplier)

        self.reload_supplier()
        return tab

    def create_customer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.table_customer = QTableWidget(self)
        self.table_customer.setColumnCount(8)
        headers = ["№ПП", "Наименование", "ИНН", "КПП", "ОГРН",
                   "Регион", "Город", "Закон"]
        self.table_customer.setHorizontalHeaderLabels(headers)
        self.table_customer.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_customer.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_customer.setColumnWidth(1, 500)
        self.table_customer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_customer.setShowGrid(True)
        self.table_customer.verticalHeader().setVisible(False)
        self.table_customer.setWordWrap(True)

        self.label_customer = QLabel("Всего записей", self)
        self.label_customer.setAlignment(Qt.AlignHCenter)

        # Поиск
        self.search_customer = QLineEdit()
        self.search_customer.setPlaceholderText("Поиск по наименованию, ИНН, региону")
        self.search_customer.setFixedWidth(400)
        self.search_customer.textChanged.connect(self.apply_filter_customer)

        # Фильтр по закону
        self.filter_customer_law = QComboBox()
        self.filter_customer_law.addItem("Все законы")
        for law in Customer.select(Customer.law).distinct():
            if law.law:
                self.filter_customer_law.addItem(str(law.law))
        self.filter_customer_law.setFixedWidth(150)
        self.filter_customer_law.currentIndexChanged.connect(self.apply_filter_customer)

        btn_reset_customer = QPushButton("Сбросить")
        btn_reset_customer.setFixedWidth(100)
        btn_reset_customer.clicked.connect(self.reset_customer)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_customer)
        search_layout.addWidget(self.filter_customer_law)
        search_layout.addWidget(btn_reset_customer)
        search_layout.setAlignment(Qt.AlignLeft)

        layout.addLayout(search_layout)
        layout.addWidget(self.table_customer)
        layout.addWidget(self.label_customer)

        self.reload_customer()
        return tab

    def create_vessel_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.table_vessel = QTableWidget(self)
        self.table_vessel.setColumnCount(10)
        headers = ["№ПП", "Проект судна", "Тип (РМРС)", "Класс",
                   "Год постройки", "Страна постройки", "Верфь",
                   "Дедвейт", "Реестр. номер закупки", "Сумма контракта"]
        self.table_vessel.setHorizontalHeaderLabels(headers)
        self.table_vessel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_vessel.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_vessel.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table_vessel.setColumnWidth(1, 300)
        self.table_vessel.setColumnWidth(6, 300)
        self.table_vessel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_vessel.setShowGrid(True)
        self.table_vessel.verticalHeader().setVisible(False)
        self.table_vessel.setWordWrap(True)

        self.label_vessel = QLabel("Всего записей", self)
        self.label_vessel.setAlignment(Qt.AlignHCenter)

        # Поиск
        self.search_vessel = QLineEdit()
        self.search_vessel.setPlaceholderText("Поиск по проекту, типу, верфи")
        self.search_vessel.setFixedWidth(400)
        self.search_vessel.textChanged.connect(self.apply_filter_vessel)

        # Фильтр по году
        self.filter_vessel_year = QComboBox()
        self.filter_vessel_year.addItem("Все годы")
        for v in Vessel.select(Vessel.year_built).distinct().order_by(Vessel.year_built):
            if v.year_built:
                self.filter_vessel_year.addItem(str(v.year_built))
        self.filter_vessel_year.setFixedWidth(120)
        self.filter_vessel_year.currentIndexChanged.connect(self.apply_filter_vessel)

        btn_reset_vessel = QPushButton("Сбросить")
        btn_reset_vessel.setFixedWidth(100)
        btn_reset_vessel.clicked.connect(self.reset_vessel)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_vessel)
        search_layout.addWidget(QLabel("Год:"))
        search_layout.addWidget(self.filter_vessel_year)
        search_layout.addWidget(btn_reset_vessel)
        search_layout.setAlignment(Qt.AlignLeft)

        layout.addLayout(search_layout)
        layout.addWidget(self.table_vessel)
        layout.addWidget(self.label_vessel)

        self.reload_vessel()
        return tab

    # ── Поставщики ────────────────────────────────────────────
    def reload_supplier(self):
        self.suppliersqs = Supplier.select()
        self._show_suppliers(list(self.suppliersqs))

    def apply_filter_supplier(self):
        keyword = self.search_supplier.text().strip()
        q = Supplier.select()
        if keyword:
            q = q.where(
                Supplier.organization.contains(keyword) |
                Supplier.inn.contains(keyword) |
                Supplier.kpp.contains(keyword)
            )
        self._show_suppliers(list(q))

    def reset_supplier(self):
        self.search_supplier.clear()
        self.reload_supplier()

    def _show_suppliers(self, rows: list):
        self.tablesupplier.setRowCount(0)
        self.labelsupplier.setText(f"Найдено: {len(rows)}")

        for i, s in enumerate(rows):
            # подтягиваем все контракты этого поставщика через связку
            contract_links = (SupplierContract
                              .select(Contract)
                              .join(Contract)
                              .where(SupplierContract.supplier == s.id))
            contract_labels = [
                c.contract.RegistryNumber or c.contract.ContractNumber or f"#{c.contract.Id}"
                for c in contract_links
            ]
            contracts_str = ", ".join(contract_labels) if contract_labels else "—"

            self.tablesupplier.insertRow(i)
            values = (s.id, s.organization, s.inn, s.kpp, s.country,
                      s.address, s.phone, s.mail, s.status, contracts_str)
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.tablesupplier.setItem(i, col, item)

    # ── Заказчики ─────────────────────────────────────────────
    def reload_customer(self):
        self.customers_qs = Customer.select()
        self._show_customers(list(self.customers_qs))

    def apply_filter_customer(self):
        keyword = self.searchsupplier.text().strip()
        q = Supplier.select()
        if keyword:
            # добираем поставщиков, у которых совпадает контракт (по RegistryNumber),
            # не только по полям самого поставщика
            matching_ids = (SupplierContract
                            .select(SupplierContract.supplier)
                            .join(Contract)
                            .where(Contract.RegistryNumber.contains(keyword))
                            .distinct()
                            .tuples())
            matching_ids = [row[0] for row in matching_ids]

            q = q.where(
                Supplier.organization.contains(keyword) |
                Supplier.inn.contains(keyword) |
                Supplier.kpp.contains(keyword) |
                Supplier.id.in_(matching_ids)
            )
        self._show_suppliers(list(q))


    def reset_customer(self):
            self.search_customer.clear()
            self.filter_customer_law.setCurrentIndex(0)
            self.reload_customer()

    def _show_customers(self, rows: list):
        self.table_customer.setRowCount(0)
        self.label_customer.setText(f"Всего записей: {len(rows)}")
        for i, c in enumerate(rows):
            self.table_customer.insertRow(i)
            for col, val in enumerate([
                c.id, c.name, c.inn, c.kpp, c.ogrn,
                c.region, c.city, c.law
            ]):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.table_customer.setItem(i, col, item)

    # ── Суда ──────────────────────────────────────────────────
    def reload_vessel(self):
        self.vessels_qs = Vessel.select()
        self._show_vessels(list(self.vessels_qs))

    def apply_filter_vessel(self):
        keyword = self.search_vessel.text().strip()
        year = self.filter_vessel_year.currentText()
        q = Vessel.select()
        if keyword:
            q = q.where(
                Vessel.ship_project.contains(keyword) |
                Vessel.ship_type_rmrs.contains(keyword) |
                Vessel.shipyard_name.contains(keyword)
            )
        if year != "Все годы":
            q = q.where(Vessel.year_built == int(year))
        self._show_vessels(list(q))

    def reset_vessel(self):
        self.search_vessel.clear()
        self.filter_vessel_year.setCurrentIndex(0)
        self.reload_vessel()

    def _show_vessels(self, rows: list):
        self.table_vessel.setRowCount(0)
        self.label_vessel.setText(f"Всего записей: {len(rows)}")
        for i, v in enumerate(rows):
            self.table_vessel.insertRow(i)

            # Безопасно получаем contract_sum, если вы его не приджойнили в запросе,
            # чтобы программа не вылетала с ошибкой AttributeError.
            contract_sum_val = getattr(v, 'contract_sum', 'Нет данных')

            for col, val in enumerate([
                v.id,
                v.ship_project,
                v.ship_type_rmrs,
                v.ship_class,
                v.year_built,
                v.country_built,
                v.shipyard_name,
                v.deadweight,
                v.registry_number,  # Исправлено: убрано слово 'purchase_'
                contract_sum_val  # Безопасный вывод суммы
            ]):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.table_vessel.setItem(i, col, item)
    def toggle_menu_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_contract.setVisible(not self.menu_frame_contract.isVisible())
        if self.menu_frame_contract.isVisible():
            self.QwordFinderContract.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.QwordFinderContract.setIcon(QIcon("../Pics/right-arrow.png"))
    def toggle_menu(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.QwordFinder.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.QwordFinder.setIcon(QIcon("../Pics/right-arrow.png"))
    def toggle_menu_filters(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_filters.setVisible(not self.menu_frame_filters.isVisible())
        if self.menu_frame_filters.isVisible():
            self.FilterCollapse.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterCollapse.setIcon(QIcon("../Pics/right-arrow.png"))
    def toggle_menu_price(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_price.setVisible(not self.menu_frame_price.isVisible())
        if self.menu_frame_price.isVisible():
            self.FilterPrice.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterPrice.setIcon(QIcon("../Pics/right-arrow.png"))
    def toggle_menu_date(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_data.setVisible(not self.menu_frame_data.isVisible())
        if self.menu_frame_data.isVisible():
            self.FilterDate.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterDate.setIcon(QIcon("../Pics/right-arrow.png"))
    
    def toggle_menu_filters_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_filters_contract.setVisible(not self.menu_frame_filters_contract.isVisible())
        if self.menu_frame_filters_contract.isVisible():
            self.FilterCollapseContract.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterCollapseContract.setIcon(QIcon("../Pics/right-arrow.png"))

    def toggle_menu_price_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_price_contrac.setVisible(not self.menu_frame_price_contrac.isVisible())
        if self.menu_frame_price_contrac.isVisible():
            self.FilterPriceContract.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterPriceContract.setIcon(QIcon("../Pics/right-arrow.png"))
    def toggle_menu_date_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_data_contrac.setVisible(not self.menu_frame_data_contrac.isVisible())
        if self.menu_frame_data_contrac.isVisible():
            self.FilterDateContract.setIcon(QIcon("../Pics/arrow-down.png"))
        else:
            self.FilterDateContract.setIcon(QIcon("../Pics/right-arrow.png"))
    def show_all_purchases(self):
      
    # Очищаем таблицу перед добавлением новых данных
        self.table.setRowCount(0)
        self.label.setText(f"Всего записей {len(self.purchases_list)}")
        if len(self.purchases_list) != 0:
            for current_position, current_purchase in enumerate(self.purchases_list):
                # Добавляем новую строку для каждой записи
                self.table.insertRow(current_position)
                initial_price =  format_string("%.0f", current_purchase.InitialMaxContractPrice, grouping=True)
                # Добавляем данные в каждую ячейку для текущей записи
                for col, value in enumerate([current_purchase.Id, current_purchase.PurchaseOrder, current_purchase.RegistryNumber,str(current_purchase.PlacementDate)
                                             , current_purchase.PurchaseName,current_purchase.AuctionSubject,
                                             initial_price, current_purchase.Currency,
                                              current_purchase.CustomerName
                                             ]):
                    item = QTableWidgetItem(str(value))

                    contract = (Contract
                                .select()
                                .where(Contract.purchase == current_purchase.Id)
                                .first())
                    if contract is None and current_purchase.RegistryNumber:
                        contract = (Contract
                                    .select()
                                    .where(Contract.RegistryNumber == current_purchase.RegistryNumber)
                                    .first())

                    if contract:
                        contract_item = QTableWidgetItem("✅")
                        contract_item.setFlags(contract_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        contract_item.setTextAlignment(Qt.AlignCenter)
                        contract_item.setData(Qt.UserRole, contract.Id)
                        self.table.setItem(current_position, 9, contract_item)
                    else:
                        empty_item = QTableWidgetItem("❌")
                        empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEnabled)
                        empty_item.setTextAlignment(Qt.AlignCenter)
                        empty_item.setForeground(Qt.gray)
                        self.table.setItem(current_position, 9, empty_item)
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    # Добавляем данные в виде "название поля    - значение поля" для каждой колонки
                    self.table.setItem(current_position, col, item)
                    if col == 6:  # Индексация колонок начинается с 0
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
                    # Устанавливаем перенос текста в ячейке путем увеличения высоты строки
                    self.table.setRowHeight(current_position, self.table.rowHeight(current_position) + 3)  # Увеличиваем высоту строки                        
                    # Добавляем данные в виде "название поля    - значение поля" для каждой колонки
        else:
            self.label.setText("Нет записей")

    def show_all_contracts(self):
        self.table_cont.setRowCount(0)
        self.label_cont.setText(f"Всего записей: {len(self.contracts_list)}")

        for i, c in enumerate(self.contracts_list):
            self.table_cont.insertRow(i)

            # Цены
            price = c.ContractPrice or 0.0
            nmck = c.purchase.InitialMaxContractPrice or 0.0
            diff = price - nmck
            reduction = c.ReductionNMCPercent

            price_str = format_string("%.0f", price, grouping=True) if price else "—"
            nmck_str = format_string("%.0f", nmck, grouping=True)  if nmck else "—"
            diff_str = format_string("%.0f", diff, grouping=True)  if (price and nmck) else "—"
            reduction_str = f"{reduction:.2f}%" if reduction is not None else "—"
            executor_name = self.get_contract_executor(c)
            values = [
                c.Id,
                c.RegistryNumber or "—",
                c.purchase.RegistryNumber or "—",
                c.ContractNumber or "—",
                str(c.StartDate) if c.StartDate else "—",
                str(c.EndDate) if c.EndDate else "—",
                price_str,
                nmck_str,
                diff_str,
                reduction_str,
                c.ContractingAuthority or "—",
                executor_name,
                c.purchase.PurchaseName or "—",
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.table_cont.setItem(i, col, item)

            self.table_cont.setRowHeight(i, self.table_cont.rowHeight(i) + 3)
    def highlight_apply_filter_button(self):
    # Подсвечиваем кнопку apply_filter_button
        self.apply_filter_button.setStyleSheet("background-color: #ccffcc;")
    
    def highlight_apply_filter_button_contract(self):
    # Подсвечиваем кнопку apply_filter_button
        self.apply_filter_button_contract.setStyleSheet("background-color: #ccffcc;")

  
    def highlight_input(self):
        min_price = self.min_price_input.text()
        max_price = self.max_price_input.text()
        min_data_valid = self.min_data_input.date().isValid()
        max_data_valid = self.max_data_input.date().isValid()
        search_text = self.search_input.text()
        
        # Подсветка полей в зависимости от введенных данных
        if min_price or max_price:
            self.min_price_input.setStyleSheet("background-color: #ccffcc;")
            self.max_price_input.setStyleSheet("background-color: #ccffcc;")
            self.FilterPrice.setStyleSheet("background-color: #ccffcc;")
        else:
            self.min_price_input.setStyleSheet("")
            self.min_price_input.setStyleSheet("")

        if min_data_valid or max_data_valid:
            self.min_data_input.setStyleSheet("background-color: #ccffcc;")
            self.max_data_input.setStyleSheet("background-color: #ccffcc;")
            self.FilterDate.setStyleSheet("background-color: #ccffcc;")
        else:
            self.min_data_input.setStyleSheet("")
            self.max_data_input.setStyleSheet("")
           
        # Подсветка search_input
        if search_text:
            self.search_input.setStyleSheet("background-color: #ccffcc;")
            self.QwordFinder.setStyleSheet("background-color: #ccffcc;")
        else:
            self.search_input.setStyleSheet("")

    def highlight_input_contract(self):
        min_price = self.min_price_input_contrac.text()
        max_price = self.max_price_input_contrac.text()
        min_data_valid = self.min_data_input_contrac.date().isValid()
        max_data_valid = self.max_data_input_contrac.date().isValid()
        search_text = self.search_input_contract.text()
        
        # Подсветка полей в зависимости от введенных данных
        if min_price or max_price:
            self.min_price_input_contrac.setStyleSheet("background-color: #ccffcc;")
            self.max_price_input_contrac.setStyleSheet("background-color: #ccffcc;")
            self.FilterPriceContract.setStyleSheet("background-color: #ccffcc;")
        else:
            self.min_price_input_contrac.setStyleSheet("")
            self.max_price_input_contrac.setStyleSheet("")

        if min_data_valid or max_data_valid:
            self.min_data_input_contrac.setStyleSheet("background-color: #ccffcc;")
            self.max_data_input_contrac.setStyleSheet("background-color: #ccffcc;")
            self.FilterDateContract.setStyleSheet("background-color: #ccffcc;")
        else:
            self.min_data_input_contrac.setStyleSheet("")
            self.max_data_input_contrac.setStyleSheet("")
        if search_text:
            self.search_input_contract.setStyleSheet("background-color: #ccffcc;")
            self.QwordFinderContract.setStyleSheet("background-color: #ccffcc;")
        else:
            self.search_input_contract.setStyleSheet("")
  
        
        
    def highlight_current_item(self, index):
        if index >= 0:
            sender = self.sender()  # Получаем объект, который вызвал сигнал
            if sender == self.sort_by_putch_order:
                self.sort_by_putch_order.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            elif sender == self.sort_by_putch_okpd2:
                self.sort_by_putch_okpd2.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            elif sender == self.sort_options:
                self.sort_options.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            elif sender == self.sort_by_putch_CustomerName:
                self.sort_by_putch_CustomerName.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            elif sender == self.sort_by_putch_ProcurementMethod:
                self.sort_by_putch_ProcurementMethod.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")

    def highlight_current_item_contract(self, index):
        if index >= 0:
            sender = self.sender()  # Получаем объект, который вызвал сигнал
            if sender == self.sort_options_contract:
                self.sort_options_contract.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapseContract.setStyleSheet("background-color: #ccffcc;")
            elif sender == self.sort_by_putch_winner:
                self.sort_by_putch_winner.setStyleSheet("background-color: #ccffcc;")
                self.FilterCollapseContract.setStyleSheet("background-color: #ccffcc;")

    
    def apply_filter(self):
        self.current_position = 0
        self.selected_option = self.sort_options.currentText()

        if  self.selected_option == "Сортировать по цене (возрастание)":
            order_by = Purchase.InitialMaxContractPrice
        elif  self.selected_option == "Сортировать по цене (убывание)":
            order_by = Purchase.InitialMaxContractPrice.desc()
        elif  self.selected_option == "Сортировать по дате (от новых к старым)":
            order_by = Purchase.PlacementDate.desc()
        elif  self.selected_option == "Сортировать по дате (от старых к новым)":
            order_by = Purchase.PlacementDate
  

        # Получаем минимальную и максимальную цены из полей ввода
        self.min_price = float(self.min_price_input.text()) if self.min_price_input.text() else float('-inf')
        self.max_price = float(self.max_price_input.text()) if self.max_price_input.text() else float('inf')

        min_date_str = self.min_data_input.date()
        max_date_str = self.max_data_input.date()

        self.min_date = min_date_str.toPython() if min_date_str.isValid() else None
        self.max_date = max_date_str.toPython() if max_date_str.isValid() else None

        
        # Выполняем запрос с фильтрацией по диапазону цен и сортировкой
        # Фильтр по цене
        purchases = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(self.min_price, self.max_price))
        ).order_by(order_by)
        # Фильтр по дате
        if  self.min_date and  self.max_date:
            purchases = purchases.where(
                (Purchase.PlacementDate.between( self.min_date,  self.max_date))
            )

        # Фильтр по цене и дате
        purchases_query_combined = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(self.min_price, self.max_price)) &
            (Purchase.PlacementDate.between( self.min_date,  self.max_date) if  self.min_date and  self.max_date else True)
        )
        # Фильтр по законам
       
        self.selected_order = self.sort_by_putch_order.currentText()
        if  self.selected_order != "Фильтрация по закону":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.PurchaseOrder ==  self.selected_order
            )
            # Фильтр по ОКПД2
        self.selected_okpd = self.sort_by_putch_okpd2.currentText()
        if  self.selected_okpd != "Фильтрация по ОКПД2":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.OKPD2Classification ==  self.selected_okpd
            )
        # Фильтр по Методу закупки
        self.selected_ProcurementMethod = self.sort_by_putch_ProcurementMethod.currentText()
        if  self.selected_ProcurementMethod != "Фильтрация по методу закупки":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.ProcurementMethod ==  self.selected_ProcurementMethod
            )
        # Фильтр по Заказчикам
        self.CustomerName = self.sort_by_putch_CustomerName.currentText()
        if  self.CustomerName != "Фильтрация по заказчикам":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.CustomerName ==  self.CustomerName
            )
        # keyword = self.selected_text
        keyword  = self.search_input.text()

    # Добавляем фильтр по ключевому слову (RegistryNumber)
        if keyword:
            purchases_query_combined = purchases_query_combined.where(
                (Purchase.RegistryNumber.contains(keyword)) |
                (Purchase.ProcurementOrganization.contains(keyword)) |
                     (Purchase.PurchaseName.contains(keyword)) |
                     (Purchase.CustomerName.contains(keyword))
            )
        
        self.purchases = purchases_query_combined.order_by(order_by)
        

        self.purchases_list = list(self.purchases)
       
        self.show_all_purchases()

    def apply_filter_contract(self):
        keyword = self.search_input_contract.text().strip()
        executor = self.sort_by_putch_winner.currentText()
        sort_idx = self.sort_options_contract.currentIndex()
        min_p = self.min_price_input_contrac.text().strip()
        max_p = self.max_price_input_contrac.text().strip()
        min_d = self.min_data_input_contrac.date()
        max_d = self.max_data_input_contrac.date()

        q = Contract.select(Contract, Purchase).join(Purchase)

        if keyword:
            matching_contract_ids = (
                SupplierContract
                .select(SupplierContract.contract)
                .join(Supplier, on=(SupplierContract.supplier == Supplier.id))
                .where(Supplier.organization.contains(keyword))
                .distinct()
            )

            q = q.where(
                Contract.ContractingAuthority.contains(keyword) |
                Contract.RegistryNumber.contains(keyword) |
                Contract.ContractNumber.contains(keyword) |
                Purchase.PurchaseName.contains(keyword) |
                (Contract.id.in_(matching_contract_ids))
            )

        if executor and executor != "Фильтрация по исполнителю":
            executor_contract_ids = (
                SupplierContract
                .select(SupplierContract.contract)
                .join(Supplier, on=(SupplierContract.supplier == Supplier.id))
                .where(Supplier.organization == executor)
                .distinct()
            )
            q = q.where(Contract.id.in_(executor_contract_ids))

        if min_p:
            try:
                q = q.where(Contract.ContractPrice >= float(min_p.replace(" ", "")))
            except ValueError:
                pass

        if max_p:
            try:
                q = q.where(Contract.ContractPrice <= float(max_p.replace(" ", "")))
            except ValueError:
                pass

        if min_d.isValid():
            q = q.where(Contract.StartDate >= min_d.toPython())

        if max_d.isValid():
            q = q.where(Contract.StartDate <= max_d.toPython())

        order_map = {
            0: Contract.ContractPrice.asc(),
            1: Contract.ContractPrice.desc(),
            2: Contract.StartDate.asc(),
            3: Contract.StartDate.desc(),
        }

        q = q.order_by(order_map.get(sort_idx, Contract.StartDate.desc()))

        self.contracts = q
        self.contracts_list = list(q)
        self.show_all_contracts()

    def resetFiltersContract(self):
        self.search_input_contract.clear()
        self.sort_options_contract.setCurrentIndex(0)
        self.sort_by_putch_winner.setCurrentIndex(0)
        self.min_price_input_contrac.clear()
        self.max_price_input_contrac.clear()
        self.min_data_input_contrac.setStyleSheet(self.transparent_style)
        self.max_data_input_contrac.setDate(self.max_data_input_contrac.date().currentDate())
        # сбрасываем подсветку
        for w in (self.apply_filter_button_contract, self.FilterCollapseContract,
                  self.FilterPriceContract, self.FilterDateContract,
                  self.QwordFinderContract, self.sort_by_putch_winner,
                  self.sort_options_contract):
            w.setStyleSheet("")
        self.reload_data_cont()

    def handle_cell_click(self, row, column):
        selected_id = self.table.item(row, 0).text()

        # Используем единую функцию маршрутизации из MainWindow (окно 2 - закупки)
        self.window.navigate_to_page(2)
        if column == 9:
            item = self.table.item(row, 9)
            if item:
                contract_id = item.data(Qt.UserRole)
                if contract_id:
                    # Переходим на вкладку контрактов и открываем нужный
                    self.main_window.navigate_to_page(8)  # вкладка контрактов
                    self.window.contractFormular.reloaddataid(contract_id)
                return
        # Обновляем данные
        self.window.purchaseViewer.reload_data_id(selected_id)

    def handle_cell_click_contract(self, row, column):
        selected_id = self.table_cont.item(row, 0).text()

        # Используем единую функцию маршрутизации из MainWindow (окно 8 - контракты)
        self.window.navigate_to_page(8)

        # Обновляем данные
        self.window.contractFormular.reload_data_id(selected_id)

    def findUnic(self):
            unique_values_list = []
            unique_values_query = Purchase.select(
            Purchase.PurchaseName, 
            Purchase.ProcurementOrganization, 
            Purchase.RegistryNumber, 
            Purchase.CustomerName
            ).distinct()

            # Получаем все значения из результата запроса
            unique_values = [
                (
                    purchase.PurchaseName,
                    purchase.ProcurementOrganization,
                    purchase.RegistryNumber,
                    purchase.CustomerName
                ) 
                for purchase in unique_values_query
            ]

            # Преобразуем все значения в список строк
           

            for purchase_name, procurement_organization, registry_number, customer_name in unique_values:
                unique_values_list.extend([
                    str(purchase_name) if purchase_name is not None else None,
                    str(procurement_organization) if procurement_organization is not None else None,
                    str(registry_number) if registry_number is not None else None,
                    str(customer_name) if customer_name is not None else None
                ])
            unique_values_list = [value for value in unique_values_list if value is not None]
            return unique_values_list

    def findUnicContract(self):
        unique_values_list = []

        contract_rows = (
            Purchase
            .select(
                Purchase.PurchaseName,
                Purchase.CustomerName,
                Contract.ContractingAuthority,
                Contract.Id
            )
            .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
            .where(Contract.ContractNumber != "Нет данных")
            .distinct()
            .dicts()
        )

        for row in contract_rows:
            for value in [
                row.get("PurchaseName"),
                row.get("CustomerName"),
                row.get("ContractingAuthority"),
            ]:
                if value:
                    unique_values_list.append(str(value))

            contract_id = row.get("Id")
            if contract_id:
                suppliers = (
                    Supplier
                    .select(Supplier.organization)
                    .join(SupplierContract, on=(SupplierContract.supplier == Supplier.id))
                    .where(SupplierContract.contract == contract_id)
                )
                for s in suppliers:
                    if s.organization:
                        unique_values_list.append(str(s.organization))

        return list(dict.fromkeys(unique_values_list))
    def handleActivated(self, text):
        # Обработка выбора элемента из автозаполнения
        self.selected_text = text

    def handleActivatedContract(self, text):
        # Обработка выбора элемента из автозаполнения
        self.selected_text_contract = text

    def return_filtered_purchase(self):
        return self.purchases

    def return_filtered_contracts(self):
        return self.contracts

    def resetFilters(self):
        # Очищаем все поля ввода
        self.min_price_input.clear()
        self.max_price_input.clear()
        self.min_data_input.setDate(QDate(2000, 1, 1))
        self.max_data_input.setDate(self.max_data_input.date().currentDate())
        self.sort_by_putch_order.setCurrentIndex(0)  # Сбрасываем выбранное значение в выпадающем списке
        self.search_input.clear()
        self.current_position = 0
        self.sort_by_putch_okpd2.setCurrentIndex(0)
        self.sort_by_putch_ProcurementMethod.setCurrentIndex(0)
        self.sort_by_putch_CustomerName.setCurrentIndex(0)
        self.selected_text = None
        
        
        # Очищаем и снова получаем уникальные значения для автозаполнения
        self.unique_values_query = self.findUnic()
        
        
        # Возвращаем записи в исходное состояние без применения каких-либо фильтров
        self.reload_data()
        # Сброс стилей всех элементов к стандартному состоянию
        self.reset_styles()

    def resetFiltersContract(self):
        # Очищаем все поля ввода
        self.selected_text_contract = None
        self.sort_options_contract.setCurrentIndex(0)
        self.sort_by_putch_winner.setCurrentIndex(0)  
        self.current_position = 0
        self.search_input_contract.clear()
        self.min_price_input_contrac.clear()
        self.max_price_input_contrac.clear()
        self.min_data_input_contrac.setDate(QDate(2000, 1, 1))
        self.max_data_input_contrac.setDate(self.max_data_input.date().currentDate())
        self.reload_data_cont()
        # Сброс стилей всех элементов к стандартному состоянию
        self.reset_styles_contract()

    def reset_styles(self):
        # Сброс стилей всех элементов к стандартному состоянию
        for input_field in [self.min_price_input, self.max_price_input, self.apply_filter_button,
                             self.sort_by_putch_order, self.search_input, self.sort_by_putch_okpd2, self.sort_options,
                             self.sort_by_putch_CustomerName,self.sort_by_putch_ProcurementMethod,self.QwordFinder,self.FilterCollapse,
                               self.FilterDate,self.FilterPrice]:
            input_field.setStyleSheet("")
        self.max_data_input.setStyleSheet(self.transparent_style) 
        self.min_data_input.setStyleSheet(self.transparent_style) 

    def reset_styles_contract(self):
        # Сброс стилей всех элементов к стандартному состоянию
        for input_field in [self.min_price_input_contrac, self.max_price_input_contrac, self.apply_filter_button_contract, self.FilterCollapseContract,self.FilterPriceContract,
                            self.FilterDateContract,self.FilterCollapseContract, self.sort_options_contract,self.sort_by_putch_winner,self.Qword_contract, self.QwordFinderContract]:
            input_field.setStyleSheet("")
        self.max_data_input_contrac.setStyleSheet(self.transparent_style) 
        self.min_data_input_contrac.setStyleSheet(self.transparent_style) 
     

    def remove_button_clicked(self):
        # reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
        #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        reply = QMessageBox()
        reply.setText('Вы точно хотите удалить выбранные записи?')
        reply.addButton("нет", QMessageBox.NoRole)
        reply.addButton("да", QMessageBox.YesRole)
        result = reply.exec()
        if result == 1:
            if self.current_purchase.Id:
                success = delete_records_by_id([self.current_purchase.Id])
                if success:
                    self.main_win.updatePurchaseLabel()
                    QMessageBox.information(self, "Успех", "Вы успешно удалили запись!")
                    self.resetFilters()
                else:
                    QMessageBox.information(self,"Ошибка", "Ошибка при удалении записей")
                    
                  
        else:
            pass
    def update_currency(self):
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
            self.curr_shower = InsertWidgetCurrency(purchase_id)
            self.curr_shower.show()
    
    def export_to_excel_clicked(self ):
        
        current_sort_option = self.sort_options.currentText()
        search_input = self.selected_text if self.selected_text is not None else None
        sort_options  = current_sort_option if current_sort_option is not None  else None
        sort_by_putch_order =  self.sort_by_putch_order.currentText() if self.sort_by_putch_order is not None  else None
        min_date = self.min_data_input.date().toPython() if self.min_data_input.date().toPython() is not None  else None
        max_date = self.max_data_input.date().toPython() if self.max_data_input.date().toPython() is not None  else None
        min_price = self.min_price_input.text() if self.min_price_input.text() is not None  else None
        max_price = self.max_price_input.text()  if self.max_price_input.text() is not None  else None
      
        filters = {
        'search_input': search_input,
        'filter_criteria': sort_options ,
        'purchase_order': sort_by_putch_order,
        'start_date': min_date,
        'end_date': max_date,
        'min_price': min_price,
        'max_price': max_price,
        
    }   
    
         
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                # query1 = self.purchases
                # query = self.purchases.select(Purchase, Contract).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                query = (
                    self.purchases
                    .select(Purchase.Id, Purchase.PurchaseOrder, Purchase.RegistryNumber, Purchase.ProcurementMethod,
        Purchase.PurchaseName, Purchase.AuctionSubject, Purchase.PurchaseIdentificationCode,
        Purchase.LotNumber, Purchase.LotName, Purchase.InitialMaxContractPrice, Purchase.Currency,
        Purchase.InitialMaxContractPriceInCurrency, Purchase.ContractCurrency,
        Purchase.OKDPClassification, Purchase.OKPDClassification, Purchase.OKPD2Classification,
        Purchase.PositionCode, Purchase.CustomerName, Purchase.ProcurementOrganization,
        Purchase.PlacementDate, Purchase.UpdateDate, Purchase.ProcurementStage,
        Purchase.ProcurementFeatures, Purchase.ApplicationStartDate, Purchase.ApplicationEndDate,
        Purchase.AuctionDate, Purchase.QueryCount, Purchase.ResponseCount, Purchase.AveragePrice,
        Purchase.MinPrice, Purchase.MaxPrice, Purchase.StandardDeviation, Purchase.CoefficientOfVariation,
        Purchase.TKPData, Purchase.NMCKMarket, Purchase.FinancingLimit, Purchase.InitialMaxContractPriceOld,
        Purchase.notification_link,Purchase.quantity_units,Purchase.nmck_per_unit,
        
        Contract.TotalApplications, Contract.AdmittedApplications, Contract.RejectedApplications,
        Contract.PriceProposal, Contract.Applicant, Contract.Applicant_satatus, Contract.WinnerExecutor,
        Contract.ContractingAuthority, Contract.ContractIdentifier, Contract.RegistryNumber,
        Contract.ContractNumber, Contract.StartDate, Contract.EndDate, Contract.ContractPrice,
        Contract.AdvancePayment, Contract.ReductionNMC, Contract.ReductionNMCPercent,
        Contract.SupplierProtocol, Contract.ContractFile, FinalDetermination.RequestMethod, FinalDetermination.PublicInformationMethod,
        FinalDetermination.NMCObtainedMethods, FinalDetermination.CostMethodNMC,
        FinalDetermination.ComparablePrice, FinalDetermination.NMCMethodsTwo,
        FinalDetermination.CEIComparablePrices, FinalDetermination.CEICostMethod,
        FinalDetermination.CEIMethodsTwo,  CurrencyRate.CurrencyValue, CurrencyRate.CurrentCurrency,
        CurrencyRate.DateValueChanged, CurrencyRate.CurrencyRateDate, CurrencyRate.PreviousCurrency)
                    .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                    .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                    .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                )     
                

                records, data, user = self.main_window.return_variabels()
                # cleaned_filename = data.sub(r'[\\/*?:"<>| ]', '_', data)
                self.data = list(query.tuples())
                # print(self.data[0])
                if export_to_excel(self.data ,f'{selected_file}/Отфильтрованные данные__{data}_{records}_{user}.xlsx',filters=filters ) == True:
                    QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка записи")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")
           
    def export_to_excel_clicked_contract(self ):
        
        current_sort_option = self.sort_options_contract.currentText()
        sort_options  = current_sort_option if current_sort_option is not None  else None
        min_date = self.min_data_input_contrac.date().toPython() if self.min_data_input_contrac.date().toPython() is not None  else None
        max_date = self.max_data_input_contrac.date().toPython() if self.max_data_input_contrac.date().toPython() is not None  else None
        min_price = self.min_price_input_contrac.text() if self.min_price_input_contrac.text() is not None  else None
        max_price = self.max_price_input_contrac.text()  if self.max_price_input_contrac.text() is not None  else None
      
        filters = {
        'filter_criteria': sort_options ,
        'start_date': min_date,
        'end_date': max_date,
        'min_price': min_price,
        'max_price': max_price,
        
    }
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:

                records, data, user = self.main_window.return_variabels()
                # cleaned_filename = data.sub(r'[\\/*?:"<>| ]', '_', data)
                self.data = list(self.contracts.dicts())
                # print(self.data[0])
                if export_to_excel_contract(self.data ,f'{selected_file}/Отфильтрованные данные_контракты__{data}_{records}_{user}.xlsx',filters=filters ) == True:
                    QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка записи")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")
           
    def reload_data(self):
        self.purchases = Purchase.select()
        self.purchases_list = list(self.purchases)
        self.update()
        self.show_all_purchases()

    def reload_data_cont(self):
        self.contracts = (
            Contract.select(Contract, Purchase)
            .join(Purchase)
            .where(Contract.ContractNumber != None)
            .order_by(Contract.StartDate.desc())
        )
        self.contracts_list = list(self.contracts)
        self.show_all_contracts()
    def return_filters_variabels(self):
    
        # search_input = self.selected_text if self.selected_text is not None else ""
        sort_by_putch_order =  self.sort_by_putch_order.currentText() if self.sort_by_putch_order.currentText() != "Фильтровать по закону"  else "-"
        min_date = self.min_data_input.date().toPython() if self.min_data_input.date().toPython() is not None  else "-"
        max_date = self.max_data_input.date().toPython() if self.max_data_input.date().toPython() is not None  else "-"
        min_price = self.min_price_input.text() if self.min_price_input.text() is not None  else "Фильтр не применен"
        max_price = self.max_price_input.text()  if self.max_price_input.text() is not None  else "Фильтр не применен"
        sort_by_putch_okpd2 = self.sort_by_putch_okpd2.currentText() if self.sort_by_putch_okpd2.currentText() != "Фильтровать по ОКПД2" else "-"
        return sort_by_putch_order,min_date,max_date,min_price,max_price,sort_by_putch_okpd2

    def get_contract_executor(self, contract) -> str:
        supplier_link = (
            SupplierContract
            .select(SupplierContract, Supplier)
            .join(Supplier, on=(SupplierContract.supplier == Supplier.id))
            .where(SupplierContract.contract == contract)
            .first()
        )

        if supplier_link and supplier_link.supplier:
            return supplier_link.supplier.organization or "—"

        return "—"
        
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidgetAll(None,None)
#     csv_loader_widget.show()
#     sys.exit(app.exec())