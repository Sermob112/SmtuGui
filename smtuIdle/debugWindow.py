from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from models import Contract
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
            if  Contract.delete().execute() & Purchase.delete().execute():
                QMessageBox.information(self, "Успех", "Вы успешно удалили данные!")
            else:
                QMessageBox.information(self,"Ошибка", "Ошибка при удалении данных")
        pass
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = DebugWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())