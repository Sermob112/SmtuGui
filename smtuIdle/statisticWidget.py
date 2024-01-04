from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from peewee import *
import pandas as pd
from models import Purchase

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
        # btn_analysis = QPushButton("Анализ", self)

        btn_back.clicked.connect(self.show_previous_data)
        btn_forward.clicked.connect(self.show_next_data)

        # Инициализация переменной для отслеживания текущего индекса данных
        self.current_data_index = 0

        # btn_analysis.clicked.connect(self.analisMAxPrice)
        # Создаем таблицу
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Метод", "223-ФЗ","44-ФЗ","Общий итог"])
        
        # Устанавливаем политику расширения таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Размещаем виджеты в компоновке
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget( self.table)
        layout.addWidget(btn_back)
        layout.addWidget(btn_forward)
        # layout.addWidget(btn_analysis)

          # Список для хранения всех данных, которые вы хотите отобразить в таблице
        self.all_data = [self.analis(), self.analisMAxPrice()]

        self.label_texts = [
            "Статистический анализ методов, использованных для определения НМЦК и ЦКЕП",
            "Уровень цены контракта, заключенного по результатам конкурса"
        ]

        # Первоначальное отображение данных
        self.show_current_data()


        self.setLayout(layout)

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
        # print(total_purchase_counts)

        return pivot_table, column_sums 
        # Заполняем таблицу данными
        # self.populate_table(pivot_table, column_sums)

        # Уровень цены контракта, заключенного по результатам конкурса


    def analisMAxPrice(self):
        purchases = Purchase.select(Purchase.PurchaseOrder, Purchase.InitialMaxContractPrice)

        # Создаем DataFrame
        df = pd.DataFrame([(purchase.PurchaseOrder, purchase.InitialMaxContractPrice) for purchase in purchases],
                        columns=['PurchaseOrder', 'InitialMaxContractPrice'])
        df['PriceRange'] = df.apply(self.determine_price_range, axis=1)
        pivot_table = df.pivot_table(index='PriceRange', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()
        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        column_sums2 = pivot_table.sum()
        column_means2 = pivot_table.mean()
        total_purchase_counts2 = column_sums2.sum()
        column_sums2['Суммы'] = total_purchase_counts2
        return pivot_table, column_sums2 
        # self.populate_table(pivot_table, column_sums2)




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
        sum_value_total = sums.get('223-ФЗ', 0) + sums.get('44-ФЗ', 0)
        self.table.setItem(row_position, last_col_index, QTableWidgetItem(str(sum_value_total)))

        
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

# if __name__ == "__main__":
#     from PySide6.QtWidgets import QApplication
#     import sys

#     app = QApplication(sys.argv)
#     window = StatisticWidget()
#     window.show()
#     sys.exit(app.exec())