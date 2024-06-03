from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination,CurrencyRate
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import QColor,QIcon,QFont,QBrush
from PySide6.QtCore import QDate
import sys, json
from peewee import JOIN
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel,export_to_excel_contract
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from peewee import fn
from locale import currency,format_string
import locale
from functools import partial
from AllDbScroller import PurchasesWidgetAll
from statisticWidget import StatisticWidget  

import pandas as pd
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(Canvas, self).__init__(fig)
        self.setParent(parent)

    def plot(self, data, x_column, y_column):
        try:
            self.axes.clear()
            # Построение графика
            data.plot(kind='bar', x=x_column, y=y_column, ax=self.axes)
            self.draw()
        except Exception as e:
            print("Error plotting graph:", e)

        
    def plot_pie(self, data, x_column, y_column):
        self.axes.clear()
        self.axes.pie(data[y_column], labels=data[x_column], autopct='%1.1f%%', startangle=90)
        self.draw()





class ResultWindow(QWidget):
    def __init__(self,main, role):
        super().__init__()
        # self.main_win = main_window
        self.selected_text = None
        self.selected_text_contract = None
        self.main_window = main
        self.role = role
        
         # Создаем компонент вкладок
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_purch_tab(), 'Результаты')
        tab_widget.addTab(self.create_cont_tab(), 'График')
        layout = QVBoxLayout(self)
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.formular_texts = [
            "Методы, использованных для определения НМЦК и ЦКЕП",
            "Формулировки, применяемых государственными\n заказчиками, при объявлении закупки",
            "Классификации ОКПД2",           
            "Количество заявок на участие в закупке",
            "Количество допущенных заявок\n на участие в закупке",
            "Количество отклоненных заявок\n на участие в закупке",
            "Соотношения НМЦК и ЦКЕП и цены\n контракта, заключенного по результатам конкурса",
            "Количество ценовых предложений\n поставщиков при обосновании НМЦК и ЦКЕП методом анализа рынка",
            "Уровень цены контракта, заключенного\n по результатам конкурса",
            "Диапазон значений коэффициента\n вариации при определении НМЦК и ЦКЕП"
        ]
    def create_purch_tab(self):
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

        



        data = self.reload_data()
        data_cont = self.reload_data_cont()
        self.show_all_contracts()
        label = QLabel(f"Всего записей: {len(data)}" , self)
        label2 = QLabel(f"Всего заключенных контрактов: {len(data_cont)}", self)
        
        lable_layout = QHBoxLayout()
        lable_layout.addWidget(label)
        lable_layout.addWidget(label2)
        layout.addLayout(lable_layout)
        layout.addWidget(self.table_cont)
        self.tets()
        return tab
    def create_cont_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.current_data_index = 0
        self.label_texts = [
            "График количества заключенных контрактов",
            "Анализ по соотношению коэффициенту вариации",
            "Количество заявок на участие в закупке",
            "Количество допущенных заявок\n на участие в закупке",
            "Количество отклоненных заявок\n на участие в закупке",
            "Итог",
        ]
  
        self.all_data = [self.winner_analis(),self.analisCoeffVar(),self.analisQueryCount(), 
                         self.analisQueryCountAccept(),self.analisQueryCountDecline(),self.final_analis()]
        self.buttons = []
        self.FirstStage = QPushButton("Анализ НМЦК")
        self.FirstStage.setIcon(QIcon("Pics/right-arrow.png"))
        self.FirstStage.setMaximumWidth(200)
        self.FirstStage.setStyleSheet("text-align: left; padding-left: 10px;font-size: 11pt;")
        self.FirstStage.clicked.connect(self.toggle_stage_1)
         # колапсирующее окно Первый этап
        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        self.Qword = QLabel("Анализ методов и формулировок в государственных закупках")
        menu_layout.addWidget(self.Qword)
        for index, text in enumerate(self.label_texts):
           
            button = QtWidgets.QPushButton()
            button.setText(text) 
            button.setFixedSize(200,50)
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
        self.buttons_layout = QVBoxLayout()
        self.buttons_layout.addWidget(self.FirstStage)
        self.buttons_layout.addWidget(self.menu_frame)
        layout.addLayout(self.buttons_layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.gist(), 'Гистограмма')
        self.tab_widget.addTab(self.pie(), 'Круговая диаграмма')
        layout.addWidget(self.tab_widget)
        return tab
    

    def reload_data(self):
            self.purchases = Purchase.select()
            self.purchases_list = list(self.purchases)
            self.update()
            return self.purchases_list
           

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
        Purchase.PurchaseOrder,
        Purchase.CoefficientOfVariation,
