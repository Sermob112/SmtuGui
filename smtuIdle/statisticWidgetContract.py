from PySide6 import QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import *
from peewee import *
import pandas as pd
from smtuIdle.BD.models import *
import json
from functools import partial
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

REDUCTION_ORDER = [
    "Снижение более 50%",
    "Снижение 20–50%",
    "Снижение 5–20%",
    "Снижение 1–5%",
    "0%",
    "Повышение 1–5%",
    "Повышение 5–20%",
    "Повышение 20–50%",
    "Повышение более 50%",
]
PENALTY_BUCKET_ORDER = [
    "0 ₽",
    "До 100 тыс. ₽",
    "100–500 тыс. ₽",
    "500 тыс.–1 млн ₽",
    "1–2 млн ₽",
    "2–3 млн ₽",
    "3–4 млн ₽",
    "4–5 млн ₽",
    "Более 5 млн ₽",
]


REDUCTION_ORDER = [
    "Снижение более 50%",
    "Снижение 20–50%",
    "Снижение 5–20%",
    "Снижение 1–5%",
    "0%",
    "Повышение 1–5%",
    "Повышение 5–20%",
    "Повышение 20–50%",
    "Повышение более 50%",
    "Нет данных",
]


class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(Canvas, self).__init__(fig)
        self.setParent(parent)
        self.label_texts = [
            "Анализ количества победителей",
            "Анализ количества заключённых контрактов",
            "Анализ количества указанных номеров контрактов",
            "Анализ соотношения НМЦК и ЦКЕП и цены контракта,\nзаключённого по результатам конкурса",
            "Анализ количества ценовых предложений поставщиков\nпри обосновании НМЦК и ЦКЕП методом анализа рынка",
            "Анализ уровня цены контракта, заключённого\nпо результатам конкурса",
            "Анализ диапазона значений коэффициента вариации\nпри определении НМЦК и ЦКЕП",
            "Анализ изменения сроков исполнения контрактов",  # ← сроки
            "Анализ изменения цены контракта",  # ← цена
            "Анализ начисленных и оплаченных неустоек",
        ]

    def plot(self, data, x_column, y_column):
        try:
            self.axes.clear()
            # Построение графика
            data.plot(kind='bar', x=x_column, y=y_column, ax=self.axes)
            self.axes.legend([y_column])  # Добавляем легенду
            self.draw()
        except Exception as e:
            print("Error plotting graph:", e)


    def plot_pie(self, data, x_column, y_column, pos):
        self.axes.clear()
        self.axes.pie(data[y_column], labels=data[x_column], autopct='%1.1f%%', startangle=90)
        wedges, texts, autotexts = self.axes.pie(
            data[y_column], labels=data[x_column], autopct='%1.1f%%', startangle=90
        )
        self.axes.legend(wedges, data[x_column], title="Категории", loc='center left', bbox_to_anchor=(1, 0.5))
        self.axes.set_title(self.label_texts[pos])
        self.draw()


