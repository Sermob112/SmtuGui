from PySide6.QtWidgets import QApplication,QFileDialog, QMessageBox, QCompleter,QMainWindow,QLabel,QLineEdit,QComboBox, QTableWidget,QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget,QPushButton,QHeaderView
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import ChangedDate
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
class ChangeLogWindow(QWidget):
    def __init__(self, role):
        super().__init__()
        self.setWindowTitle("Окно ввода даных валюты")
        self.setGeometry(100, 100, 600, 400)
        self.selected_text = None
        self.role = role
        # Создаем таблицу для отображения данных
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Идентификатор", "Операция","Реестровый номер закупки", "Пользователь", "Дата изменения", "Наименование закупки", "Роль"])
    
        self.table.horizontalHeader().setStretchLastSection(True) # Растягиваем вторую колонку на оставшееся пространство
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        for i in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.setWordWrap(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
       
        self.populate_table()

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        self.setLayout(layout)
        # if self.role != "Гость":
        #     self.table.cellClicked.connect(self.handle_table_click)
 
    def populate_table(self):
        self.table.setRowCount(0)
        changes = ChangedDate.select()
        
        if not changes:
            # Если таблица пуста, добавляем надпись
            self.table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(0x0004 | 0x0080)  # Выравнивание по центру
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 6)
        else:
            for change in changes:
                id_value = change.id or "Нет данных"
                registry_number_value = change.RegistryNumber or "Нет данных"
                username_value = change.username or "Нет данных"
                changed_time_value = change.chenged_time.strftime('%Y-%m-%d %H:%M:%S') if change.chenged_time else "Нет данных"
                purchase_name_value = change.PurchaseName or "Нет данных"
                role_value = change.Role or "Нет данных"
                type = change.Type or "Нет данных"
                self.add_row_to_table(id_value, registry_number_value, username_value, changed_time_value, purchase_name_value, role_value,type)

    def add_row_to_table(self, id_value, registry_number_value, username_value, changed_time_value, purchase_name_value, role_value,type):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(str(id_value)))
        self.table.setItem(row_position, 1, QTableWidgetItem(type))
        self.table.setItem(row_position, 2, QTableWidgetItem(registry_number_value))
        self.table.setItem(row_position, 3, QTableWidgetItem(username_value))
        self.table.setItem(row_position, 4, QTableWidgetItem(changed_time_value))
        self.table.setItem(row_position, 5, QTableWidgetItem(purchase_name_value))
        self.table.setItem(row_position, 6, QTableWidgetItem(role_value))

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
            self.currency_shower = InsertWidgetCurrency(self,selected_id)
            self.currency_shower.show()
            self.currency_shower.closed_signal.connect(self.handle_currency_shower_closed)
    def handle_currency_shower_closed(self):
        # Получите индекс текущей выбранной строки в таблице
        self.populate_table()

  

if __name__ == "__main__":
    app = QApplication([])
    widget = ChangeLogWindow()
    widget.show()
    app.exec()