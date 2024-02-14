from PySide6 import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QColor
import statistics
from models import *
from peewee import *
import pandas as pd
from parserV3 import *
from AddUserDialog import AddUserDialog
from EditUserDialog import EditUserDialog
import sys

class DebugWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.buttons_added = False 
    def init_ui(self):
        layout = QVBoxLayout()
        
        lbl_debug = QLabel('Отладка', self)
        layout.addWidget(lbl_debug)

        # Создаем компонент вкладок
        tab_widget = QTabWidget()

        # Добавляем вкладки
        tab_widget.addTab(self.create_logs_tab(), 'Логи')
        tab_widget.addTab(self.create_users_tab(), 'Пользователи и роли')
        tab_widget.addTab(self.bd_contoll(), 'Управление БД')

        layout.addWidget(tab_widget)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def create_logs_tab(self):
        # Создаем вкладку для первых данных
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Таблица для первых данных
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(['Имя пользователя', 'Вход', 'Выход'])
        layout.addWidget(self.table_widget)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Загрузка первых данных
        self.load_logs()
        return tab

    def create_users_tab(self):
        
        # Создаем вкладку для данных пользователей
        tab = QWidget()
        self.layout_user = QVBoxLayout(tab)

        # Таблица для данных пользователей
        self.users_table_widget = QTableWidget()
        self.users_table_widget.setColumnCount(3)  # Количество столбцов
        self.users_table_widget.setHorizontalHeaderLabels(['№','Пользователь', 'Роль'])  # Заголовки столбцов
        self.layout_user.addWidget(self.users_table_widget)
        self.users_table_widget.horizontalHeader().setStretchLastSection(True)
        self.users_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table_widget.verticalHeader().setVisible(False)
        self.users_table_widget.horizontalHeader().setVisible(True)
        
        # Загрузка данных пользователей
        self.load_user_roles()
         # Кнопка "Добавить пользователя"
        btn_add_user = QPushButton('Добавить пользователя', self)
        btn_add_user.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
        self.layout_user.addWidget(btn_add_user, alignment=Qt.AlignCenter)
         # Привязываем обработчик события clicked
        btn_add_user.clicked.connect(self.add_user_dialog)
        self.users_table_widget.itemSelectionChanged.connect(self.user_selection_changed)

        # # Кнопка "Редактировать пользователя"
        # btn_edit_user = QPushButton('Редактировать пользователя', self)
        # btn_edit_user.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
        # layout.addWidget(btn_edit_user, alignment=Qt.AlignCenter)
        # btn_edit_user.clicked.connect(self.edit_user_dialog)
        # # Кнопка "Удалить пользователя"
        # btn_delete_user = QPushButton('Удалить пользователя', self)
        # btn_delete_user.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
        # layout.addWidget(btn_delete_user, alignment=Qt.AlignCenter)

        return tab
    def bd_contoll(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        buttonLAyout = QHBoxLayout(tab)
        # Кнопка загрузки CSV файла
        btn_load_csv = QPushButton('Загрузить CSV файл отладки', self)
        btn_load_csv.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
        buttonLAyout.addWidget(btn_load_csv, alignment=Qt.AlignTop)  # Устанавливаем выравнивание кнопки вверх

        # Кнопка удаления всех данных
        btn_delete_data = QPushButton('Удалить все данные БД', self)
        btn_delete_data.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
        buttonLAyout.addWidget(btn_delete_data, alignment=Qt.AlignTop)  # Устанавливаем выравнивание кнопки вверх
        layout.addLayout(buttonLAyout)
        return tab

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
    def load_user_roles(self):
        # Получаем данные пользователей из модели UserRole
        users_roles = UserRole.select()
        # Очищаем таблицу перед загрузкой новых данных
        self.users_table_widget.clearContents()
        self.users_table_widget.setRowCount(0)
        for user_role in users_roles:
            row_position = self.users_table_widget.rowCount()
            self.users_table_widget.insertRow(row_position)
            self.users_table_widget.setItem(row_position, 0, QTableWidgetItem(str(user_role.user.id)))
            self.users_table_widget.setItem(row_position, 1, QTableWidgetItem(user_role.user.username))  # Предполагая, что у пользователя есть атрибут username
            self.users_table_widget.setItem(row_position, 2, QTableWidgetItem(user_role.role.name))  # Предполагая, что у роли есть атрибут name
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


    def edit_user(self):
        # Получаем данные пользователя и его текущую роль
        selected_user_id = self.user_combo.currentData()
        selected_user = User.get(User.id == selected_user_id)
        selected_role_id = self.role_combo.currentData()
        selected_role = Role.get(Role.id == selected_role_id)

        # Проверяем, что пользователь и роль выбраны
        if selected_user and selected_role:
            # Обновляем роль пользователя
            UserRole.update(role=selected_role).where(UserRole.user == selected_user).execute()
            self.accept()
        else:
            QMessageBox.warning(self, 'Внимание', 'Выберите пользователя и роль.')


    def user_selection_changed(self):
        selected_items = self.users_table_widget.selectedItems()
        if selected_items:
            # Очищаем предыдущее выделение
            for row in range(self.users_table_widget.rowCount()):
                for col in range(self.users_table_widget.columnCount()):
                    item = self.users_table_widget.item(row, col)
                    

            # Подсвечиваем выбранную строку
            for item in selected_items:
                item.setBackground(QColor("lightblue"))

            # Добавляем кнопки только к выбранной строке
            selected_row = selected_items[0].row() if selected_items else -1
            if selected_row != -1:
                self.add_buttons_to_user_row(selected_row)
                
    def add_buttons_to_user_row(self, row):
        if not self.buttons_added:
            # Кнопка "Редактировать пользователя"
            btn_edit_user = QPushButton('Редактировать пользователя', self)
            btn_edit_user.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
            self.layout_user.addWidget(btn_edit_user, alignment=Qt.AlignCenter)
            btn_edit_user.clicked.connect(self.edit_user_dialog)
            # Кнопка "Удалить пользователя"
            btn_delete_user = QPushButton('Удалить пользователя', self)
            btn_delete_user.setFixedWidth(300)  # Устанавливаем минимальную ширину кнопки
            self.layout_user.addWidget(btn_delete_user, alignment=Qt.AlignCenter)
            btn_delete_user.clicked.connect(self.delete_user)
            self.buttons_added = True

    def add_user_dialog(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_user_roles()

    def edit_user_dialog(self):
        dialog = EditUserDialog(self,user_id = 1)
        user_id = 1
        if dialog.exec() == QDialog.Accepted:
            self.load_user_roles()

    def delete_user(self):
        selected_items = self.users_table_widget.selectedItems()
        if selected_items:
            # Получаем ID пользователя из первого столбца выбранной строки
            selected_row = selected_items[0].row()
            user_id_item = self.users_table_widget.item(selected_row, 0)
            user_id = int(user_id_item.text())  # Преобразуем текст в целочисленный ID пользователя
            print(user_id)
            # Здесь вы должны выполнить удаление пользователя с использованием полученного user_id
            # Например, если вы используете Peewee ORM, это может выглядеть так:
            try:
                user = User.get(User.id == user_id)
                user.delete_instance()  # Удаляем пользователя из базы данных
                # Обновляем отображение таблицы
                self.load_user_roles()
                QMessageBox.information(self, "Успешно", "Пользователь успешно удален.")
            except User.DoesNotExist:
                QMessageBox.warning(self, "Ошибка", "Пользователь с указанным ID не найден.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не выбран для удаления.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    csv_loader_widget = DebugWidget()
    csv_loader_widget.show()
    sys.exit(app.exec_())
            