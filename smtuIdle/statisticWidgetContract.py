from PySide6 import QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import *
from peewee import *
import pandas as pd
from smtuIdle.BD.models import Purchase, Contract
import json
from functools import partial
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(Canvas, self).__init__(fig)
        self.setParent(parent)
        self.label_texts = [
            "Анализ количества заключённых контрактов",
            "Анализ соотношения коэффициента вариации",
            "Количество заявок на участие в закупке",
            "Количество допущенных заявок на участие в закупке",
            "Количество отклонённых заявок на участие в закупке",
            "Итог",
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
        # btn_back.clicked.connect(self.show_previous_data)
        # btn_forward.clicked.connect(self.show_next_data)
        self.toExcel.clicked.connect(self.export_to_excel_clicked)
        self.Update.clicked.connect(self.update_data)
        self.Reset_filters.clicked.connect(self.reset_filters)
        # Инициализация переменной для отслеживания текущего индекса данных
        self.current_data_index = 0
    


        self.table.horizontalHeader().setStretchLastSection(True)
        # Установите политику изменения размеров колонок содержимого
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.table.horizontalHeader().setStretchLastSection(True)

        # self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        
          # Список для хранения всех данных, которые  отобразить в таблице
        self.all_data = [self.winner_analis(), self.count_non_zero_contract_prices()
                         ,self.count_non_zero_contract_num(),self.analisNMCKReduce()
                         ,self.analyze_price_count(), self.analisMAxPrice(),self.analisCoeffVar()]
        
        
        self.label_texts = [
            "Анализ количества победителей",
            "Анализ количества заключённых контрактов",
            "Анализ количества указанных номеров контрактов",
            "Анализ соотношения НМЦК и ЦКЕП и цены контракта,\nзаключённого по результатам конкурса",
            "Анализ количества ценовых предложений поставщиков\nпри обосновании НМЦК и ЦКЕП методом анализа рынка",
            "Анализ уровня цены контракта, заключённого\nпо результатам конкурса",
            "Анализ диапазона значений коэффициента вариации\nпри определении НМЦК и ЦКЕП"
        ]
        self.buttons = []

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
        # button_layout.addWidget(btn_back)
        # button_layout.addWidget(btn_forward)

        #  вертикальный слой для кнопок внизу справа
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
        # self.analisQueryCount()
        # self.analisPriceCount()
        # self.analyze_price_count()
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
        self.all_data = [self.winner_analis(), self.count_non_zero_contract_prices()
                         ,self.count_non_zero_contract_num(),self.analisNMCKReduce()
                         ,self.analyze_price_count(), self.analisMAxPrice(),self.analisCoeffVar()]
        self.show_current_data()
        self.query = self.all_purchase.return_filtered_contracts()
        sort_by_putch_order, min_date, max_date, min_price, max_price, okpd2= self.all_purchase.return_filters_variabels()
        self.filter_layout.addWidget(self.label_filter_data)
        self.filter_layout.addWidget(self.label_filter_order)
        self.filter_layout.addWidget(self.label_filter_price)
        self.filter_layout.addWidget(self.label_filter_okpd2)
        self.label_filter_data.setText(f"Фильтр по дате: с {min_date} по {max_date}")
        self.label_filter_order.setText(f"Фильтр по закону:{sort_by_putch_order}")
        self.label_filter_price.setText(f"Фильтр по цене:{min_price} - {max_price}")
        self.label_filter_okpd2.setText(f"Фильтр по ОКПД2:{okpd2}")

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
        # print(column_sums)
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
     
        # Определите порядок категорий
       

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


    def save_to_excel_combined(self, pivot_tables_purchase, column_sums_purchase, pivot_tables_max_price, column_sums_max_price, output_excel_path):
        data_to_export = {}
   
        for idx, (pivot_table_purchase, column_sum_purchase) in enumerate(zip(pivot_tables_purchase, column_sums_purchase)):
            excel_df_purchase = pd.DataFrame(columns=['Метод'] + list(pivot_table_purchase.columns) + ['Суммы'])

            for method, row in pivot_table_purchase.iterrows():
                excel_df_purchase = pd.concat([excel_df_purchase, pd.DataFrame([[method] + list(row) + [str(row['Единицы'])]], columns=excel_df_purchase.columns)])

            column_sums_purchase_row = ['Суммы'] + list(column_sum_purchase) + [column_sum_purchase.sum()]
            if len(column_sums_purchase_row) == len(excel_df_purchase.columns):
                excel_df_purchase = pd.concat([excel_df_purchase, pd.DataFrame([column_sums_purchase_row], columns=excel_df_purchase.columns)])

            data_to_export[self.label_texts[idx][:20]] =excel_df_purchase
        for idx, (pivot_table_max_price, column_sum_max_price) in enumerate(zip(pivot_tables_max_price, column_sums_max_price)):
            excel_df_max_price = pd.DataFrame(columns=['Метод'] + list(pivot_table_max_price.columns) + ['Суммы'])

            for method, row in pivot_table_max_price.iterrows():
                excel_df_max_price = pd.concat([excel_df_max_price, pd.DataFrame([[method] + list(row) + [row.sum()]], columns=excel_df_max_price.columns)])

            column_sums_max_price_row = ['Суммы'] + list(column_sum_max_price) + [column_sum_max_price['Суммы']]
            if len(column_sums_max_price_row) == len(excel_df_max_price.columns):
                excel_df_max_price = pd.concat([excel_df_max_price, pd.DataFrame([column_sums_max_price_row], columns=excel_df_max_price.columns)])
            
            
            data_to_export[self.label_texts[idx + 3][:20]] = excel_df_max_price

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                with pd.ExcelWriter(f'{selected_file}/{output_excel_path}', engine='openpyxl') as writer:
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
        first_column_name = data.index.name
        if (self.current_data_index == 4):
            first_column_name = 'Количество ценовых предложений\n поставщиков при обосновании НМЦК и ЦКЕП методом анализа рынка'
        # Устанавливаем количество столбцов в таблице
        num_columns = len(all_purchase_orders) + 2  # Плюс два для "Метод" и "Общий итог"
        self.table.setColumnCount(num_columns)
        
        # Устанавливаем заголовки столбцов
        header_labels = [first_column_name] + list(all_purchase_orders) + ["Общий итог"]
        self.table.setHorizontalHeaderLabels(header_labels)

        # Добавляем строки в таблицу
        for index, row in data.iterrows():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Заполняем ячейки в строке
            self.table.setItem(row_position, 0, QTableWidgetItem(index))  # Метод
            for col_index, purchase_order in enumerate(all_purchase_orders):
                value = row.get(purchase_order, 0)  # Получаем значение из DataFrame, если оно есть, иначе 0
                self.table.setItem(row_position, col_index + 1, QTableWidgetItem(str(value)))
        for row_index, row_sum in enumerate(data['Общий итог']):
            item = QTableWidgetItem(str(row_sum))
            self.table.setItem(row_index, self.table.columnCount() - 1, item)
      
        # Добавляем строку с суммами
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem('Суммы'))
        first_column_name = data.index.name
        # print("First column name:", first_column_name)
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
        # elif 100000 <= row['InitialMaxContractPrice']:
        #     return 'Менее 100 тыс.руб'
        else:
            return 'Менее 100 тыс.руб'
        
    def show_current_data(self):
        # Очистка таблицы перед обновлением
        self.clear_table()
        # self.plot_graph()
        # self.plot_pie()
        # Получение текущих данных
        current_data = self.all_data[self.current_data_index]
        # Отображение данных в таблице
        if self.current_data_index < 3:
            self.populate_table(current_data[0], current_data[1])
        else:
            self.populate_table_2(current_data[0], current_data[1])


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

    def export_to_excel_clicked(self ):

        pivot_tables_purchase1, column_sums_purchase1 = self.winner_analis()
        pivot_tables_purchase2, column_sums_purchase2 = self.count_non_zero_contract_prices()
        pivot_tables_purchase3, column_sums_purchase3 = self.count_non_zero_contract_num()
        pivot_tables_max_price1, column_sums_max_price1 = self.analisMAxPrice()
        pivot_tables_max_price2, column_sums_max_price2 = self.analisNMCKReduce()
        pivot_tables_max_price3, column_sums_max_price3 = self.analisCoeffVar()
        pivot_tables_max_price4, column_sums_max_price4= self.analyze_price_count()
        sort_by_putch_order, min_date, max_date, min_price, max_price, okpd2 = self.all_purchase.return_filters_variabels()
        filters = []

