from PySide6.QtWidgets import *
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination,CurrencyRate
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import QColor,QIcon,QFont
from PySide6.QtCore import QDate
import sys, json
from peewee import JOIN
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel,export_to_excel_contract
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
from peewee import fn
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('test.db')
cursor = db.cursor()


class PurchasesWidgetAll(QWidget):
    def __init__(self,main, role):
        super().__init__()
        # self.main_win = main_window
        self.selected_text = None
        self.main_window = main
        self.role = role
        
         # Создаем компонент вкладок
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_purch_tab(), 'Закупки')
        tab_widget.addTab(self.create_cont_tab(), 'Контракты')
        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def create_purch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(9)

        # Устанавливаем заголовки колонок
        column_headers = ["№ПП", "Закон", "Реестровый номер", "Дата размещения",
                          "Наименование закупки", "Предмет аукциона", "НМЦК",
                          "Валюта", "Наименование заказчика"]
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
        self.sort_options.addItems(["Сортировать по Цене (Возростание)", "Сортировать по Цены (Убывание)",
                                    
                                    "Сортировать по Дате (Возростание)","Сортировать по Дате (Убывание)"])
         # Устанавливаем обработчик событий для выпадающего меню
       
        self.sort_options.setFixedWidth(250)
        self.sort_options.currentIndexChanged.connect(self.highlight_current_item)
        unique_purchase_orders = Purchase.select(Purchase.PurchaseOrder).distinct()
        self.sort_by_putch_order = QComboBox()
        self.sort_by_putch_order.addItem("Фильтрация по Закону")
        self.sort_by_putch_order.setFixedWidth(250)
        self.sort_by_putch_order.currentIndexChanged.connect(self.highlight_current_item)
        for order in unique_purchase_orders:
            self.sort_by_putch_order.addItem(str(order.PurchaseOrder))


      
        unique_purchase_OKPD2 = Purchase.select(Purchase.OKPD2Classification).distinct()
        self.sort_by_putch_okpd2 = QComboBox()
        self.sort_by_putch_okpd2.addItem("Фильтрация по ОКПД2")
        self.sort_by_putch_okpd2.setFixedWidth(250)
        for order in unique_purchase_OKPD2:
            self.sort_by_putch_okpd2.addItem(str(order.OKPD2Classification))

        unique_purchase_CustomerName = Purchase.select(Purchase.CustomerName).distinct()
        self.sort_by_putch_CustomerName = QComboBox()
        self.sort_by_putch_CustomerName.addItem("Фильтрация по Заказчикам")
        self.sort_by_putch_CustomerName.setFixedWidth(250)
        for order in unique_purchase_CustomerName:
            self.sort_by_putch_CustomerName.addItem(str(order.CustomerName))

        self.transparent_style = "QDateEdit { color: transparent; }"

        unique_purchase_ProcurementMethod = Purchase.select(Purchase.ProcurementMethod).distinct()
        self.sort_by_putch_ProcurementMethod = QComboBox()
        self.sort_by_putch_ProcurementMethod.addItem("Фильтрация по Методу закупки")
        self.sort_by_putch_ProcurementMethod.setFixedWidth(250)
        for order in unique_purchase_ProcurementMethod:
            self.sort_by_putch_ProcurementMethod.addItem(str(order.ProcurementMethod))
        # Создаем метки и поля для ввода минимальной и максимальной цены
        self.sort_by_putch_okpd2.currentIndexChanged.connect(self.highlight_current_item)
        self.min_price_label = QLabel("Минимальная цена")
        self.min_price_input = QLineEdit()
        self.min_price_input.setFixedWidth(100)
        self.max_price_label = QLabel("Максимальная цена")
        self.max_price_input = QLineEdit()
        self.max_price_input.setFixedWidth(100)
        self.toExcel = QPushButton("Экспорт в Excel", self)
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
        self.search_input.setFixedWidth(300)
        completer = QCompleter(self.unique_values_query )
        # self.search_input.textChanged.connect(completer.filter)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated.connect(self.handleActivated)
        self.search_input.setCompleter(completer)
        # Устанавливаем автозавершение для поля ввода
        # self.search_input.setCompleter(completer)
        # Создаем кнопки для навигации
       
    
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.label)
        icon_path = "Pics/icons8-фильтр-ios-17-32.png"
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
        self.QwordFinder.setIcon(QIcon("Pics/right-arrow.png"))
        self.QwordFinder.setMaximumWidth(300)
        self.QwordFinder.clicked.connect(self.toggle_menu)
        # Добавляем кнопку выпадающего меню по фильтрам
        self.FilterCollapse = QPushButton("Фильтры")
        self.FilterCollapse.setIcon(QIcon("Pics/right-arrow.png"))
        self.FilterCollapse.setMaximumWidth(300)
        self.FilterCollapse.clicked.connect(self.toggle_menu_filters)
         # Добавляем кнопку выпадающего меню по цене
        self.FilterPrice = QPushButton("Цена")
        self.FilterPrice.setIcon(QIcon("Pics/right-arrow.png"))
        self.FilterPrice.setMaximumWidth(300)
        self.FilterPrice.clicked.connect(self.toggle_menu_price)
        # Добавляем кнопку выпадающего меню по дате
        self.FilterDate = QPushButton("Дата")
        self.FilterDate.setIcon(QIcon("Pics/right-arrow.png"))
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
        DataLabel = QLabel("Фильтрация по Дате Размещения")
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
        # toplayoutH = QHBoxLayout(self)
        # Добавляем выпадающее меню
        # toplayoutH.addWidget(self.sort_options)
        # toplayoutH.addWidget(self.sort_by_putch_order)
        # toplayoutH.addWidget(self.sort_by_putch_okpd2)
        # toplayoutH.addWidget(self.sort_by_putch_ProcurementMethod)
        # toplayoutH.addWidget(self.sort_by_putch_CustomerName)
        # layout.addLayout(toplayoutH)
        # Создаем горизонтальный макет для минимальной и максимальной цены
        # price_layout = QGridLayout()
        # # Добавляем их в сетку
        # price_layout.addWidget(self.min_price_label, 0, 0)
        # price_layout.addWidget(self.min_price_input, 0, 1)
        # price_layout.addWidget(self.max_price_label, 1, 0)
        # price_layout.addWidget(self.max_price_input, 1, 1)
        # # layout.addLayout(price_layout)

        # # Создаем горизонтальный макет для начальной и конечной даты
        # date_layout = QGridLayout()
        # date_layout.addWidget(self.min_data_label, 0, 0)
        # date_layout.addWidget(self.min_data_input, 0, 1)
        # date_layout.addWidget(self.max_data_label, 1, 0)
        # date_layout.addWidget(self.max_data_input, 1, 1)
        # combined_layout = QHBoxLayout()
        # combined_layout.addLayout(price_layout)
        # combined_layout.addLayout(date_layout)
        # combined_layout.addSpacing(200) 
        # frame = QFrame()
        # frame.setLayout(combined_layout)

        # Ограничиваем максимальную ширину frame
        # frame.setMaximumWidth(850)
        # layout.addWidget(frame)
        # price_layout.setColumnStretch(2, 1)  # Растягиваем последний столбец
        # date_layout.setColumnStretch(2, 1)

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
       
        # self.purchases = Purchase.select()
        # self.purchases = (Purchase
        #         .select()
        #         .join(Contract, JOIN.LEFT_OUTER)
        #           # Уточните условия, если нужно
        #         )
        # combined_list = (Purchase
        #         .select()
        #         .join(Contract, JOIN.LEFT_OUTER)
        #           # Уточните условия, если нужно
        #         .execute())
   
        # self.purchases_list = list(self.purchases)
        # self.purchases_list = list(self.purchases)
        # self.show_current_purchase()

        if self.role == "Гость":
            self.toExcel.hide()
        else:
            self.toExcel.show()
        return tab

    def create_cont_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Создаем таблицу для отображения данных
        self.table_cont = QTableWidget(self)
        self.table_cont.setColumnCount(11)

        # Устанавливаем заголовки колонок
        column_headers = ["№ПП", "Реестровый номер договора", "Реестровый номер закупки",
                          "Номер контракта", "Дата начала/подписания", "Цена контракта",'НМЦК','Разница НМЦК и Цены контракта',
                           "Заказчик по контракту","Победитель", 
                           "Наименование закупки"]
        self.table_cont.resizeColumnsToContents()
        self.table_cont.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_cont.setHorizontalHeaderLabels(column_headers)
        self.table_cont.setColumnWidth(8, 600)
        self.table_cont.setColumnWidth(9, 600)
        self.table_cont.setColumnWidth(10, 600)
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Затем устанавливаем режим изменения размера колонки "Наименование закупки" на фиксированный размер
        self.table_cont.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table_cont.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table_cont.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.table_cont.setTextElideMode(Qt.ElideRight)
        self.table_cont.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_cont.setShowGrid(True)
        self.table_cont.verticalHeader().setVisible(False)
        self.table_cont.horizontalHeader().setVisible(True)
        self.table_cont.setWordWrap(True)
        # Создаем метки и поля для ввода минимальной и максимальной цены
        
        self.min_price_label_contrac = QLabel("Минимальная цена ")
        self.min_price_input_contrac = QLineEdit()
        self.min_price_input_contrac.setFixedWidth(100)
        self.max_price_label_contrac = QLabel("Максимальная цена")
        self.max_price_input_contrac = QLineEdit()
        self.max_price_input_contrac.setFixedWidth(100)
        self.toExcel_contract = QPushButton("Экспорт в Excel", self)
        self.toExcel_contract.clicked.connect(self.export_to_excel_clicked_contract)
        self.toExcel_contract.setFixedWidth(400)
        button_layout3 = QHBoxLayout()
        button_layout3.addWidget(self.toExcel_contract)
        button_layout3.setAlignment(Qt.AlignHCenter)
        self.min_data_label_contrac = QLabel("Начальная дата")
        self.min_data_input_contrac = QDateEdit()
        self.min_data_input_contrac.setCalendarPopup(False)
        self.min_data_input_contrac.setStyleSheet(self.transparent_style)
        # self.min_data_input.setDate(self.min_data_input.date().currentDate())

        self.min_data_input_contrac.clear()
        self.min_data_input_contrac.setFixedWidth(150)
        self.min_data_input_contrac.setCalendarPopup(True)
        self.max_data_label_contrac = QLabel("Конечная дата")
        self.max_data_input_contrac = QDateEdit()
        self.max_data_input_contrac.setCalendarPopup(True)
        self.max_data_input_contrac.setDate(self.max_data_input.date().currentDate())
        self.max_data_input_contrac.setStyleSheet(self.transparent_style) 
     
        self.current_position = 0   
        self.label_cont = QLabel("Всего записей", self)
        self.table_cont.cellClicked.connect(self.handle_cell_click_contract)
         
         # Создаем выпадающее меню
        self.sort_options_contract = QComboBox()
        self.sort_options_contract.addItems(["Сортировать по Цене (Возростание)", "Сортировать по Цены (Убывание)",
                                    
                                    "Сортировать по Дате (Возростание)","Сортировать по Дате (Убывание)"])
         # Устанавливаем обработчик событий для выпадающего меню
       
        self.sort_options_contract.setFixedWidth(250)
        self.sort_options_contract.currentIndexChanged.connect(self.highlight_current_item_contract)
        unique_contract_winnter = Contract.select(Contract.WinnerExecutor).distinct()
        self.sort_by_putch_winner = QComboBox()
        self.sort_by_putch_winner.addItem("Фильтрация по Победителю-исполнителю контракта")
        self.sort_by_putch_winner.setFixedWidth(250)
        self.sort_by_putch_winner.currentIndexChanged.connect(self.highlight_current_item_contract)
        for order in unique_contract_winnter:
            self.sort_by_putch_winner.addItem(str(order.WinnerExecutor))


      
        self.search_input_contract = QLineEdit()
        self.search_input_contract.setPlaceholderText("Поиск по Реестровому номеру, заказчику, наименованию объекта или организации")
        self.unique_values_query_contract = self.findUnicContract()
        self.search_input_contract.setFixedWidth(300)
        completer = QCompleter(self.unique_values_query_contract )
        # self.search_input.textChanged.connect(completer.filter)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated.connect(self.handleActivated)
        self.search_input_contract.setCompleter(completer)
         #  кнопка "Сбросить фильтры" 
        self.reset_filters_button_contract = QPushButton("Сбросить фильтры контрактов", self)
        self.reset_filters_button_contract.setFixedWidth(250)
        self.reset_filters_button_contract.clicked.connect(self.resetFiltersContract)
        # Создаем поле ввода для поиска
       
       
    
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.label_cont)
        icon_path = "Pics/icons8-фильтр-ios-17-32.png"
        self.label_cont.setAlignment(Qt.AlignHCenter)
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
        self.apply_filter_button_contract = QPushButton("Применить фильтры контрактов", self)
        self.apply_filter_button_contract.setIcon(icon)
        self.apply_filter_button_contract.clicked.connect(self.apply_filter_contract)
        self.apply_filter_button_contract.setFixedWidth(250)
        self.QwordFinderContract = QPushButton("Поиск по ключевому слову")
        self.QwordFinderContract.setIcon(QIcon("Pics/right-arrow.png"))
        self.QwordFinderContract.setMaximumWidth(300)
        self.QwordFinderContract.clicked.connect(self.toggle_menu_contract)
         #меню по ключевому слову
        self.menu_content_contract = QWidget()
        menu_layout_contract = QVBoxLayout()
        self.Qword_contract = QLabel("Поиск по ключевому слову")
        menu_layout_contract.addWidget(line)
        menu_layout_contract.addWidget(self.Qword_contract)
        menu_layout_contract.addWidget(self.search_input_contract)
        
        self.menu_content_contract.setLayout(menu_layout_contract)
        self.menu_frame_contract = QFrame()
        self.menu_frame_contract.setLayout(QVBoxLayout())
        self.menu_frame_contract.layout().addWidget(self.menu_content_contract)
        self.menu_frame_contract.setVisible(False)

        # Добавляем кнопку выпадающего меню по фильтрам
        self.FilterCollapseContract = QPushButton("Фильтры")
        self.FilterCollapseContract.setIcon(QIcon("Pics/right-arrow.png"))
        self.FilterCollapseContract.setMaximumWidth(300)
        self.FilterCollapseContract.clicked.connect(self.toggle_menu_filters_contract)

         # Добавляем кнопку выпадающего меню по цене
        self.FilterPriceContract = QPushButton("Цена")
        self.FilterPriceContract.setIcon(QIcon("Pics/right-arrow.png"))
        self.FilterPriceContract.setMaximumWidth(300)
        self.FilterPriceContract.clicked.connect(self.toggle_menu_price_contract)
        # Добавляем кнопку выпадающего меню по дате
        self.FilterDateContract = QPushButton("Дата")
        self.FilterDateContract.setIcon(QIcon("Pics/right-arrow.png"))
        self.FilterDateContract.setMaximumWidth(300)
        self.FilterDateContract.clicked.connect(self.toggle_menu_date_contract)
         # Добавляем кнопку выпадающего меню по цене

        #меню по ключевому фильтрам
        self.menu_content_filters_contract  = QWidget()
        menu_layout_filters = QHBoxLayout()
        self.FilterLable_contract  = QLabel("Расшириная фильтрация по справочникам контрактов")
        menu_layout_filtersH = QVBoxLayout()
        menu_layout_filtersH.addWidget(line1)
        menu_layout_filtersH.addWidget(self.FilterLable_contract )
        menu_layout_filters.addWidget(self.sort_options_contract)
        menu_layout_filters.addWidget(self.sort_by_putch_winner)
        # menu_layout_filters.addWidget(self.sort_by_putch_order)
        # menu_layout_filters.addWidget(self.sort_by_putch_okpd2)
        # menu_layout_filters.addWidget(self.sort_by_putch_ProcurementMethod)
        # menu_layout_filters.addWidget(self.sort_by_putch_CustomerName)
        menu_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        menu_layout_filtersH.addLayout(menu_layout_filters)
        self.menu_content_filters_contract .setLayout(menu_layout_filtersH)
        self.menu_frame_filters_contract  = QFrame()
        self.menu_frame_filters_contract.setLayout(QVBoxLayout())
        self.menu_frame_filters_contract.layout().addWidget(self.menu_content_filters_contract )
        self.menu_frame_filters_contract.setVisible(False)
        #меню по  фильтрам цена
        self.menu_content_price_contrac = QWidget()
        menu_layout_price_contrac = QHBoxLayout()
        menu_layout_priceV_contrac = QVBoxLayout()
        self.PriceLabel_contrac = QLabel("Фильтрация по Цене контрактов")
        menu_layout_priceV_contrac.addWidget( self.PriceLabel_contrac)
        menu_layout_priceV_contrac.addWidget(line2)
        menu_layout_price_contrac.addWidget(self.min_price_label_contrac)
        menu_layout_price_contrac.addWidget(self.min_price_input_contrac)
        menu_layout_price_contrac.addWidget(self.max_price_label_contrac)
        menu_layout_price_contrac.addWidget(self.max_price_input_contrac)
        menu_layout_priceV_contrac.addLayout(menu_layout_price_contrac)
        menu_layout_price_contrac.setAlignment(Qt.AlignmentFlag.AlignLeft)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        menu_layout_price_contrac.addItem(spacer)
        self.menu_content_price_contrac.setLayout(menu_layout_priceV_contrac)
        self.menu_frame_price_contrac = QFrame()
        self.menu_frame_price_contrac.setLayout(QVBoxLayout())
        self.menu_frame_price_contrac.layout().addWidget(self.menu_content_price_contrac)
        self.menu_frame_price_contrac.setVisible(False)
        #меню по  фильтрам дата
        self.menu_content_data_contrac = QWidget()
        menu_layout_data_contrac = QHBoxLayout()
        DataLabel_contrac = QLabel("Фильтрация по Дате Размещения контракта")
        menu_layout_dataV_contrac = QVBoxLayout()
        menu_layout_dataV_contrac.addWidget(DataLabel_contrac)
        menu_layout_dataV_contrac.addWidget(line3)
        menu_layout_data_contrac.addWidget(self.min_data_label_contrac)
        menu_layout_data_contrac.addWidget(self.min_data_input_contrac)
        menu_layout_data_contrac.addWidget(self.max_data_label_contrac)
        menu_layout_data_contrac.addWidget(self.max_data_input_contrac)
        menu_layout_data_contrac.setAlignment(Qt.AlignmentFlag.AlignLeft)
        menu_layout_dataV_contrac.addLayout(menu_layout_data_contrac)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        menu_layout_data_contrac.addItem(spacer)
        self.menu_content_data_contrac.setLayout(menu_layout_dataV_contrac)
        self.menu_frame_data_contrac = QFrame()
        self.menu_frame_data_contrac.setLayout(QVBoxLayout())
        self.menu_frame_data_contrac.layout().addWidget(self.menu_content_data_contrac)
        self.menu_frame_data_contrac.setVisible(False)
        
        self.All_parametrs_finder_contract = QLabel("Все параметры поиска")
        font = QFont()
        font.setPointSize(16)
        # layout = QVBoxLayout(self)
        # Устанавливаем созданный шрифт для QLabel
        self.All_parametrs_finder_contract.setFont(font)
        # layout.addWidget(self.search_input)
        button_layout_filters = QHBoxLayout()
        button_layout_filters.addWidget(self.QwordFinderContract)
        button_layout_filters.addWidget(self.FilterCollapseContract)
        button_layout_filters.addWidget(self.FilterPriceContract)
        button_layout_filters.addWidget(self.FilterDateContract)
        button_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.All_parametrs_finder_contract,alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(button_layout_filters)
        layout.addWidget(self.menu_frame_contract)
        layout.addWidget(self.menu_frame_filters_contract)
        layout.addWidget(self.menu_frame_price_contrac)
        layout.addWidget(self.menu_frame_data_contrac)
        

        # Добавляем кнопку "Применить фильтр"
        button_layout_filters = QHBoxLayout()
        button_layout_filters.addWidget(self.apply_filter_button_contract)
        button_layout_filters.addWidget(self.reset_filters_button_contract)
        button_layout_filters.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(button_layout_filters)
        # Добавляем таблицу и остальные элементы в макет
        layout.addWidget(self.table_cont)
        layout.addLayout(button_layout)
        layout.addLayout(button_layout3)
        # Получаем данные из базы данных и отображаем первую запись
        self.reload_data_cont()

        self.min_price_input_contrac.textChanged.connect(self.highlight_input_contract)
        self.max_price_input_contrac.textChanged.connect(self.highlight_input_contract)
        self.min_data_input_contrac.dateChanged.connect(self.highlight_input_contract)
        self.max_data_input_contrac.dateChanged.connect(self.highlight_input_contract)
        self.search_input_contract.textChanged.connect(self.highlight_input_contract)
        self.apply_filter_button_contract.clicked.connect(self.highlight_apply_filter_button_contract)
       

        if self.role == "Гость":
            self.toExcel.hide()
        else:
            self.toExcel.show()
        return tab
    def toggle_menu_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_contract.setVisible(not self.menu_frame_contract.isVisible())
        if self.menu_frame_contract.isVisible():
            self.QwordFinderContract.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.QwordFinderContract.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_menu(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.QwordFinder.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.QwordFinder.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_menu_filters(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_filters.setVisible(not self.menu_frame_filters.isVisible())
        if self.menu_frame_filters.isVisible():
            self.FilterCollapse.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterCollapse.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_menu_price(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_price.setVisible(not self.menu_frame_price.isVisible())
        if self.menu_frame_price.isVisible():
            self.FilterPrice.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterPrice.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_menu_date(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_data.setVisible(not self.menu_frame_data.isVisible())
        if self.menu_frame_data.isVisible():
            self.FilterDate.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterDate.setIcon(QIcon("Pics/right-arrow.png"))
    
    def toggle_menu_filters_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_filters_contract.setVisible(not self.menu_frame_filters_contract.isVisible())
        if self.menu_frame_filters_contract.isVisible():
            self.FilterCollapseContract.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterCollapseContract.setIcon(QIcon("Pics/right-arrow.png"))

    def toggle_menu_price_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_price_contrac.setVisible(not self.menu_frame_price_contrac.isVisible())
        if self.menu_frame_price_contrac.isVisible():
            self.FilterPriceContract.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterPriceContract.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_menu_date_contract(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_data_contrac.setVisible(not self.menu_frame_data_contrac.isVisible())
        if self.menu_frame_data_contrac.isVisible():
            self.FilterDateContract.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FilterDateContract.setIcon(QIcon("Pics/right-arrow.png"))
    def show_all_purchases(self):
    # Очищаем таблицу перед добавлением новых данных
        self.table.setRowCount(0)
        self.label.setText(f"Всего записей {len(self.purchases_list)}")
        if len(self.purchases_list) != 0:
            for current_position, current_purchase in enumerate(self.purchases_list):
                # Добавляем новую строку для каждой записи
                self.table.insertRow(current_position)
                
                # Добавляем данные в каждую ячейку для текущей записи
                for col, value in enumerate([current_purchase.Id, current_purchase.PurchaseOrder, current_purchase.RegistryNumber,str(current_purchase.PlacementDate)
                                             , current_purchase.PurchaseName,current_purchase.AuctionSubject,
                                             str(current_purchase.InitialMaxContractPrice), current_purchase.Currency,
                                              current_purchase.CustomerName
                                             ]):
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(current_position, col, item)
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
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
    # Очищаем таблицу перед добавлением новых данных
        self.table_cont.setRowCount(0)
        self.label_cont.setText(f"Всего записей {len(self.contracts_list)}")
        if len(self.contracts_list) != 0:
            for current_position, current_purchase in enumerate(self.contracts_list):
                # Добавляем новую строку для каждой записи
                self.table_cont.insertRow(current_position)
                
                # Добавляем данные в каждую ячейку для текущей записи
                for col, value in enumerate([current_purchase[0], current_purchase[1], current_purchase[2],
                                  str(current_purchase[3]), current_purchase[4],
                                  current_purchase[5],  current_purchase[22],str( current_purchase[22] - current_purchase[5]),
                                  str(current_purchase[6]), current_purchase[7],
                                  current_purchase[8]
                                  ]):
                    item = QTableWidgetItem(str(value))
                    self.table_cont.setItem(current_position, col, item)
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    # Добавляем данные в виде "название поля    - значение поля" для каждой колонки
                    self.table_cont.setItem(current_position, col, item)
                    # if col == 6:  # Индексация колонок начинается с 0
                    #     item.setTextAlignment(Qt.AlignRight | Qt.AlignTop)
                    # Устанавливаем перенос текста в ячейке путем увеличения высоты строки
                    self.table_cont.setRowHeight(current_position, self.table_cont.rowHeight(current_position) + 3)  # Увеличиваем высоту строки                        
                    # Добавляем данные в виде "название поля    - значение поля" для каждой колонки
        else:
            self.label_cont.setText("Нет записей")     
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
            # elif sender == self.sort_options:
            #     self.sort_options.setStyleSheet("background-color: #ccffcc;")
            #     self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            # elif sender == self.sort_by_putch_CustomerName:
            #     self.sort_by_putch_CustomerName.setStyleSheet("background-color: #ccffcc;")
            #     self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
            # elif sender == self.sort_by_putch_ProcurementMethod:
            #     self.sort_by_putch_ProcurementMethod.setStyleSheet("background-color: #ccffcc;")
            #     self.FilterCollapse.setStyleSheet("background-color: #ccffcc;")
        
    
    def apply_filter(self):
        self.current_position = 0
        self.selected_option = self.sort_options.currentText()

        if  self.selected_option == "Сортировать по Цене (Возростание)":
            order_by = Purchase.InitialMaxContractPrice
        elif  self.selected_option == "Сортировать по Цены (Убывание)":
            order_by = Purchase.InitialMaxContractPrice.desc()
        elif  self.selected_option == "Сортировать по Дате (Убывание)":
            order_by = Purchase.PlacementDate.desc()
        elif  self.selected_option == "Сортировать по Дате (Возростание)":
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
        if  self.selected_order != "Фильтрация по Закону":
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
        if  self.selected_ProcurementMethod != "Фильтрация по Методу закупки":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.ProcurementMethod ==  self.selected_ProcurementMethod
            )
        # Фильтр по Заказчикам
        self.CustomerName = self.sort_by_putch_CustomerName.currentText()
        if  self.CustomerName != "Фильтрация по Заказчикам":
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
        self.current_position = 0
        self.selected_option_contract = self.sort_options_contract.currentText()
    #     self.contracts  = (
    # Purchase.select(
    #     Purchase.Id,
    #     Contract.RegistryNumber,
    #     Purchase.RegistryNumber,
    #     Contract.ContractNumber,
    #     Contract.StartDate,
    #     Contract.ContractPrice,
    #     Contract.ContractingAuthority,
    #     Contract.WinnerExecutor,
    #     Purchase.PurchaseName,
    #     Contract.TotalApplications,
    #     Contract.AdmittedApplications,
    #     Contract.RejectedApplications,
    #     Contract.PriceProposal,
    #     Contract.Applicant,
    #     Contract.Applicant_satatus,
    #     Contract.ContractIdentifier,
    #     Contract.EndDate,
    #     Contract.AdvancePayment,
    #     Contract.ReductionNMC,
    #     Contract.ReductionNMCPercent,
    #     Contract.SupplierProtocol,
    #     Contract.ContractFile
    # )
    # .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
    # .where(Contract.ContractNumber != "Нет данных"))
        
        if  self.selected_option_contract == "Сортировать по Цене (Возростание)":
            order_by = Contract.ContractPrice
        elif  self.selected_option_contract == "Сортировать по Цены (Убывание)":
            order_by = Contract.ContractPrice.desc()
        elif  self.selected_option_contract == "Сортировать по Дате (Убывание)":
            order_by = Contract.StartDate.desc()
        elif  self.selected_option_contract == "Сортировать по Дате (Возростание)":
            order_by = Contract.StartDate

        min_price = float(self.min_price_input_contrac.text()) if self.min_price_input_contrac.text() else float('-inf')
        max_price = float(self.max_price_input_contrac.text()) if self.max_price_input_contrac.text() else float('inf')
        
        min_date_str = self.min_data_input_contrac.date()
        max_date_str = self.max_data_input_contrac.date()

        min_date = min_date_str.toPython() if min_date_str.isValid() else None
        max_date = max_date_str.toPython() if max_date_str.isValid() else None

         # Фильтр по цене
        self.contracts = self.contracts.where(
            (Contract.ContractPrice.between(min_price, max_price))
                                        ).order_by(order_by)
        # Фильтр по дате
        if  min_date and max_date:
            self.contracts = self.contracts.where(
                (Contract.StartDate.between( min_date,  max_date))
            )

        # Фильтр по цене и дате
        self.contracts = self.contracts.where(
            (Contract.ContractPrice.between(min_price, max_price)) &
            (Contract.StartDate.between(min_date,  max_date) if min_date and  max_date else True)
        )

        self.selected_contr = self.sort_by_putch_winner.currentText()
        if  self.selected_contr != "Фильтрация по Победителю-исполнителю контракта":
            self.contracts = self.contracts.where(
                Contract.WinnerExecutor == self.selected_contr )
            
        keyword  = self.search_input_contract.text()

        if keyword:
            self.contracts  = self.contracts .where(
                (Contract.WinnerExecutor.contains(keyword)) |
                (Contract.ContractingAuthority.contains(keyword)) |
                     (Purchase.PurchaseName.contains(keyword)) |
                     (Purchase.CustomerName.contains(keyword))
            )
        

        self.contracts_list = list(self.contracts.order_by(order_by).tuples())
        self.show_all_contracts()
  
    def handle_cell_click(self, row, column):
        # Получаем Id из выбранной строки и выводим в консоль

        selected_id = self.table.item(row, 0).text()
        self.window.stackedWidget.setCurrentIndex(2)
        self.window.purchaseViewer.reload_data_id(selected_id)
        # from DBtest import PurchasesWidget
        # self.wind = PurchasesWidget(selected_id)
        # self.wind.show()
    def handle_cell_click_contract(self, row, column):
        # Получаем Id из выбранной строки и выводим в консоль

        selected_id = self.table.item(row, 0).text()
        self.window.stackedWidget.setCurrentIndex(8)
        self.window.ContractFormularWidget.reload_data_id(selected_id)


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
            unique_values_query = (Purchase.select(
            Purchase.PurchaseName, 
            Contract.WinnerExecutor,  # Исправлено на Contract
            Contract.ContractingAuthority,  # Исправлено на Contract
            Purchase.CustomerName,
            )
            .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
            .where(Contract.ContractNumber != "Нет данных")
            .distinct())
            # Получаем все значения из результата запроса
            unique_values = [
                (
                    purchase.PurchaseName,
                    purchase.contract.WinnerExecutor,
                    purchase.contract.ContractingAuthority,
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
    def handleActivated(self, text):
        # Обработка выбора элемента из автозаполнения
        self.selected_text = text


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
                
                # query = (
                #     self.purchases
                #     .select(Purchase, Contract, FinalDetermination, CurrencyRate)
                #     .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                #     .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                #     .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                # )     
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
                # query1 = self.purchases
                # query = self.purchases.select(Purchase, Contract).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                 
                
                # query = (
                #     self.purchases
                #     .select(Purchase, Contract, FinalDetermination, CurrencyRate)
                #     .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                #     .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                #     .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                # )     
                records, data, user = self.main_window.return_variabels()
                # cleaned_filename = data.sub(r'[\\/*?:"<>| ]', '_', data)
                self.data = list(self.contracts.tuples())
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
        self.contracts =  (
    Contract.select(
        Purchase.Id,
        Contract.RegistryNumber,
        Purchase.RegistryNumber,
        Contract.ContractNumber,
        Contract.StartDate,
        Contract.ContractPrice,
        Contract.ContractingAuthority,
        Contract.WinnerExecutor,
        Purchase.PurchaseName,
        Contract.TotalApplications,
        Contract.AdmittedApplications,
        Contract.RejectedApplications,
        Contract.PriceProposal,
        Contract.Applicant,
        Contract.Applicant_satatus,
        Contract.ContractIdentifier,
        Contract.EndDate,
        Contract.AdvancePayment,
        Contract.ReductionNMC,
        Contract.ReductionNMCPercent,
        Contract.SupplierProtocol,
        Contract.ContractFile,
        Purchase.InitialMaxContractPrice,
    )
    .join(Purchase, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
    .where(Contract.ContractNumber != "Нет данных"))
    #     self.contracts  = (
    # Purchase.select(
    #     Purchase.Id,
    #     Contract.RegistryNumber,
    #     Purchase.RegistryNumber,
    #     Contract.ContractNumber,
    #     Contract.StartDate,
    #     Contract.ContractPrice,
    #     Contract.ContractingAuthority,
    #     Contract.WinnerExecutor,
    #     Purchase.PurchaseName,
    #     Contract.TotalApplications,
    #     Contract.AdmittedApplications,
    #     Contract.RejectedApplications,
    #     Contract.PriceProposal,
    #     Contract.Applicant,
    #     Contract.Applicant_satatus,
    #     Contract.ContractIdentifier,
    #     Contract.EndDate,
    #     Contract.AdvancePayment,
    #     Contract.ReductionNMC,
    #     Contract.ReductionNMCPercent,
    #     Contract.SupplierProtocol,
    #     Contract.ContractFile
    # )
    # .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
    # .where(Contract.ContractNumber != "Нет данных"))
        self.contracts_list = list(self.contracts.tuples())
        self.update()
        self.show_all_contracts()
    def return_filters_variabels(self):
    
        # search_input = self.selected_text if self.selected_text is not None else ""
        sort_by_putch_order =  self.sort_by_putch_order.currentText() if self.sort_by_putch_order.currentText() != "Фильтровать по Закону"  else "-"
        min_date = self.min_data_input.date().toPython() if self.min_data_input.date().toPython() is not None  else "-"
        max_date = self.max_data_input.date().toPython() if self.max_data_input.date().toPython() is not None  else "-"
        min_price = self.min_price_input.text() if self.min_price_input.text() is not None  else "Фильтр не применен"
        max_price = self.max_price_input.text()  if self.max_price_input.text() is not None  else "Фильтр не применен"
        sort_by_putch_okpd2 = self.sort_by_putch_okpd2.currentText() if self.sort_by_putch_okpd2.currentText() != "Фильтровать по ОКПД2" else "-"
        return sort_by_putch_order,min_date,max_date,min_price,max_price,sort_by_putch_okpd2

        
        

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidgetAll()
#     csv_loader_widget.show()
#     sys.exit(app.exec())