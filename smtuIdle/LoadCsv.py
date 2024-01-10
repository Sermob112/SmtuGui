import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from DBtest import PurchasesWidget
from statisticWidget import StatisticWidget
from parserV3 import *

class CsvLoaderWidget(QWidget):
    def __init__(self):
        super(CsvLoaderWidget, self).__init__()

        # Добавляем счетчик новых записей как атрибут класса
        self.inserted_rows_count = 0
        self.repeat_count = 0
        self.all_count = count_total_records()
        self.selected_ids = []
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Set vertical header to resize to contents
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Optional: Hide the vertical scrollbar
        layout.addWidget(self.table)

        # Добавляем лейбл под таблицей
        lbl_table_info = QLabel('Дополнительная информация под таблицей', self)
        layout.addWidget(lbl_table_info)
       
        # Вторая таблица
        self.second_table = QTableWidget(self)
        self.second_table.setColumnCount(8)
        self.second_table.setHorizontalHeaderLabels(['Id', 'Реестровый номер', 'Дата аукциона', 'Дата начала заявки', 'Дата окончания заявки', 'Дата обновления', 'Дата размещения', 'Номер лота'])
        self.second_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.second_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.second_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.second_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.second_table)
        # Добавляем кнопку "Удалить выбранные записи"
        btn_delete_selected = QPushButton('Удалить выбранные записи', self)
        btn_delete_selected.clicked.connect(self.delete_selected_records)
        layout.addWidget(btn_delete_selected)

        # Добавляем обработчик события для клика по ячейке
        self.second_table.cellClicked.connect(self.handle_table_click)

        # Устанавливаем макет на виджет
        self.update_table()
        self.update_second_table()
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def show_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.inserted_rows_count, insert_errors = insert_in_table(selected_file)
            
            if not insert_errors:
  
                self.update_table()
                
             
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
    def update_second_table(self):
        self.result, self.repeat_count = find_records_with_differences()
        # Проверяем, что у нас есть данные для обновления таблицы
        if hasattr(self, 'result') and self.result:
            # Очищаем таблицу перед обновлением
            self.second_table.setRowCount(0)
            
            # Перебираем данные и добавляем их в таблицу
            for row, record in enumerate(self.result):
                self.second_table.insertRow(row)
                for col, value in enumerate(record):
                    item = QTableWidgetItem(str(value))
                    self.second_table.setItem(row, col, item)

    def update_table(self):
        # Обновляем таблицу после изменения счетчика новых записей
        self.populate_table(self.table)
        self.update_second_table()
    def handle_table_click(self, row, col):
        # Получаем значение из колонки 'Id'
        id_item = self.second_table.item(row, 0)  # Предполагаем, что 'Id' находится в первой колонке
        if id_item:
            selected_id = id_item.text()
            print(f'Selected Id: {selected_id}')

            if selected_id in self.selected_ids:
                # Если Id уже выбран, удаляем его из списка и сбрасываем цвет ячеек
                self.selected_ids.remove(selected_id)
                for i in range(self.second_table.columnCount()):
                    item = self.second_table.item(row, i)
                    if item:
                        item.setBackground(Qt.white)
            else:
                # Иначе, добавляем Id в список и выделяем строку
                self.selected_ids.append(selected_id)
                for i in range(self.second_table.columnCount()):
                    item = self.second_table.item(row, i)
                    if item:
                        item.setBackground(Qt.red)
    def delete_selected_records(self):
        reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.selected_ids:
                success = delete_records_by_id(self.selected_ids)
                if success:
                    print("Успешно удалены записи с Id:", self.selected_ids)
                    self.second_table.clearContents()
                    # self.second_table.setRowCount(0)
                    self.selected_ids = []
                    self.update_second_table()
                else:
                    print("Ошибка при удалении записей")
        else:
            self.update_second_table()
            # В противном случае, ничего не делаем
            pass
        

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = CsvLoaderWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())