class StatisticWidgetContract(QWidget):
    def __init__(self, all_purches,role):
        super().__init__()
        self.all_purchase = all_purches
        self.role = role
        self.init_ui()
        
    def init_ui(self):
        self.formular_texts = [
            "Методы, использованные для определения НМЦК и ЦКЕП",
            "Формулировки, применяемые государственными\n заказчиками при объявлении закупки",
            "Классификации ОКПД2",
            "Количество заявок\nна участие в закупке",
            "Количество допущенных\nзаявок на участие в закупке",
            "Количество отклоненных\nзаявок на участие в закупке",
            "Соотношение НМЦК и ЦКЕП и цены контракта,\nзаключенного по результатам конкурса",
            "Количество ценовых предложений поставщиков\nпри обосновании НМЦК и ЦКЕП методом анализа рынка",
            "Уровень цены контракта, заключенного\nпо результатам конкурса",
            "Диапазон значений коэффициента вариации\nпри определении НМЦК и ЦКЕП"
        ]
        # Создаем лейбл
        self.label_text = "Статистический анализ методов, использованных для определения НМЦК и ЦКЕП"
        self.label = QLabel(self.label_text)
        self.label_filter_order = QLabel("Фильтры: ")
        self.label_filter_data = QLabel("Фильтры: ")
        self.label_filter_price = QLabel("Фильтры: ")
        self.label_filter_okpd2 = QLabel("Фильтры: ")
        self.table = QTableWidget(self)
         # Создаем кнопки "Назад" и "Вперед"
        # btn_back = QPushButton("Назад", self)
        # btn_forward = QPushButton("Вперед", self)
        self.toExcel = QPushButton("Экспорт в Excel", self)
        self.Update = QPushButton("Обновить", self)
        self.Reset_filters = QPushButton("Сбросить фильтры", self)
        # btn_analysis = QPushButton("Анализ", self)
        self.query = self.all_purchase.return_filtered_contracts()

        self.current_data_index = 0
        self.all_data = []

        # --- 2. Подписываем сигналы ---
        self.toExcel.clicked.connect(self.export_to_excel_clicked)
        self.Update.clicked.connect(self.update_data)
        self.Reset_filters.clicked.connect(self.reset_filters)

        # --- 3. Теперь безопасно вызываем update_data ---


        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
          # Список для хранения всех данных, которые  отобразить в таблице
        self.all_data = [self.winner_analis(), self.count_non_zero_contract_prices()
                         ,self.count_non_zero_contract_num(),self.analisNMCKReduce()
                         ,self.analyze_price_count(), self.analisMAxPrice(),self.analisCoeffVar(),
                         self.analyze_contract_deadlines(),  # ← сроки
                         self.analyze_contract_price_changes(),  # ← цена
                         self.analyze_contract_penalties(),
                         ]
        
        
        self.label_texts = [
            "Анализ количества победителей",
            "Анализ количества заключённых контрактов",
            "Анализ количества указанных номеров контрактов",
            "Анализ соотношения НМЦК и ЦКЕП и цены контракта,\nзаключённого по результатам конкурса",
            "Анализ количества ценовых предложений поставщиков\nпри обосновании НМЦК и ЦКЕП методом анализа рынка",
            "Анализ уровня цены контракта, заключённого\nпо результатам конкурса",
            "Анализ диапазона значений коэффициента вариации\nпри определении НМЦК и ЦКЕП",
            "Анализ изменения сроков исполнения контрактов",  # ← сроки
            "Анализ изменения цены контракта",  # ← цена
            "Анализ начисленных и оплаченных неустоек",
        ]
        self.buttons = []
        self.update_data()
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
         # Добавляем кнопку выпадающего меню Первый этап
        self.FirstStage = QPushButton("Анализ количественных характеристик контрактов")
        self.FirstStage.setIcon(QIcon("Pics/right-arrow.png"))
        self.FirstStage.setMaximumWidth(400)
        self.FirstStage.setStyleSheet("text-align: left; padding-left: 10px;font-size: 11pt;")
        self.FirstStage.clicked.connect(self.toggle_stage_1)
         # колапсирующее окно Первый этап
        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        self.Qword = QLabel("Анализ количественных характеристик контрактов")
        menu_layout.addWidget(self.Qword)
        for index, text in enumerate(self.label_texts[:3]):
           
            button = QtWidgets.QPushButton()
            button.setText(text) 
            button.setFixedSize(400,50)
            size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
            button.setSizePolicy(size_policy)
            button.setStyleSheet("text-align: left;padding-left: 8px;")
            button.clicked.connect(partial(self.show_specific_data, index, button))
            menu_layout.addWidget(button,alignment=Qt.AlignmentFlag.AlignTop)
            self.buttons.append(button)
        # menu_layout.addWidget(line)
        
        self.menu_content.setLayout(menu_layout)
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(QVBoxLayout())
        self.menu_frame.layout().addWidget(self.menu_content)
        self.menu_frame.setVisible(False)


        self.ThirdStage = QPushButton("Анализ контрактов")
        self.ThirdStage.setIcon(QIcon("Pics/right-arrow.png"))
        self.ThirdStage.setMaximumWidth(400)
        self.ThirdStage.setStyleSheet("text-align: left;padding-left: 10px;font-size: 11pt;")
        self.ThirdStage.clicked.connect(self.toggle_stage_3)
         # колапсирующее окно Первый этап
        self.menu_content_3 = QWidget()
        menu_layout_3 = QVBoxLayout()
        self.Qword_3 = QLabel("Анализ заключенных контрактов и разницы НМЦК и ЦКЕИ")
        menu_layout_3.addWidget(self.Qword_3)
        for index, text in enumerate(self.label_texts[3:]):
            button = QtWidgets.QPushButton(text)
            button.setFixedSize(400, 50)
            
            size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
            button.setSizePolicy(size_policy)
            button.setStyleSheet("text-align: left;padding-left: 8px;")
            button.clicked.connect(partial(self.show_specific_data, index + 3, button))
            menu_layout_3.addWidget(button,alignment=Qt.AlignmentFlag.AlignTop)
            self.buttons.append(button)
        # menu_layout.addWidget(line)
        self.menu_content_3.setLayout(menu_layout_3)
        self.menu_frame_3 = QFrame()
        self.menu_frame_3.setLayout(QVBoxLayout())
        self.menu_frame_3.layout().addWidget(self.menu_content_3)
        self.menu_frame_3.setVisible(False)
        self.buttons_layout = QVBoxLayout()
        main_layout = QHBoxLayout(self)
        self.buttons_layout.addWidget(self.FirstStage)
        self.buttons_layout.addWidget(self.menu_frame)
        self.buttons_layout.addWidget(self.ThirdStage)
        self.buttons_layout.addWidget(self.menu_frame_3)

        self.buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # scroll_area.setWidget(scroll_widget)
        # main_layout.addWidget(scroll_area)
        main_layout.addLayout(self.buttons_layout)
        
        self.buttonConvas = QPushButton('Показать график')
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.gist(), 'Гистограмма')
        self.tab_widget.addTab(self.pie(), 'Круговая диаграмма')
        self.tab_widget.hide()
        self.buttonConvas.hide()
        self.buttonConvas.clicked.connect(self.show_convas)
        #  вертикальный слой для метки и таблицы
        self.vertical_layout = QVBoxLayout(self)
        self.filter_layout = QHBoxLayout(self)
        self.vertical_layout.addLayout(self.filter_layout)
        self.vertical_layout.addWidget(self.label)
        self.vertical_layout.addWidget(self.table)
        
        # self.vertical_layout.addWidget(self.canvas)
        self.vertical_layout.addWidget(self.buttonConvas)
        self.vertical_layout.addWidget(self.tab_widget)
        
        # Добавьте вертикальный слой с меткой и таблицей в горизонтальный слой
        main_layout.addLayout(self.vertical_layout)

 #  вертикальный слой для кнопок внизу
        button_layout = QVBoxLayout(self)
        button_layout2_H = QHBoxLayout(self)
        button_layout2 = QVBoxLayout(self)
       
        button_layout2_H.addWidget(self.Update)
        button_layout2_H.addWidget(self.Reset_filters)
        button_layout2.addWidget(self.toExcel)
        button_layout2.addLayout(button_layout2_H)
        #  вертикальные слои с кнопками в горизонтальный слой
        self.vertical_layout.addLayout(button_layout)
        self.vertical_layout.addLayout(button_layout2)
        
        #  основной макет для вашего виджета
        self.setLayout(main_layout)
        #  отображение данных
        self.show_current_data()
        self.highlight_first_button()

        self.setLayout(main_layout)

        if self.role == "Гость":
            self.toExcel.hide()
        else:
            self.toExcel.show()

    def gist(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.canvas_gist = Canvas()
        layout.addWidget(self.canvas_gist)
        self.plot_graph()
        return tab
    def pie(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.canvas_pie = Canvas()
        layout.addWidget(self.canvas_pie)
        self.plot_pie()
        return tab
    def show_convas(self):
        # current_policy = self.table.sizeAdjustPolicy()
        return

    def plot_graph(self):
        # self.table.hide()
        current_data = self.all_data[self.current_data_index]
        # pivot_table, column_sums = self.winner_analis()
        x = current_data[0].columns[0]
        y = current_data[0].columns[1]
        self.canvas_gist.plot(current_data[0],x,y)
    def plot_pie(self):
        # self.table.hide()
        current_data = self.all_data[self.current_data_index]
        # pivot_table, column_sums = self.winner_analis()
        x = current_data[0].columns[0]
        y = current_data[0].columns[1]
        self.canvas_pie.plot_pie(current_data[0],x,y,self.current_data_index)
    def toggle_stage_1(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.FirstStage.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FirstStage.setIcon(QIcon("Pics/right-arrow.png"))

    def toggle_stage_2(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_2.setVisible(not self.menu_frame_2.isVisible())
        if self.menu_frame_2.isVisible():
            self.SecondStage.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.SecondStage.setIcon(QIcon("Pics/right-arrow.png"))
    def toggle_stage_3(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame_3.setVisible(not self.menu_frame_3.isVisible())
        if self.menu_frame_3.isVisible():
            self.ThirdStage.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.ThirdStage.setIcon(QIcon("Pics/right-arrow.png"))

    def update_data(self):
        self.query = self.all_purchase.return_filtered_contracts()

        self.all_data = [
            self.winner_analis(),
            self.count_non_zero_contract_prices(),
            self.count_non_zero_contract_num(),
            self.analisNMCKReduce(),
            self.analyze_price_count(),
            self.analisMAxPrice(),
            self.analisCoeffVar(),
            self.analyze_contract_deadlines(),
            self.analyze_contract_price_changes(),
            self.analyze_contract_penalties(),
        ]

        # Защита от выхода индекса за границы
        if not self.all_data:
            self.current_data_index = 0
            self.clear_table()
            return

        self.current_data_index = min(
            self.current_data_index,
            len(self.all_data) - 1
        )

        # Важно: label_texts инициализируется до вызова update_data
        self.show_current_data()

        for btn in self.buttons:
            btn.setStyleSheet("text-align: left;")

        if self.buttons:
            active_index = min(self.current_data_index, len(self.buttons) - 1)
            self.buttons[active_index].setStyleSheet(
                "text-align: left; background-color: lightGreen;"
            )

        sort_by_putch_order, min_date, max_date, min_price, max_price, okpd2 = (
            self.all_purchase.return_filters_variabels()
        )

        self.label_filter_data.setText(
            f"Фильтр по дате: с {min_date} по {max_date}"
        )
        self.label_filter_order.setText(
            f"Фильтр по закону: {sort_by_putch_order}"
        )
        self.label_filter_price.setText(
            f"Фильтр по цене: {min_price} - {max_price}"
        )
        self.label_filter_okpd2.setText(
            f"Фильтр по ОКПД2: {okpd2}"
        )

    def analyze_price_count(self):
        coeff_range_order = [
            'Ценовое предложение №1',
            'Ценовое предложение №2',
            'Ценовое предложение №3',
            'Ценовое предложение №4',
            'Ценовое предложение №5',
            'Ценовое предложение №6',
        ]
        bucket_order = ['Одно', 'Два', 'Три', 'Четыре', 'Пять', 'Более пяти']

        query = (Purchase
                 .select(Purchase.PurchaseOrder, Contract.PriceProposal)
                 .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                 .where(Contract.PriceProposal.is_null(False))
                 .dicts())

        df_data = []

        for row in query:
            raw = row.get("PriceProposal")
            if not raw:
                continue

            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            if isinstance(parsed, list):
                price_proposal_dict = {}
                for item in parsed:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            price_proposal_dict[k] = v
            elif isinstance(parsed, dict):
                price_proposal_dict = parsed
            else:
                continue

            # Считаем ОБЩЕЕ количество заполненных предложений в записи
            filled_count = sum(
                1 for key in coeff_range_order
                if price_proposal_dict.get(key, "") not in ("", "Нет данных")
            )

            if filled_count == 0:
                continue

            # Определяем категорию по количеству заполненных предложений
            if filled_count >= 6:
                bucket = 'Более пяти'
            else:
                bucket = bucket_order[filled_count - 1]

            df_data.append([row.get("PurchaseOrder"), bucket])

        if not df_data:
            empty_df = pd.DataFrame(columns=[self.formular_texts[7]] + bucket_order)
            empty_df.set_index(self.formular_texts[7], inplace=True)
            return empty_df.T, pd.Series(dtype=float)

        df = pd.DataFrame(df_data, columns=['PurchaseOrder', self.formular_texts[7]])

        pivot_table = df.pivot_table(
            index=self.formular_texts[7],
            columns='PurchaseOrder',
            aggfunc='size',
            fill_value=0
        )
        pivot_table = pivot_table.reindex(bucket_order, axis=0, fill_value=0)

        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums = pivot_table.sum()
        column_sums['Суммы'] = column_sums.sum()

        return pivot_table, column_sums
    

    def count_non_empty_values(self, dictionary):
        count = 0
        for key, value in dictionary.items():
            if value != "Нет данных" :
                count += 1
        return count
    def reset_filters(self):
        self.all_purchase.resetFilters()
        self.update_data()
    def winner_analis(self):
   
        #Статистический анализ методов, использованных для определения НМЦК и ЦКЕП
        contracts = self.query
    
        df = pd.DataFrame([(contract.WinnerExecutor, contract.Id) for contract in contracts], columns=['WinnerExecutor', 'Count'])
        
        # Создаем сводную таблицу по победителям
        pivot_table = df.pivot_table(index='WinnerExecutor', aggfunc='size', fill_value=0).reset_index()
      
        pivot_table.columns = ['Победитель-исполнитель контракта', 'Единицы']

        column_sums = pivot_table['Единицы'].sum()
        column_sums = pd.DataFrame({'Единицы': [column_sums]})
        column_sums.index = ['Итого']
   
        return pivot_table,column_sums
    
    def count_non_zero_contract_prices(self):
    # Получаем список всех контрактов
        contracts = self.query

        # Считаем количество контрактов, у которых ContractPrice != 0
        df = pd.DataFrame([(contract.ContractPrice, contract.Id) for contract in contracts if contract.ContractPrice != 0], 
                      columns=['Цена', 'Единицы'])
        
        # Создаем сводную таблицу по победителям
        pivot_table = df.pivot_table(index='Цена', aggfunc='size', fill_value=0).reset_index()
        pivot_table.columns = ['Цена', 'Единицы']
        
        # Вычисляем сумму ненулевых значений ContractPrice
        column_sums = pivot_table['Единицы'].count()
        
        # Создаем DataFrame для суммы
        column_sums_df = pd.DataFrame({'Единицы': [column_sums]})
        column_sums_df.index = ['Итого']
        # print(column_sums)
        return pivot_table, column_sums_df
    
    def count_non_zero_contract_num(self):
    # Получаем список всех контрактов
        contracts = self.query

        # Считаем количество контрактов, у которых ContractPrice != 0
        df = pd.DataFrame([(contract.ContractNumber, contract.Id) for contract in contracts if contract.ContractNumber != 'Нет данных'], 
                      columns=['Номер контракта', 'Единицы'])
        
        # Создаем сводную таблицу по победителям
        pivot_table = df.pivot_table(index='Номер контракта', aggfunc='size', fill_value=0).reset_index()
        pivot_table.columns = ['Номер контракта', 'Единицы']
        
        # Вычисляем сумму ненулевых значений ContractPrice
        column_sums = pivot_table['Единицы'].count()
        
        # Создаем DataFrame для суммы
        column_sums_df = pd.DataFrame({'Единицы': [column_sums]})
        column_sums_df.index = ['Итого']
        return pivot_table, column_sums_df

    def analisMAxPrice(self):
        purchases = self.query
        price_range_order = [
            'Цена контракта более 100 000 000 тыс.руб.',
            'Цена контракта 5 000 000 - 10 000 000 тыс.руб.',
            'Цена контракта 1 000 000 - 5 000 000 тыс.руб.',
            'Цена контракта 500 000-  1 000 000 тыс.руб.',
            'Цена контракта 200 000 - 500 000 тыс.руб.',
            'Цена контракта 100 000 - 200 000 тыс.руб.',
            'Менее 100 тыс.руб'
          
        ]
        # Создаем DataFrame
        df = pd.DataFrame([(purchase.purchase.PurchaseOrder, purchase.ContractPrice) for purchase in purchases],
                       columns=['PurchaseOrder',f'{self.formular_texts[8]}'])
        df[f'{self.formular_texts[8]}'] = df.apply(self.determine_price_range, axis=1)
        df[f'{self.formular_texts[8]}'] = pd.Categorical(df[f'{self.formular_texts[8]}'], categories=price_range_order, ordered=True)
        df = df.sort_values(f'{self.formular_texts[8]}')
        pivot_table = df.pivot_table(index=f'{self.formular_texts[8]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
        return pivot_table, column_sums2 
    def analisCoeffVar(self):
        purchases = self.query
        coeff_range_order = [
      'Значение коэффициента вариации 0%',
        'Значение коэффициента вариации 0-1%',
        'Значение коэффициента вариации 1-2%',
        'Значение коэффициента вариации 2-5%',
        'Значение коэффициента вариации 5-10%',
        'Значение коэффициента вариации 10-20%',
        'Значение коэффициента вариации 20-33%',
        'Значение коэффициента вариации более 33%'
    ]
        # Создаем DataFrame
        df = pd.DataFrame([(purchase.purchase.PurchaseOrder, purchase.purchase.CoefficientOfVariation) for purchase in purchases],
                       columns=['PurchaseOrder', f'{self.formular_texts[9]}'])
        df[f'{self.formular_texts[9]}'] = df.apply(self.determine_var_range, axis=1)
        df[f'{self.formular_texts[9]}'] = pd.Categorical(df[f'{self.formular_texts[9]}'], categories=coeff_range_order, ordered=True)
        df = df.sort_values(f'{self.formular_texts[9]}')
        pivot_table = df.pivot_table(index=f'{self.formular_texts[9]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
        return pivot_table, column_sums2 
    
    def analisNMCKReduce(self):
       
        coeff_range_order = [
        'Цена контракта совпадает с НМЦК и ЦКЕП',
        'Цена контракта ниже НМЦК и ЦКЕП на 0-1%',
        'Цена контракта ниже НМЦК и ЦКЕП на 1-5%',
        'Цена контракта ниже НМЦК и ЦКЕП на 5-10%',
        'Цена контракта ниже НМЦК и ЦКЕП на 10-20%',
        'Цена контракта ниже НМЦК и ЦКЕП более 20%',

    ]
        # Создаем DataFrame
        query = self.query
        t = list(query)
        df = pd.DataFrame([(purchase.purchase.PurchaseOrder, purchase.ReductionNMC) for purchase in t],
                           columns=['PurchaseOrder',f'{self.formular_texts[6]}'])
        df[f'{self.formular_texts[6]}'] = df.apply(self.determine_NMCK_range, axis=1)
        df[f'{self.formular_texts[6]}'] = pd.Categorical(df[f'{self.formular_texts[6]}'], categories=coeff_range_order, ordered=True)
        df = df.sort_values(f'{self.formular_texts[6]}')
        pivot_table = df.pivot_table(index=f'{self.formular_texts[6]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
        return pivot_table, column_sums2

    def save_to_excel_combined_extended(
            self,
            pivot_tables_purchase,
            column_sums_purchase,
            pivot_tables_max_price,
            column_sums_max_price,
            pivot_tables_new,
            column_sums_new,
            output_excel_path,
    ):
        data_to_export = {}

        # Старые таблицы (победители, цены, номера)
        for idx, (pivot_table_purchase, column_sum_purchase) in enumerate(
                zip(pivot_tables_purchase, column_sums_purchase)
        ):
            excel_df_purchase = pd.DataFrame(
                columns=["Метод"] + list(pivot_table_purchase.columns) + ["Суммы"]
            )

            for method, row in pivot_table_purchase.iterrows():
                excel_df_purchase = pd.concat(
                    [
                        excel_df_purchase,
                        pd.DataFrame(
                            [[method] + list(row) + [str(row["Единицы"])]],
                            columns=excel_df_purchase.columns,
                        ),
                    ]
                )

            column_sums_purchase_row = ["Суммы"] + list(column_sum_purchase) + [
                column_sum_purchase.sum()
            ]
            if len(column_sums_purchase_row) == len(excel_df_purchase.columns):
                excel_df_purchase = pd.concat(
                    [
                        excel_df_purchase,
                        pd.DataFrame([column_sums_purchase_row], columns=excel_df_purchase.columns),
                    ]
                )

            sheet_name = self.label_texts[idx][:20].replace("/", "_").replace("\\", "_")
            data_to_export[sheet_name] = excel_df_purchase

        # Старые таблицы (цены, НМЦК, вариация, предложения)
        for idx, (pivot_table_max_price, column_sum_max_price) in enumerate(
                zip(pivot_tables_max_price, column_sums_max_price)
        ):
            excel_df_max_price = pd.DataFrame(
                columns=["Метод"] + list(pivot_table_max_price.columns) + ["Суммы"]
            )

            for method, row in pivot_table_max_price.iterrows():
                excel_df_max_price = pd.concat(
                    [
                        excel_df_max_price,
                        pd.DataFrame(
                            [[method] + list(row) + [str(row.sum())]],
                            columns=excel_df_max_price.columns,
                        ),
                    ]
                )

            column_sums_max_price_row = ["Суммы"] + list(column_sum_max_price) + [
                column_sum_max_price["Суммы"]
            ]
            if len(column_sums_max_price_row) == len(excel_df_max_price.columns):
                excel_df_max_price = pd.concat(
                    [
                        excel_df_max_price,
                        pd.DataFrame([column_sums_max_price_row], columns=excel_df_max_price.columns),
                    ]
                )

            sheet_name = self.label_texts[idx + 3][:20].replace("/", "_").replace("\\", "_")
            data_to_export[sheet_name] = excel_df_max_price

        # Новые таблицы (сроки, цена, штрафы)
        new_labels = [
            "Сроки",
            "Изменение цены",
            "Штрафы",
        ]

        for idx, (pivot_table_new, column_sum_new) in enumerate(
                zip(pivot_tables_new, column_sums_new)
        ):
            excel_df_new = pd.DataFrame(
                columns=["Метод"] + list(pivot_table_new.columns) + ["Суммы"]
            )

            for method, row in pivot_table_new.iterrows():
                excel_df_new = pd.concat(
                    [
                        excel_df_new,
                        pd.DataFrame(
                            [[method] + list(row) + [str(row.sum())]],
                            columns=excel_df_new.columns,
                        ),
                    ]
                )

            column_sums_new_row = ["Суммы"] + list(column_sum_new) + [
                column_sum_new["Суммы"]
            ]
            if len(column_sums_new_row) == len(excel_df_new.columns):
                excel_df_new = pd.concat(
                    [
                        excel_df_new,
                        pd.DataFrame([column_sums_new_row], columns=excel_df_new.columns),
                    ]
                )

            sheet_name = new_labels[idx].replace("/", "_").replace("\\", "_")
            data_to_export[sheet_name] = excel_df_new

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                with pd.ExcelWriter(
                        f"{selected_file}/{output_excel_path}", engine="openpyxl"
                ) as writer:
                    for sheet_name, df in data_to_export.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")

    def clear_table(self):
        self.table.setRowCount(0)

    def populate_table_2(self, data, sums):
        # Очищаем таблицу перед обновлением
        self.clear_table()
        self.table.setColumnWidth(0, 500)

        # Получаем список всех уникальных законов
        all_purchase_orders = set(data.columns.tolist())
        all_purchase_orders.remove('Общий итог')

        # Для многоуровневого индекса заголовок первого столбца
        if isinstance(data.index, pd.MultiIndex):
            first_column_name = ' / '.join(data.index.names)
        else:
            first_column_name = data.index.name

        if self.current_data_index == 4:
            first_column_name = 'Количество ценовых предложений\n поставщиков при обосновании НМЦК и ЦКЕП методом анализа рынка'

        # Устанавливаем количество столбцов в таблице
        num_columns = len(all_purchase_orders) + 2
        self.table.setColumnCount(num_columns)

        # Устанавливаем заголовки столбцов
        header_labels = [first_column_name] + list(all_purchase_orders) + ["Общий итог"]
        self.table.setHorizontalHeaderLabels(header_labels)

        # Добавляем строки в таблицу
        for index, row in data.iterrows():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Преобразуем индекс в строку (для MultiIndex это будет кортеж)
            if isinstance(index, tuple):
                index_str = ' | '.join(str(i) for i in index)
            else:
                index_str = str(index)

            self.table.setItem(row_position, 0, QTableWidgetItem(index_str))

            for col_index, purchase_order in enumerate(all_purchase_orders):
                value = row.get(purchase_order, 0)
                self.table.setItem(row_position, col_index + 1, QTableWidgetItem(str(value)))

            row_sum = row.get('Общий итог', 0)
            item = QTableWidgetItem(str(row_sum))
            self.table.setItem(row_position, self.table.columnCount() - 1, item)

        # Добавляем строку с суммами
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem('Суммы'))

        for col_index, key in enumerate(sums.keys()):
            value = sums[key]
            self.table.setItem(row_position, col_index + 1, QTableWidgetItem(str(value)))

    def populate_table(self, data, sums):
        # Получаем список всех уникальных законов
        all_purchase_orders = set(data.columns)

        # Устанавливаем количество столбцов в таблице
        num_columns = len(all_purchase_orders) # Плюс два для "Метод" и "Общий итог"
        self.table.setColumnCount(num_columns)

        # Устанавливаем заголовки столбцов
        header_labels = list(all_purchase_orders)
        self.table.setHorizontalHeaderLabels(header_labels)

        # Добавляем строки в таблицу
        for index, row in data.iterrows():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Заполняем ячейки в строке
            self.table.setItem(row_position, 0, QTableWidgetItem(index))  # Метод
            for col_index, purchase_order in enumerate(all_purchase_orders):
                value = row.get(purchase_order, 0)  # Получаем значение из DataFrame, если оно есть, иначе 0
                self.table.setItem(row_position, col_index , QTableWidgetItem(str(value)))

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem('Суммы'))
        for col_index, value in enumerate(sums.iloc[0]):
            self.table.setItem(row_position, col_index + 1, QTableWidgetItem(str(value)))  # Сдвигаем индекс столбца на 1

    def determine_NMCK_range(self,row):
        term =  row[f'{self.formular_texts[6]}']
        try:
            if term * 100 == 0:
                return 'Цена контракта совпадает с НМЦК и ЦКЕП'
            elif 0 <= term * 100 <= 1:
                return 'Цена контракта ниже НМЦК и ЦКЕП на 0-1%'
            elif 1 <= term * 100 <= 5:
                return 'Цена контракта ниже НМЦК и ЦКЕП на 1-5%'
            elif 5 <= term * 100<= 10:
                return 'Цена контракта ниже НМЦК и ЦКЕП на 5-10%'
            elif 10 <= term * 100 <= 20:
                return 'Цена контракта ниже НМЦК и ЦКЕП на 10-20%'
            else:
                return 'Цена контракта ниже НМЦК и ЦКЕП более 20%'
        except:
            pass
        
    def determine_var_range(self,row):
        term =  row[f'{self.formular_texts[9]}'] 
        try:
            if term * 100 == 0:
                return 'Значение коэффициента вариации 0%'
            elif 0 <= term * 100 <= 1:
                return 'Значение коэффициента вариации 0-1%'
            elif 1 <= term * 100 <= 2:
                return 'Значение коэффициента вариации 1-2%'
            elif 2 <= term * 100<= 5:
                return 'Значение коэффициента вариации 2-5%'
            elif 5 <= term * 100<= 10:
                return 'Значение коэффициента вариации 5-10%'
            elif 10 <= term* 100 <= 20:
                return 'Значение коэффициента вариации 10-20%'
            elif 20 <= term* 100 <= 33:
                return 'Значение коэффициента вариации 10-20%'
            else:
                return 'Более 33%'
        except:
            pass
        
    def determine_price_range(self,row):
        qyt = row[f'{self.formular_texts[8]}'] 
        if qyt > 100000000:
            return 'Цена контракта более 100 000 000 тыс.руб.'
        elif 5000000 <= qyt <= 10000000:
            return 'Цена контракта 5 000 000 - 10 000 000 тыс.руб.'
        elif 1000000 <= qyt <= 5000000:
            return 'Цена контракта 1 000 000 - 5 000 000 тыс.руб.'
        elif 500000 <= qyt <= 1000000:
            return 'Цена контракта 500 000-  1 000 000 тыс.руб.'
        elif 200000 <= qyt <= 500000:
            return 'Цена контракта 200 000 - 500 000 тыс.руб.'
        elif 100000 <= qyt <= 200000:
            return 'Цена контракта 100 000 - 200 000 тыс.руб.'

        else:
            return 'Менее 100 тыс.руб'

    def show_current_data(self):
        if not self.all_data:
            self.clear_table()
            return

        if not hasattr(self, "label_texts"):
            return

        if self.current_data_index < 0:
            self.current_data_index = 0

        if self.current_data_index >= len(self.all_data):
            self.current_data_index = len(self.all_data) - 1

        current_data = self.all_data[self.current_data_index]

        self.clear_table()

        if self.current_data_index < 3:
            self.populate_table(current_data[0], current_data[1])
        else:
            self.populate_table_2(current_data[0], current_data[1])

        if self.current_data_index < len(self.label_texts):
            self.label.setText(
                self.label_texts[self.current_data_index]
            )


    def show_previous_data(self):
        # Уменьшаем индекс данных, если это возможно
        if self.current_data_index > 0:
            self.current_data_index -= 1
            self.show_current_data()
            self.label.setText(self.label_texts[self.current_data_index])

    def show_next_data(self):
        # Увеличиваем индекс данных, если это возможно
        if self.current_data_index < len(self.all_data) - 1:
            self.current_data_index += 1
            self.show_current_data()
            self.label.setText(self.label_texts[self.current_data_index])

    def export_to_excel_clicked(self):
        # Существующие 7 методов
        pivot_tables_purchase1, column_sums_purchase1 = self.winner_analis()
        pivot_tables_purchase2, column_sums_purchase2 = self.count_non_zero_contract_prices()
        pivot_tables_purchase3, column_sums_purchase3 = self.count_non_zero_contract_num()

        pivot_tables_max_price1, column_sums_max_price1 = self.analisMAxPrice()
        pivot_tables_max_price2, column_sums_max_price2 = self.analisNMCKReduce()
        pivot_tables_max_price3, column_sums_max_price3 = self.analisCoeffVar()
        pivot_tables_max_price4, column_sums_max_price4 = self.analyze_price_count()

        # Новые 3 метода
        pivot_deadlines, column_sums_deadlines = self.analyze_contract_deadlines()
        pivot_price_changes, column_sums_price_changes = self.analyze_contract_price_changes()
        pivot_penalties, column_sums_penalties = self.analyze_contract_penalties()

        sort_by_putch_order, min_date, max_date, min_price, max_price, okpd2 = (
            self.all_purchase.return_filters_variabels()
        )

        filters = []
        okpd2 = okpd2.replace(".", "_")
        okpd2 = okpd2.replace(":", "_")

        if sort_by_putch_order:
            filters.append(" " + sort_by_putch_order)
        if okpd2:
            filters.append(str(okpd2))
        if min_date:
            filters.append(" " + str(min_date))
        if max_date:
            filters.append(str(max_date))
        if min_price:
            filters.append(" " + str(min_price))
        if max_price:
            filters.append(str(max_price))

        file_name = (
            f"Данные статистики по Фильтрам контракта {' '.join(filters)}.xlsx"
        )

        self.save_to_excel_combined_extended(
            [
                pivot_tables_purchase1,
                pivot_tables_purchase2,
                pivot_tables_purchase3,
            ],
            [
                column_sums_purchase1,
                column_sums_purchase2,
                column_sums_purchase3,
            ],
            [
                pivot_tables_max_price1,
                pivot_tables_max_price2,
                pivot_tables_max_price3,
                pivot_tables_max_price4,
            ],
            [
                column_sums_max_price1,
                column_sums_max_price2,
                column_sums_max_price3,
                column_sums_max_price4,
            ],
            [
                pivot_deadlines,
                pivot_price_changes,
                pivot_penalties,
            ],
            [
                column_sums_deadlines,
                column_sums_price_changes,
                column_sums_penalties,
            ],
            file_name,
        )

    def show_specific_data(self, index, button):
        # Проверка границ
        if index < 0 or index >= len(self.label_texts):
            return

        for btn in self.buttons:
            btn.setStyleSheet("text-align: left;")

        button.setStyleSheet("text-align: left; background-color: lightGreen;")
        self.active_button = button

        self.current_data_index = index
        self.show_current_data()
        self.label.setText(self.label_texts[self.current_data_index])
    def highlight_first_button(self):
    # Вызываем метод для подсветки первой кнопки
        if self.buttons:
            first_button = self.buttons[0]
            self.show_specific_data(0, first_button)

    def analyze_contract_price_changes(self):
        """
        Анализ изменения цены контракта относительно НМЦК.
        """
        from smtuIdle.BD.models import Purchase, Contract

        contracts = list(self.query)

        records = []
        for c in contracts:
            p = c.purchase

            current_price = c.ContractPrice if c.ContractPrice is not None else None
            nmck = (
                p.InitialMaxContractPriceInCurrency
                if p and p.InitialMaxContractPriceInCurrency is not None
                else None
            )

            reduction_percent = (
                ((current_price - nmck) / nmck) * 100
                if current_price is not None and nmck not in (None, 0)
                else None
            )

            reduction_bucket = self.get_reduction_bucket(reduction_percent)

            records.append({
                "PurchaseOrder": p.PurchaseOrder if p else "—",
                "Снижение относительно НМЦК": reduction_bucket,
            })

        if not records:
            empty_df = pd.DataFrame(columns=["Снижение относительно НМЦК", "Единицы"])
            empty_df.set_index("Снижение относительно НМЦК", inplace=True)
            return empty_df, pd.Series(dtype=float)

        df = pd.DataFrame(records)

        df["Снижение относительно НМЦК"] = pd.Categorical(
            df["Снижение относительно НМЦК"],
            categories=REDUCTION_ORDER,
            ordered=True
        )

        df = df.sort_values("Снижение относительно НМЦК")

        pivot_table = df.pivot_table(
            index="Снижение относительно НМЦК",
            columns="PurchaseOrder",
            aggfunc="size",
            fill_value=0
        )

        pivot_table = pivot_table.reindex(REDUCTION_ORDER, fill_value=0)

        row_totals = pivot_table.sum(axis=1)
        pivot_table["Общий итог"] = row_totals
        column_sums = pivot_table.sum()
        column_sums["Суммы"] = column_sums.sum()

        return pivot_table, column_sums

    def get_reduction_bucket(self, reduction_percent):
        """
        reduction_percent = (current_price - nmck) / nmck * 100
        отрицательное = снижение, положительное = повышение
        """
        if reduction_percent is None:
            return "Снижение более 50%"  # или можно вернуть "Нет данных", если нужно

        if reduction_percent < -50:
            return "Снижение более 50%"
        elif reduction_percent < -20:
            return "Снижение 20–50%"
        elif reduction_percent < -5:
            return "Снижение 5–20%"
        elif reduction_percent < -1:
            return "Снижение 1–5%"
        elif -1 <= reduction_percent <= 1:
            return "0%"
        elif reduction_percent <= 5:
            return "Повышение 1–5%"
        elif reduction_percent <= 20:
            return "Повышение 5–20%"
        elif reduction_percent <= 50:
            return "Повышение 20–50%"
        else:
            return "Повышение более 50%"

    def analyze_contract_penalties(self):
        """
        Анализ штрафов (неустоек, пеней):
        - количество штрафов по диапазонам,
        - сумма начислено,
        - сумма оплачено,
        - сумма долга.
        """
        from smtuIdle.BD.models import Purchase, Contract

        contracts = list(self.query)

        records = []
        total_charged_all = 0.0
        total_paid_all = 0.0

        for c in contracts:
            p = c.purchase

            latest_version = self.get_latest_contract_version(c)
            process_json = getattr(latest_version, "process_info_json", None) if latest_version else None

            penalties = self.extract_penalties(process_json) if process_json else []

            # Сумма по этому контракту
            total_charged = sum(pen["НАЧИСЛЕНО"] for pen in penalties if pen["НАЧИСЛЕНО"] is not None)
            total_paid = sum(pen["ОПЛАЧЕНО"] for pen in penalties if pen["ОПЛАЧЕНО"] is not None)
            debt = total_charged - total_paid

            total_charged_all += total_charged
            total_paid_all += total_paid

            penalty_bucket = self.get_penalty_bucket(debt)

            records.append({
                "PurchaseOrder": p.PurchaseOrder if p else "—",
                "Размер штрафа": penalty_bucket,
                "Начислено": total_charged,
                "Оплачено": total_paid,
                "Долг": debt,
            })

        if not records:
            empty_df = pd.DataFrame(columns=["Размер штрафа", "Единицы"])
            empty_df.set_index("Размер штрафа", inplace=True)
            return empty_df, pd.Series(dtype=float)

        df = pd.DataFrame(records)

        df["Размер штрафа"] = pd.Categorical(
            df["Размер штрафа"],
            categories=PENALTY_BUCKET_ORDER,
            ordered=True
        )

        df = df.sort_values("Размер штрафа")

        # 1. Количество контрактов по диапазонам
        pivot_count = df.pivot_table(
            index="Размер штрафа",
            columns="PurchaseOrder",
            aggfunc="size",
            fill_value=0
        )
        pivot_count = pivot_count.reindex(PENALTY_BUCKET_ORDER, fill_value=0)

        # 2. Сумма начислено
        pivot_charged = df.pivot_table(
            index="Размер штрафа",
            columns="PurchaseOrder",
            values="Начислено",
            aggfunc="sum",
            fill_value=0
        )
        pivot_charged = pivot_charged.reindex(PENALTY_BUCKET_ORDER, fill_value=0)

        # 3. Сумма оплачено
        pivot_paid = df.pivot_table(
            index="Размер штрафа",
            columns="PurchaseOrder",
            values="Оплачено",
            aggfunc="sum",
            fill_value=0
        )
        pivot_paid = pivot_paid.reindex(PENALTY_BUCKET_ORDER, fill_value=0)

        # 4. Сумма долга
        pivot_debt = df.pivot_table(
            index="Размер штрафа",
            columns="PurchaseOrder",
            values="Долг",
            aggfunc="sum",
            fill_value=0
        )
        pivot_debt = pivot_debt.reindex(PENALTY_BUCKET_ORDER, fill_value=0)

        # Итоги по строкам
        for pivot in [pivot_count, pivot_charged, pivot_paid, pivot_debt]:
            row_totals = pivot.sum(axis=1)
            pivot["Общий итог"] = row_totals

        # Итоги по столбцам
        column_sums_count = pivot_count.sum()
        column_sums_count["Суммы"] = column_sums_count.sum()

        column_sums_charged = pivot_charged.sum()
        column_sums_charged["Суммы"] = column_sums_charged.sum()

        column_sums_paid = pivot_paid.sum()
        column_sums_paid["Суммы"] = column_sums_paid.sum()

        column_sums_debt = pivot_debt.sum()
        column_sums_debt["Суммы"] = column_sums_debt.sum()

        # Сохраняем для отображения
        self.penalty_pivot_count = pivot_count
        self.penalty_pivot_charged = pivot_charged
        self.penalty_pivot_paid = pivot_paid
        self.penalty_pivot_debt = pivot_debt

        self.penalty_column_sums_count = column_sums_count
        self.penalty_column_sums_charged = column_sums_charged
        self.penalty_column_sums_paid = column_sums_paid
        self.penalty_column_sums_debt = column_sums_debt

        self.total_charged_all = total_charged_all
        self.total_paid_all = total_paid_all
        self.total_debt_all = total_charged_all - total_paid_all

        # Возвращаем количество для отображения в таблице
        return pivot_count, column_sums_count

    def get_penalty_bucket(self, amount):
        if amount is None or amount == 0:
            return "0 ₽"
        elif amount < 100_000:
            return "До 100 тыс. ₽"
        elif amount < 500_000:
            return "100–500 тыс. ₽"
        elif amount < 1_000_000:
            return "500 тыс.–1 млн ₽"
        elif amount < 2_000_000:
            return "1–2 млн ₽"
        elif amount < 3_000_000:
            return "2–3 млн ₽"
        elif amount < 4_000_000:
            return "3–4 млн ₽"
        elif amount < 5_000_000:
            return "4–5 млн ₽"
        else:
            return "Более 5 млн ₽"
    def analyze_contract_deadlines(self):
        """
        Анализ изменения сроков исполнения контрактов.
        """
        from smtuIdle.BD.models import Purchase, Contract

        contracts = list(self.query)  # это Contract-объекты

        records = []
        for c in contracts:
            p = c.purchase  # объект Purchase, связанный через ForeignKey

            initial_version = self.get_initial_contract_version(c)
            initial_end = self.parse_date_safe(
                initial_version.date_execution_due if initial_version else None
            )
            current_end = self.parse_date_safe(c.EndDate)
            months_diff = (
                self.months_diff_safe(initial_end, current_end)
                if initial_end and current_end else None
            )

            months_bucket = self.get_months_bucket(months_diff)
            records.append({
                "PurchaseOrder": p.PurchaseOrder if p else "—",
                    "Изменение срока": months_bucket,
            })

        if not records:
            empty_df = pd.DataFrame(columns=["Изменение срока", "Единицы"])
            empty_df.set_index("Изменение срока", inplace=True)
            return empty_df, pd.Series(dtype=float)

        df = pd.DataFrame(records)
        pivot_table = df.pivot_table(
            index="Изменение срока",
            columns="PurchaseOrder",
            aggfunc="size",
            fill_value=0
        )

        row_totals = pivot_table.sum(axis=1)
        pivot_table["Общий итог"] = row_totals
        column_sums = pivot_table.sum()
        column_sums["Суммы"] = column_sums.sum()

        return pivot_table, column_sums

    def get_initial_contract_version(self, contract):
        """
        Возвращает первую версию контракта из ContractVersion.
        """
        try:
            from smtuIdle.BD.models import ContractVersion
            first = (
                ContractVersion
                .select()
                .where(ContractVersion.contract == contract)
                .order_by(ContractVersion.version.asc())
                .first()
            )
            return first
        except Exception:
            return None

    def get_latest_contract_version(self, contract):
        """
        Возвращает последнюю версию контракта из ContractVersion.
        """
        try:
            from smtuIdle.BD.models import ContractVersion
            last = (
                ContractVersion
                .select()
                .where(ContractVersion.contract == contract)
                .order_by(ContractVersion.version.desc())
                .first()
            )
            return last
        except Exception:
            return None

    def parse_float_safe(self, value):
        if value is None:
            return None

        s = str(value).strip()
        if not s or s in ("Нет данных", "[]", "None", "null"):
            return None

        import re
        s = re.sub(r"[^\d,.\-]", "", s)

        if not s:
            return None

        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")

        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    def parse_date_safe(self, value):
        if not value:
            return None

        if hasattr(value, "year"):
            return value

        from datetime import datetime
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(str(value)).date()
        except Exception:
            return None

    def months_diff_safe(self, start_date, end_date):
        if not start_date or not end_date:
            return None
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    def get_months_bucket(self, months_diff):
        if months_diff is None:
            return "Нет данных"
        if months_diff == 0:
            return "0 мес"
        elif 0 < months_diff <= 3:
            return "1–3 мес"
        elif 3 < months_diff <= 6:
            return "4–6 мес"
        elif 6 < months_diff <= 12:
            return "7–12 мес"
        else:
            return "Более 12 мес"

    def extract_penalties(self, process_json):
        import json
        import re

        def _parse_json(value):
            if not value:
                return None
            if isinstance(value, (dict, list)):
                return value
            try:
                return json.loads(value)
            except Exception:
                return None

        def clean_price_value(raw):
            if not raw:
                return None
            s = str(raw).strip()
            if not s or s in ("Нет данных", "—", "null", "None"):
                return None
            s = re.sub(r"[^\d,.\-]", "", s)
            if not s:
                return None
            if "," in s and "." in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None

        data = _parse_json(process_json)
        if not isinstance(data, dict):
            return []

        records = []
        try:
            section_key = "информация_о_начислении_неустоек_штрафов_пеней"
            section = data.get(section_key, {})
            for item in section.get("items", []):
                if item.get("kind") != "table":
                    continue

                table = item.get("table", {})
                rows_by_index = table.get("rows_by_index", [])
                headers = table.get("headers", [])

                # Если есть rows (словари) — обрабатываем их
                for row in table.get("rows", []):
                    requirement_raw = row.get("ТРЕБОВАНИЕ", "") or ""
                    payer_raw = row.get("ПРИЧИНА НАЧИСЛЕНИЯ", "") or ""
                    nachisleno_raw = row.get("НАЧИСЛЕНО, ₽", "") or ""
                    oplacheno_raw = row.get("ОПЛАЧЕНО, ₽", "") or ""

                    charged = clean_price_value(nachisleno_raw)
                    paid = clean_price_value(oplacheno_raw)

                    # Если charged None, пробуем взять из rows_by_index
                    if charged is None and rows_by_index:
                        for rbi in rows_by_index:
                            if len(rbi) >= 6:
                                charged_raw = rbi[5]  # 6-й столбец — начислено
                                charged = clean_price_value(charged_raw)
                                break

                    if payer_raw or requirement_raw or paid is not None or charged is not None:
                        records.append({
                            "ПЛАТЕЛЬЩИК": payer_raw,
                            "ТРЕБОВАНИЕ": requirement_raw,
                            "НАЧИСЛЕНО": charged,
                            "ОПЛАЧЕНО": paid,
                        })

                # Если rows пустые, но rows_by_index есть — берём оттуда
                if not table.get("rows") and rows_by_index:
                    for rbi in rows_by_index:
                        if len(rbi) < 5:
                            continue
                        payer_raw = rbi[1] if len(rbi) > 1 else ""
                        requirement_raw = rbi[2] if len(rbi) > 2 else ""
                        nachisleno_raw = rbi[3] if len(rbi) > 3 else ""
                        oplacheno_raw = rbi[4] if len(rbi) > 4 else ""
                        charged_raw = rbi[5] if len(rbi) > 5 else ""

                        charged = clean_price_value(charged_raw)
                        paid = clean_price_value(oplacheno_raw)

                        records.append({
                            "ПЛАТЕЛЬЩИК": payer_raw,
                            "ТРЕБОВАНИЕ": requirement_raw,
                            "НАЧИСЛЕНО": charged,
                            "ОПЛАЧЕНО": paid,
                        })

        except Exception:
            pass
        return records