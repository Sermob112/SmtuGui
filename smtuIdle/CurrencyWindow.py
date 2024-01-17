from PySide6.QtWidgets import QApplication,QFileDialog, QMessageBox, QCompleter,QMainWindow,QLabel,QLineEdit,QComboBox, QTableWidget,QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget,QPushButton,QHeaderView
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import QColor
import sys, json
from peewee import JOIN
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.
# Создаем соединение с базой данных
db = SqliteDatabase('test.db')
cursor = db.cursor()
class CurrencyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Окно ввода даных валюты")
        self.setGeometry(100, 100, 600, 400)
        self.selected_text = None
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Номер","Идентификатор", "Текущая валюта"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.cellClicked.connect(self.handle_table_click)
        self.populate_table()
           # Размещаем таблицу в вертикальном layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def populate_table(self):
        self.table.setRowCount(0)
        purchases = Purchase.select().where((Purchase.Currency != 'RUB') & (Purchase.Currency.is_null(False)) &(Purchase.Currency != 'Нет данных') )
        for purchase in purchases:
            currency_value = purchase.Currency or "Нет данных"
            registry_number = purchase.RegistryNumber or "Нет данных"
            purch_id = str(purchase.Id) or "Нет данных"
            self.add_row_to_table(purch_id,registry_number, currency_value)
        
    
    def add_row_to_table(self, purch_id, label_text, value_text):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        Id_item = QTableWidgetItem(purch_id)
        label_item = QTableWidgetItem(label_text)
        value_item = QTableWidgetItem(value_text)

        self.table.setItem(row_position, 0, Id_item)
        self.table.setItem(row_position, 1, label_item)
        self.table.setItem(row_position, 2, value_item)

    def handle_table_click(self,row):
        id_item = self.table.item(row, 0)  # Предполагаем, что 'Id' находится в первой колонке
        if id_item:
             # Подсветим выделенную строку в синий цвет
            for i in range(self.table.columnCount()):
                    item = self.table.item(row, i)
                    if item:
                        item.setBackground(Qt.blue) 
            selected_id = id_item.text()
            print(f'Selected Id: {selected_id}')
            self.currency_shower = InsertWidgetCurrency(selected_id)
            self.currency_shower.show()
            self.currency_shower.closed_signal.connect(self.handle_currency_shower_closed)
    def handle_currency_shower_closed(self):
        # Получите индекс текущей выбранной строки в таблице
        self.populate_table()

  

if __name__ == "__main__":
    app = QApplication([])
    widget = CurrencyWidget()
    widget.show()
    app.exec()