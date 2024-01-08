from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from peewee import *
import pandas as pd
from parserV3 import *
import sys

class StatisticWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
    # Создаем кнопку
        btn_load_csv = QPushButton('Загрузить CSV файл', self)
        btn_load_csv.clicked.connect(self.show_file_dialog)

        # Добавляем кнопку на виджет
        layout.addWidget(btn_load_csv)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def show_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            insert_in_table_full(selected_file)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    csv_loader_widget = StatisticWidget()
    csv_loader_widget.show()
    sys.exit(app.exec_())