import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton,QHeaderView, QFileDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy
from PySide6.QtCore import Qt

from parserV3 import *

class CsvLoaderWidget(QWidget):
    def __init__(self):
        super(CsvLoaderWidget, self).__init__()

        # Добавляем счетчик новых записей как атрибут класса
        self.inserted_rows_count = 0
        self.repeat_count = 0
        self.all_count = count_total_records()
      
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Создаем кнопку
        btn_load_csv = QPushButton('Загрузить CSV файл', self)
        btn_load_csv.clicked.connect(self.show_file_dialog)

        # Добавляем кнопку на виджет
        layout.addWidget(btn_load_csv)

        # Добавляем надпись
        lbl_info = QLabel('Информация о дублировании или загрузке новых закупок', self)
        layout.addWidget(lbl_info)

        # Добавляем таблицу
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Описание', 'Значение'])
        self.populate_table(self.table)
        self.update_table()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table)
        # Устанавливаем политику размеров для таблицы
  

        # Устанавливаем макет на виджет
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def show_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            # Вставляем данные в базу данных
            self.inserted_rows_count, insert_errors = insert_in_table(selected_file)
            result, self.repeat_count = find_records_with_differences()
            # self.all_count = count_total_records()
            # Если вставка прошла успешно, обновляем таблицу
            if not insert_errors:
                self.update_table()
                print(f"Успешно вставлено новых записей: {self.inserted_rows_count}")
                print(f"повторы: {self.repeat_count}")
                print(f"повторы: { self.all_count}")
    def populate_table(self, table):
        # Добавляем данные в таблицу
        data = [
            ('В БД НМЦК и ЦК добавлено Закупок:', str(self.inserted_rows_count)),
            ('В БД НМЦК и ЦК всего размещено Закупок:', str(self.all_count))
          
        ]

        table.setRowCount(len(data))

        for row, (desc, value) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(desc))
            table.setItem(row, 1, QTableWidgetItem(value))

    def update_table(self):
        # Обновляем таблицу после изменения счетчика новых записей
        self.populate_table(self.table)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = CsvLoaderWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())