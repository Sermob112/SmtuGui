import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from DBtest import PurchasesWidget
from statisticWidget import StatisticWidget
from parserV3 import *
from PySide6.QtWidgets import QStyleFactory
from CurrencyWindow import CurrencyWidget
class CsvLoaderWidget(QWidget):
    def __init__(self, main_window, curr_win , purchaseViewerallparent, parent=None):
        super(CsvLoaderWidget, self).__init__(parent)
        self.main_window = main_window
        self.curr_wind = curr_win
        self.purchaseViewerall = purchaseViewerallparent
        # Добавляем счетчик новых записей как атрибут класса
        self.inserted_rows_count = 0
        self.repeat_count = 0
        self.all_count = count_total_records()
        self.selected_ids = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.addStretch()

     

        # Создаем кнопку
        btn_load_csv = QPushButton('Загрузить*.CSV файл, полученный из ЕИС zakupki.gov.ru', self)
        btn_load_csv.clicked.connect(self.show_file_dialog)
        btn_load_csv.setMaximumWidth(400)
    
        h_layout.addWidget(btn_load_csv)

        # Пространство справа от кнопки
        h_layout.addStretch()
        # Добавляем кнопку на виджет
        layout.addLayout(h_layout)

        # Добавляем надпись
        lbl_info = QLabel('Информация о дублировании или загрузке новых закупок', self)
        lbl_info.setAlignment(Qt.AlignCenter)
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
        lbl_table_info = QLabel('Таблица дубликатов', self)
        lbl_table_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_table_info)
       
        # Вторая таблица
        self.second_table = QTableWidget(self)
        self.second_table.setColumnCount(8)
        self.second_table.setHorizontalHeaderLabels(['Номер закупки в БД', 'Реестровый номер', 'Дата аукциона', 'Дата начала заявки', 'Дата окончания заявки', 'Дата обновления', 'Дата размещения', 'Номер лота'])
        self.second_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.second_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.second_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.second_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.second_table)
        # Добавляем кнопку "Удалить выбранные записи"
        h_layout2 = QHBoxLayout()
        h_layout2.addStretch()
        btn_delete_selected = QPushButton('Удалить выбранные дубликаты', self)
        btn_delete_selected.clicked.connect(self.delete_selected_records)
        btn_delete_selected.setMaximumWidth(250)
        btn_delete_selected.setMinimumWidth(250)
        h_layout2.addWidget(btn_delete_selected)
        h_layout2.addStretch()
        layout.addLayout(h_layout2)

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
            self.all_count = count_total_records()
            if not insert_errors:
                QMessageBox.information(self, "Успех", "Данные успешно загружены")
                self.update_table()

                purchases = Purchase.select().where((Purchase.Currency != "RUB"))
                if purchases:
                    # reply = QMessageBox.question(self, "Внимание", "Найдены записи с валютами не в рублях. Изменить валюту?", 
                    #                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    
                    # if reply == QMessageBox.Yes:
                    #     self.cur = CurrencyWidget()
                    #     self.cur.show()
                    self.curr_wind.populate_table()
                    self.purchaseViewerall.resetFilters()
                    reply = QMessageBox()
                    self.update_second_table()
                    reply.setText("Найдены записи с валютами не в рублях. Изменить валюту?")
                    reply.addButton("нет", QMessageBox.NoRole)
                    reply.addButton("да", QMessageBox.YesRole)
                    result = reply.exec()
                    if result == 1:
                        self.cur = CurrencyWidget()
                        self.cur.populate_table()
                        self.cur.show()
                    else:
                       pass

                
                
                
             
    def populate_table(self, table):
        # Добавляем данные в таблицу
        data = [
             ('В БД НМЦК и ЦК всего размещено Закупок:', str(self.all_count)),
            ('В БД НМЦК и ЦК добавлено Закупок:', str(self.inserted_rows_count))
          
          
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
        self.main_window.updatePurchaseLabel()
    def handle_table_click(self, row, col):
        # Получаем значение из колонки 'Id'
        id_item = self.second_table.item(row, 0)  # Предполагаем, что 'Id' находится в первой колонке
        if id_item:
            selected_id = id_item.text()
            # print(f'Selected Id: {selected_id}')

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
        # reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
        #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        reply = QMessageBox()
        reply.setText('Вы точно хотите удалить выбранные записи?')
        reply.addButton("нет", QMessageBox.NoRole)
        reply.addButton("да", QMessageBox.YesRole)
        result = reply.exec()
        if result == 1:
            # if self.selected_ids:
                success = delete_records_by_id(self.selected_ids)
                if success:
                    QMessageBox.information(self, "Успех", f"Успешно удалены записи с номерами:, {self.selected_ids}")
                    # print("Успешно удалены записи с Id:", self.selected_ids)
                    self.second_table.clearContents()
                    # self.second_table.setRowCount(0)
                    self.selected_ids = []
                    self.update_second_table()
                    self.all_count = count_total_records()
                    self.update_table()
                    self.purchaseViewerall.resetFilters()
                    self.main_window.updatePurchaseLabel()
                else:
                    QMessageBox.information(self, "Ошибка", "Ошибка при удалении записей")
                    # print("Ошибка при удалении записей")
        else:
            self.update_second_table()
            # В противном случае, ничего не делаем
            pass
        

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = CsvLoaderWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())