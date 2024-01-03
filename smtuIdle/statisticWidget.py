from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from peewee import *
import pandas as pd
from models import Purchase

class PurchasesWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Создаем лейбл
        label_text = "Статистический анализ методов, использованных для определения НМЦК и ЦКЕП"
        label = QLabel(label_text)
         # Создаем кнопки "Назад" и "Вперед"
        btn_back = QPushButton("Назад", self)
        btn_forward = QPushButton("Вперед", self)
        btn_analysis = QPushButton("Анализ", self)
        btn_analysis.clicked.connect(self.analis)
        # Создаем таблицу
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Метод", "223-ФЗ","44-ФЗ","Общий итог"])
        
        # Устанавливаем политику расширения таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Размещаем виджеты в компоновке
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget( self.table)
        layout.addWidget(btn_back)
        layout.addWidget(btn_forward)
        layout.addWidget(btn_analysis)


        self.setLayout(layout)

    def analis(self):
        purchases = Purchase.select()
        df = pd.DataFrame([(purchase.ProcurementMethod, purchase.PurchaseOrder) for purchase in purchases], columns=['ProcurementMethod', 'PurchaseOrder'])
        pivot_table = df.pivot_table(index='ProcurementMethod', columns='PurchaseOrder', aggfunc='size', fill_value=0)
        column_sums = pivot_table.sum()

        row_totals = pivot_table.sum(axis=1)
        pivot_table['Общий итог'] = row_totals
        total_purchase_counts = column_sums.sum()
        column_sums['Суммы'] = total_purchase_counts
        print(pivot_table['Общий итог'])

        # Очищаем таблицу перед обновлением
    #     self.clear_table()

    #     # Заполняем таблицу данными
        self.populate_table(pivot_table, column_sums, row_totals)

    def clear_table(self):
        # Очищаем все строки в таблице
        self.table.setRowCount(0)

    def populate_table(self, data, sums, row_totals):
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

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = PurchasesWidget()
    window.show()
    sys.exit(app.exec())