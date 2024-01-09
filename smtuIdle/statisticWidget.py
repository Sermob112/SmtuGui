from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from peewee import *
import pandas as pd
from models import Purchase, Contract
import json

class StatisticWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Создаем лейбл
        self.label_text = "Статистический анализ методов, использованных для определения НМЦК и ЦКЕП"
        self.label = QLabel(self.label_text)
         # Создаем кнопки "Назад" и "Вперед"
        btn_back = QPushButton("Назад", self)
        btn_forward = QPushButton("Вперед", self)
        self.toExcel = QPushButton("Экспорт в Excel", self)
        # btn_analysis = QPushButton("Анализ", self)

        btn_back.clicked.connect(self.show_previous_data)
        btn_forward.clicked.connect(self.show_next_data)
        self.toExcel.clicked.connect(self.export_to_excel_clicked)

        # Инициализация переменной для отслеживания текущего индекса данных
        self.current_data_index = 0

        # btn_analysis.clicked.connect(self.analisMAxPrice)
        # Создаем таблицу
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Метод", "№223-ФЗ","№44-ФЗ","Общий итог"])
        
        # Устанавливаем политику расширения таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Размещаем виджеты в компоновке
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout(self)
        button_layout2 = QHBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget( self.table)
        button_layout.addWidget(btn_back)
        button_layout.addWidget(btn_forward)
        button_layout2.addWidget(self.toExcel )
        layout.addLayout(button_layout)
        layout.addLayout(button_layout2)
        # layout.addWidget(btn_analysis)

          # Список для хранения всех данных, которые вы хотите отобразить в таблице
        self.all_data = [self.analis(), self.analisMAxPrice(),self.analisCoeffVar()]

        self.label_texts = [
            "Статистический анализ методов, использованных для определения НМЦК и ЦКЕП",
            "Уровень цены контракта, заключенного по результатам конкурса",
            "Диапазон значений коэффициента вариации при определении НМЦК и ЦКЕП",
        ]

        # Первоначальное отображение данных
        self.show_current_data()


        self.setLayout(layout)
        # self.analisPriceCount()
        


    def analisPriceCount(self):
        #Статистический анализ методов, использованных для определения НМЦК и ЦКЕП
        query = Purchase.select(Purchase.PurchaseOrder, Contract.PriceProposal).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
        t = list(query)
        # print(len(t))
        price_proposals_dict = {}
        i = 0
        for purchase in t:  # Используйте t, а не query
            
            # Извлекаем данные из результата запроса
            price_proposal = purchase.contract.PriceProposal

            # Парсим значение PriceProposal (пример, предполагая, что это JSON-строка)
            price_proposal_dict = json.loads(price_proposal)

            # Добавляем данные в общий словарь
            price_proposals_dict[i] = price_proposal_dict
            i = i + 1
        # print(price_proposals_dict)
        # Создаем DataFrame из результатов запроса
       
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.contract.PriceProposal) for purchase in t], columns=['PurchaseOrder', 'PriceProposal'])

         # Парсим столбец PriceProposal
        df['PriceProposal'] = df['PriceProposal'].apply(lambda x: json.loads(x) if x else None)

        # Создаем столбец с количеством не пустых значений в PriceProposal
        df['NonEmptyCount'] = df['PriceProposal'].apply(self.count_non_empty_values)

        # Создаем сводную таблицу
        pivot_table = pd.pivot_table(df, values='NonEmptyCount', index='PurchaseOrder', aggfunc='sum', fill_value=0, margins=True, margins_name='Всего')

    
        # print(pivot_table)
        return pivot_table
    def count_non_empty_values(self, price_proposal):
        return sum(1 for value in price_proposal.values() if value)
      
      
    def analis(self):
        #Статистический анализ методов, использованных для определения НМЦК и ЦКЕП
        purchases = Purchase.select()
        df = pd.DataFrame([(purchase.ProcurementMethod, purchase.PurchaseOrder) for purchase in purchases], columns=['ProcurementMethod', 'PurchaseOrder'])
        pivot_table = df.pivot_table(index='ProcurementMethod', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        total_purchase_counts = column_sums.sum()
        column_sums['Суммы'] = total_purchase_counts

        return pivot_table, column_sums 
      

    def analisMAxPrice(self):
        purchases = Purchase.select(Purchase.PurchaseOrder, Purchase.InitialMaxContractPrice)
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
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.InitialMaxContractPrice) for purchase in purchases],
                        columns=['PurchaseOrder', 'InitialMaxContractPrice'])
        df['PriceRange'] = df.apply(self.determine_price_range, axis=1)
        df['PriceRange'] = pd.Categorical(df['PriceRange'], categories=price_range_order, ordered=True)
        df = df.sort_values('PriceRange')
        pivot_table = df.pivot_table(index='PriceRange', columns='PurchaseOrder', aggfunc='size', fill_value=0)
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
        purchases = Purchase.select(Purchase.PurchaseOrder, Purchase.CoefficientOfVariation)
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
        # Создаем DataFrame
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.CoefficientOfVariation) for purchase in purchases],
                        columns=['PurchaseOrder', 'CoefficientOfVariation'])
        df['CoeffRange'] = df.apply(self.determine_var_range, axis=1)
        df['CoeffRange'] = pd.Categorical(df['CoeffRange'], categories=coeff_range_order, ordered=True)
        df = df.sort_values('CoeffRange')
        pivot_table = df.pivot_table(index='CoeffRange', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
       
        return pivot_table, column_sums2 


    def save_to_excel(self, pivot_table, column_sums, output_excel_path):
        excel_df = pd.DataFrame(columns=['Методы закупок'] + list(pivot_table.columns) + ['Суммы'])

        for method, row in pivot_table.iterrows():
            excel_df = pd.concat([excel_df, pd.DataFrame([[method] + list(row) + [row.sum()]], columns=excel_df.columns)])

        excel_df = pd.concat([excel_df, pd.DataFrame([['Суммы'] + list(column_sums) + [column_sums['Суммы']]], columns=excel_df.columns)])

        data_to_export = {'Методы закупок': excel_df}

        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            for sheet_name, df in data_to_export.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    def save_to_excel_max_price(self, pivot_table, column_sums, output_excel_path):
        excel_df = pd.DataFrame(columns=['Уровень цены контракта'] + list(pivot_table.columns) + ['Суммы'])

        for method, row in pivot_table.iterrows():
            excel_df = pd.concat([excel_df, pd.DataFrame([[method] + list(row) + [row.sum()]], columns=excel_df.columns)])

        # Ensure that the number of columns matches
        column_sums_row = ['Суммы'] + list(column_sums) + [column_sums['Суммы']]
        if len(column_sums_row) == len(excel_df.columns):
            excel_df = pd.concat([excel_df, pd.DataFrame([column_sums_row], columns=excel_df.columns)])

        data_to_export = {'Уровень цены контракта': excel_df}

        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            for sheet_name, df in data_to_export.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    def save_to_excel_combined(self, pivot_table_purchase, column_sums_purchase, pivot_table_max_price, column_sums_max_price, output_excel_path):
        excel_df_purchase = pd.DataFrame(columns=['Методы закупок'] + list(pivot_table_purchase.columns) + ['Суммы'])

        for method, row in pivot_table_purchase.iterrows():
            excel_df_purchase = pd.concat([excel_df_purchase, pd.DataFrame([[method] + list(row) + [row.sum()]], columns=excel_df_purchase.columns)])

        excel_df_purchase = pd.concat([excel_df_purchase, pd.DataFrame([['Суммы'] + list(column_sums_purchase) + [column_sums_purchase['Суммы']]], columns=excel_df_purchase.columns)])

        excel_df_max_price = pd.DataFrame(columns=['Уровень цены контракта'] + list(pivot_table_max_price.columns) + ['Суммы'])

        for method, row in pivot_table_max_price.iterrows():
            excel_df_max_price = pd.concat([excel_df_max_price, pd.DataFrame([[method] + list(row) + [row.sum()]], columns=excel_df_max_price.columns)])

        column_sums_max_price_row = ['Суммы'] + list(column_sums_max_price) + [column_sums_max_price['Суммы']]
        if len(column_sums_max_price_row) == len(excel_df_max_price.columns):
            excel_df_max_price = pd.concat([excel_df_max_price, pd.DataFrame([column_sums_max_price_row], columns=excel_df_max_price.columns)])

        data_to_export = {'Методы закупок': excel_df_purchase, 'Уровень цены контракта': excel_df_max_price}

        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            for sheet_name, df in data_to_export.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    def clear_table(self):
        # Очищаем все строки в таблице
        self.table.setRowCount(0)

    def populate_table(self, data, sums):
        # Очищаем таблицу перед обновлением
        self.clear_table()
       
        # Добавляем строки в таблицу
        for index, row in data.iterrows():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # Заполняем ячейки в строке
            self.table.setItem(row_position, 0, QTableWidgetItem(index))
            for col_index, value in enumerate(row):
                self.table.setItem(row_position, col_index + 1, QTableWidgetItem(str(value)))

        # Добавляем строку с суммами
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem('Суммы'))

        # Добавляем суммы значений из столбцов '223-ФЗ' и '44-ФЗ'
        for col_index in range(1, self.table.columnCount() - 1):
            column_name = self.table.horizontalHeaderItem(col_index).text()
            sum_value = sums.get(column_name, 0)
            self.table.setItem(row_position, col_index, QTableWidgetItem(str(sum_value)))

        # Добавляем сумму значений '223-ФЗ' и '44-ФЗ' в последний столбец 'Общий итог'
        last_col_index = self.table.columnCount() - 1
        sum_value_total = sums.get('№223-ФЗ', 0) + sums.get('№44-ФЗ', 0)
        self.table.setItem(row_position, last_col_index, QTableWidgetItem(str(sum_value_total)))

        
    def determine_var_range(self,row):
        if row['CoefficientOfVariation'] * 100 == 0:
            return 'Значение коэффициента вариации 0%'
        elif 0 <= row['CoefficientOfVariation'] * 100 <= 1:
            return 'значение коэффициента вариации 0-1%'
        elif 1 <= row['CoefficientOfVariation'] * 100 <= 2:
            return 'значение коэффициента вариации 1-2%'
        elif 2 <= row['CoefficientOfVariation'] * 100<= 5:
            return 'значение коэффициента вариации 2-5%'
        elif 5 <= row['CoefficientOfVariation'] * 100<= 10:
            return 'значение коэффициента вариации 5-10%'
        elif 10 <= row['CoefficientOfVariation']* 100 <= 20:
            return 'значение коэффициента вариации 10-20%'
        elif 20 <= row['CoefficientOfVariation']* 100 <= 33:
            return 'значение коэффициента вариации 10-20%'
        else:
            return 'более 33%'
        
    def determine_price_range(self,row):
        if row['InitialMaxContractPrice'] > 100000000:
            return 'Цена контракта более 100 000 000 тыс.руб.'
        elif 5000000 <= row['InitialMaxContractPrice'] <= 10000000:
            return 'Цена контракта 5 000 000 - 10 000 000 тыс.руб.'
        elif 1000000 <= row['InitialMaxContractPrice'] <= 5000000:
            return 'Цена контракта 1 000 000 - 5 000 000 тыс.руб.'
        elif 500000 <= row['InitialMaxContractPrice'] <= 1000000:
            return 'Цена контракта 500 000-  1 000 000 тыс.руб.'
        elif 200000 <= row['InitialMaxContractPrice'] <= 500000:
            return 'Цена контракта 200 000 - 500 000 тыс.руб.'
        elif 100000 <= row['InitialMaxContractPrice'] <= 200000:
            return 'Цена контракта 100 000 - 200 000 тыс.руб.'
        else:
            return 'Менее 100 тыс.руб'
        
    def show_current_data(self):
        # Очистка таблицы перед обновлением
        self.clear_table()

        # Получение текущих данных
        current_data = self.all_data[self.current_data_index]

        # Отображение данных в таблице
        self.populate_table(current_data[0], current_data[1])

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
        pivot_table_purchase, column_sums_purchase = self.analis()
        pivot_table_max_price, column_sums_max_price = self.analisMAxPrice()
        self.save_to_excel_combined(pivot_table_purchase, column_sums_purchase, pivot_table_max_price, column_sums_max_price, 'путь_к_вашему_файлу_комбинированный.xlsx')

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = StatisticWidget()
    window.show()
    sys.exit(app.exec())