#25-->
        Purchase.QueryCount,
        Purchase.ResponseCount,
        Purchase.CoefficientOfVariation,
        Contract.TotalApplications,
        Contract.RejectedApplications,
        Contract.AdmittedApplications,
    )
    .join(Purchase, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)))
    # .where(Contract.ContractNumber != "Нет данных"))
        self.update()
        self.contracts_list = list(self.contracts.tuples())
        return  self.contracts_list
    

    def reload_data_cont_2(self):
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
        Purchase.PurchaseOrder,
        Purchase.CoefficientOfVariation,
    )
    .join(Purchase, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)))
    # .where(Contract.ContractNumber != "Нет данных"))
        self.update()
        self.contracts_list = list(self.contracts.tuples())
        return  self.contracts
    
    def show_all_contracts(self):
    # Очищаем таблицу перед добавлением новых данных
        self.reject = 0
        self.good = 0
        self.violations = 0
        self.table_cont.setRowCount(0)
      
        if len(self.contracts_list) != 0:
            for current_position, current_purchase in enumerate(self.contracts_list):
                # Добавляем новую строку для каждой записи
                self.table_cont.insertRow(current_position)
                total = format_string("%.0f", current_purchase[22], grouping=True) + ' ₽'
                difference = format_string("%.0f", current_purchase[22] - current_purchase[5], grouping=True) + ' ₽'
                advance_payment = format_string("%.0f", current_purchase[5], grouping=True) + ' ₽'

                
                # Добавляем данные в каждую ячейку для текущей записи
                for col, value in enumerate([current_purchase[0], current_purchase[1], current_purchase[2],
                                  str(current_purchase[3]), current_purchase[4],
                                   advance_payment,
                                  total,
                                  difference
                                  ,
                                  str(current_purchase[6]), current_purchase[7],
                                  current_purchase[8]
                                  ]):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                    self.table_cont.setItem(current_position, col, item)
                    self.table_cont.setRowHeight(current_position, self.table_cont.rowHeight(current_position) + 3)

                    condition1 = current_purchase[25] == 0
                    condition2 = current_purchase[26] == 0
                    condition3 = current_purchase[27] * 100 > 20
                if condition1 or condition2:
                    self.reject = self.reject + 1
                    for col in range(self.table_cont.columnCount()):
                        item = self.table_cont.item(current_position, col)
                        if item:
                            item.setBackground(QBrush(QColor(255, 0, 0)))  # Цвет красного фона

                elif sum([condition1, condition2, condition3]) >= 1:
                    self.violations = self.violations + 1
                    for col in range(self.table_cont.columnCount()):
                        item = self.table_cont.item(current_position, col)
                        if item:
                            item.setBackground(QBrush(QColor(255, 165, 0)))  # Цвет оранжевого фона
                elif current_purchase[3] != "Нет данных":
                    self.good = self.good + 1
                    for col in range(self.table_cont.columnCount()):
                        item = self.table_cont.item(current_position, col)
                        if item:
                            item.setBackground(QBrush(QColor(144, 238, 144)))  # Цвет зеленого фона


    def toggle_stage_1(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.FirstStage.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.FirstStage.setIcon(QIcon("Pics/right-arrow.png"))

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
            # self.label.setText(self.label_texts[self.current_data_index])
    
    def show_current_data(self):
        # Очистка таблицы перед обновлением
      
        self.plot_graph()
        self.plot_pie()
        # Получение текущих данных
    def tets (self):
        print(self.violations)
        print(self.good)
        print(self.reject)
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
        self.canvas_pie.plot_pie(current_data[0],x,y)

    def winner_analis(self):
   
        #Статистический анализ методов, использованных для определения НМЦК и ЦКЕП
        contracts = self.reload_data_cont_2()
    
        df = pd.DataFrame([(contract.WinnerExecutor, contract.Id) for contract in contracts], columns=['WinnerExecutor', 'Count'])
        
        # Создаем сводную таблицу по победителям
        pivot_table = df.pivot_table(index='WinnerExecutor', aggfunc='size', fill_value=0).reset_index()
      
        pivot_table.columns = ['Победитель-исполнитель контракта', 'Единицы']

        column_sums = pivot_table['Единицы'].sum()
        column_sums = pd.DataFrame({'Единицы': [column_sums]})
        column_sums.index = ['Итого']
   
        return pivot_table,column_sums
    def final_analis(self):
        # Создаем DataFrame с данными reject, good и violations
        data = {
            'Category': ['Reject', 'Good', 'Violations'],
            'Count': [self.reject, self.good, self.violations]
        }
        
        df = pd.DataFrame(data)
        
        # Суммируем данные по категориям
        total_counts = df['Count'].sum()
        total_row = pd.DataFrame({'Category': ['Total'], 'Count': [total_counts]})
        
        return df, total_row
    def analisCoeffVar(self):
        purchases = self.reload_data_cont_2()
        coeff_range_order = [
        'Значение коэффициента вариации 0%',
        'значение коэффициента вариации 0-1%',
        'значение коэффициента вариации 1-2%',
        'значение коэффициента вариации 2-5%',
        'значение коэффициента вариации 5-10%',
        'значение коэффициента вариации 10-20%',
        'значение коэффициента вариации 20-33%',
        'более 33%'
    ]
        self.formular_texts = "Диапазон значений коэффициента\n вариации при определении НМЦК и ЦКЕП"
        # Создаем DataFrame
        df = pd.DataFrame([(purchase.purchase.PurchaseOrder, purchase.purchase.CoefficientOfVariation) for purchase in purchases],
                       columns=['PurchaseOrder', f'{self.formular_texts}'])
        df[f'{self.formular_texts}'] = df.apply(self.determine_var_range, axis=1)
        df[f'{self.formular_texts}'] = pd.Categorical(df[f'{self.formular_texts}'], categories=coeff_range_order, ordered=True)
        df = df.sort_values(f'{self.formular_texts}')
        pivot_table = df.pivot_table(index=f'{self.formular_texts}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
        return pivot_table, column_sums2
    
    def count_non_empty_values(self, dictionary):
        count = 0
        for key, value in dictionary.items():
            if value != "Нет данных" :
                count += 1
        return count
    
    def determine_var_range(self,row):
        term =  row[f'{self.formular_texts}'] 
        try:
            if term * 100 == 0:
                return 'Значение коэффициента вариации 0%'
            elif 0 <= term * 100 <= 1:
                return 'значение коэффициента вариации 0-1%'
            elif 1 <= term * 100 <= 2:
                return 'значение коэффициента вариации 1-2%'
            elif 2 <= term * 100<= 5:
                return 'значение коэффициента вариации 2-5%'
            elif 5 <= term * 100<= 10:
                return 'значение коэффициента вариации 5-10%'
            elif 10 <= term* 100 <= 20:
                return 'значение коэффициента вариации 10-20%'
            elif 20 <= term* 100 <= 33:
                return 'значение коэффициента вариации 10-20%'
            else:
                return 'более 33%'
        except:
            pass

    def analisQueryCount(self):
        query = Purchase.select(Purchase.PurchaseOrder, Contract.TotalApplications).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)).where(Contract.TotalApplications.is_null(False)  & (Contract.ContractNumber != "Нет данных"))
        t = list(query)
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.contract.TotalApplications) for purchase in t],
                           columns=['PurchaseOrder', f'{self.formular_texts[3]}'])
        pivot_table = df.pivot_table(index=f'{self.formular_texts[3]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        total_purchase_counts = column_sums.sum()
        column_sums['Суммы'] = total_purchase_counts
        # print(pivot_table)
        return pivot_table, column_sums

    def analisQueryCountAccept(self):
        query = Purchase.select(Purchase.PurchaseOrder, Contract.AdmittedApplications).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)).where(Contract.AdmittedApplications.is_null(False)& (Contract.ContractNumber != "Нет данных"))
        t = list(query)
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.contract.AdmittedApplications) for purchase in t],
                           columns=['PurchaseOrder', f'{self.formular_texts[4]}'])
        pivot_table = df.pivot_table(index=f'{self.formular_texts[4]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        total_purchase_counts = column_sums.sum()
        column_sums['Суммы'] = total_purchase_counts
        # print(pivot_table)
        return pivot_table, column_sums

    def analisQueryCountDecline(self):
        query = Purchase.select(Purchase.PurchaseOrder, Contract.RejectedApplications).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)).where(Contract.RejectedApplications.is_null(False) & (Contract.ContractNumber != "Нет данных"))
        t = list(query)
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.contract.RejectedApplications) for purchase in t], 
                          columns=['PurchaseOrder', f'{self.formular_texts[5]}'])
        pivot_table = df.pivot_table(index=f'{self.formular_texts[5]}', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        total_purchase_counts = column_sums.sum()
        column_sums['Суммы'] = total_purchase_counts
        # print(pivot_table)
        return pivot_table, column_sums

if __name__ == '__main__':
    app = QApplication(sys.argv)
    csv_loader_widget = ResultWindow(None, "kek")
    csv_loader_widget.show()
    sys.exit(app.exec())


