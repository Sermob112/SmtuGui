from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from models import *
from peewee import *
import pandas as pd
from parserV3 import *
import sys

class DebugWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        lbl_debug = QLabel('Отладка', self)
        layout.addWidget(lbl_debug)
        # Добавляем таблицу
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)  # Количество столбцов
        self.table_widget.setHorizontalHeaderLabels(['Имя пользователя', 'Вход', 'Выход'])  # Заголовки столбцов
        layout.addWidget(self.table_widget)
        self.load_logs()
    # Создаем кнопку
        btn_load_csv = QPushButton('Загрузить CSV файл', self)
        btn_load_csv.clicked.connect(self.show_file_dialog)
        layout.addWidget(btn_load_csv)

        btn_delete_data = QPushButton('Удалить все данные', self)
        btn_delete_data.clicked.connect(self.delete_all_data)
        layout.addWidget(btn_delete_data)
        # Добавляем кнопку на виджет
        

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def show_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            insert_in_table_full(selected_file)
    def delete_all_data(self):
        reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if  Contract.delete().execute() & Purchase.delete().execute() & CurrencyRate.delete().execute() & FinalDetermination.delete().execute(): 
                QMessageBox.information(self, "Успех", "Вы успешно удалили данные!")
            else:
                QMessageBox.information(self,"Ошибка", "Ошибка при удалении данных")
        pass
    
    def load_logs(self):
        logs = UserLog.select()
        self.table_widget.setRowCount(len(logs))

        for idx, log in enumerate(logs):
            username_item = QTableWidgetItem(log.username)
            login_time_item = QTableWidgetItem(str(log.login_time))
            logout_time_item = QTableWidgetItem(str(log.logout_time) if log.logout_time else 'Still logged in')

            self.table_widget.setItem(idx, 0, username_item)
            self.table_widget.setItem(idx, 1, login_time_item)
            self.table_widget.setItem(idx, 2, logout_time_item)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = DebugWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())