# Проверяем каждый фильтр на пустоту и добавляем непустые значения в список filters
        okpd2 = okpd2.replace(".", "_")
        okpd2 = okpd2.replace(":", "_")
        if sort_by_putch_order:
            filters.append(" " + sort_by_putch_order)
        if okpd2:
            filters.append(str(okpd2))
        if min_date:
            filters.append(" " + str(min_date))  # Преобразуем datetime.date в строку
        if max_date:
            filters.append(str(max_date))
        if min_price:
            filters.append(" " + str(min_price))
        if max_price:
            filters.append(str(max_price))
        
       
        file_name = f"Данные статистики по Фильтрам контракта {' '.join(filters)}.xlsx"
        self.save_to_excel_combined(
        [pivot_tables_purchase1, pivot_tables_purchase2, pivot_tables_purchase3],
        [column_sums_purchase1, column_sums_purchase2, column_sums_purchase3],
        [pivot_tables_max_price1, pivot_tables_max_price2, pivot_tables_max_price3, pivot_tables_max_price4],
        [column_sums_max_price1, column_sums_max_price2, column_sums_max_price3, column_sums_max_price4],
       
        file_name
    )
    def show_specific_data(self, index, button):
    # Проверка, что индекс находится в пределах допустимых значений
        for btn in self.buttons:
            btn.setStyleSheet("text-align: left;")

        # Подсвечиваем только нажатую кнопку
        button.setStyleSheet("text-align: left; background-color: lightGreen;")

        # Обновляем текущую активную кнопку
        self.active_button = button
        if 0 <= index < len(self.label_texts):
            # Устанавливаем текущий индекс
            self.current_data_index = index
            self.show_current_data()
            self.label.setText(self.label_texts[self.current_data_index])
    def highlight_first_button(self):
    # Вызываем метод для подсветки первой кнопки
        if self.buttons:
            first_button = self.buttons[0]
            self.show_specific_data(0, first_button)
# if __name__ == "__main__":
#     from PySide6.QtWidgets import QApplication
#     import sys

#     app = QApplication(sys.argv)
#     window = StatisticWidget()
#     window.show()
#     sys.exit(app.exec())