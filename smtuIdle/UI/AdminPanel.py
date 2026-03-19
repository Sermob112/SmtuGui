from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QColor

from smtuIdle.CRUD_Operators.JsonToDB  import insert_in_table as insert_jsonl, insert_contracts,insert_customers,insert_suppliers
from smtuIdle.AddUserDialog import AddUserDialog
from smtuIdle.EditUserDialog import EditUserDialog
import sys

from smtuIdle.parserV3 import *


class DebugWidget(QWidget):
    def __init__(self, user='', role=''):
        super(DebugWidget, self).__init__()
        self.user = user
        self.role = role
        self.buttons_added = False
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        
        lbl_debug = QLabel('Отладка', self)
        layout.addWidget(lbl_debug)

        # Создаем компонент вкладок
        tab_widget = QTabWidget()

        # Добавляем вкладки
        tab_widget.addTab(self.create_logs_tab(), 'Журнал ')
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
        self.users_table_widget.setColumnCount(4)  # Количество столбцов
        self.users_table_widget.setHorizontalHeaderLabels(['№','Пользователь', 'Роль',"Пароль"])  # Заголовки столбцов
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
        main_layout = QVBoxLayout(tab)
        main_layout.setAlignment(Qt.AlignTop)

        # ── Группа: Загрузка данных ───────────────
        group_load = QGroupBox("Загрузка данных")
        grid_load = QGridLayout(group_load)
        grid_load.setSpacing(10)

        btn_load_csv = QPushButton("Загрузить CSV файл")
        btn_load_jsonl = QPushButton("Загрузить закупки из парсера")
        btn_load_contracts = QPushButton("Загрузить контракты из парсера")

        for btn in [btn_load_csv, btn_load_jsonl, btn_load_contracts]:
            btn.setFixedHeight(36)

        grid_load.addWidget(btn_load_csv, 0, 0)
        grid_load.addWidget(btn_load_jsonl, 0, 1)
        grid_load.addWidget(btn_load_contracts, 0, 2)

        btn_load_csv.clicked.connect(self.show_file_dialog)
        btn_load_jsonl.clicked.connect(self.show_jsonl_dialog)
        btn_load_contracts.clicked.connect(self.show_contracts_dialog)

        # ── Группа: Очистка данных ────────────────
        group_clear = QGroupBox("Очистка данных")
        grid_clear = QGridLayout(group_clear)
        grid_clear.setSpacing(10)

        btn_delete_data = QPushButton("Удалить все данные БД")
        btn_clear_users = QPushButton("Очистить журнал пользователей")
        btn_clear_changes = QPushButton("Очистить журнал изменений")

        for btn in [btn_delete_data, btn_clear_users, btn_clear_changes]:
            btn.setFixedHeight(36)

        # Кнопка удаления — на всю ширину сверху, чтобы выделялась
        grid_clear.addWidget(btn_delete_data, 0, 0, 1, 2)  # colspan=2
        grid_clear.addWidget(btn_clear_users, 1, 0)
        grid_clear.addWidget(btn_clear_changes, 1, 1)

        btn_delete_data.clicked.connect(self.delete_all_data)
        btn_clear_users.clicked.connect(self.clear_user_logs)
        btn_clear_changes.clicked.connect(self.clear_changed_dates)

        btn_load_customers = QPushButton("Загрузить заказчиков из парсера")
        btn_load_customers.setFixedHeight(36)

        grid_load.addWidget(btn_load_csv, 0, 0)
        grid_load.addWidget(btn_load_jsonl, 0, 1)
        grid_load.addWidget(btn_load_contracts, 0, 2)
        grid_load.addWidget(btn_load_customers, 1, 0, 1, 3)  # вторая строка, на всю ширину

        btn_load_customers.clicked.connect(self.show_customers_dialog)

        btn_load_suppliers = QPushButton("Загрузить поставщиков из парсера")
        btn_load_suppliers.setFixedHeight(36)
        grid_load.addWidget(btn_load_suppliers, 2, 0, 1, 3)  # третья строка
        btn_load_suppliers.clicked.connect(self.show_suppliers_dialog)
        # ── Сборка ────────────────────────────────
        main_layout.addWidget(group_load)
        main_layout.addWidget(group_clear)
        main_layout.addStretch()  # прижимаем группы вверх

        return tab

    def clear_user_logs(self):
        clear_user_log()
        self.table_widget.clearContents()

    def clear_changed_dates(self):
        clear_changed_date()

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
            self.users_table_widget.setItem(row_position, 2, QTableWidgetItem(user_role.role.name))
            self.users_table_widget.setItem(row_position, 3, QTableWidgetItem(user_role.user.password))  # Предполагая, что у роли есть атрибут name
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

    def show_jsonl_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JSONL files (*.jsonl);;All files (*.*)")
        file_dialog.setWindowTitle("Выберите файл закупок из парсера (.jsonl)")

        if not file_dialog.exec_():
            return

        selected_file = file_dialog.selectedFiles()[0]

        if not selected_file.endswith(".jsonl"):
            QMessageBox.warning(
                self, "Неверный формат",
                "Пожалуйста, выберите файл в формате .jsonl\n"
                "Используйте экспорт из парсера (purchases_export.jsonl)"
            )
            return

        # ── Прогресс-диалог ───────────────────────
        progress = QDialog(self)
        progress.setWindowTitle("Загрузка...")
        progress.setFixedSize(350, 80)
        progress.setWindowFlags(
            Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        lbl = QLabel("Идёт загрузка закупок, подождите...", progress)
        lbl.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(progress)
        layout.addWidget(lbl)
        progress.setLayout(layout)
        progress.show()
        QApplication.processEvents()

        # ── Загрузка ──────────────────────────────
        inserted, errors = None, []
        try:
            inserted, errors = insert_jsonl(
                filepath=selected_file,
                user=self.user,
                role=self.role
            )
        except Exception as e:
            errors.append(str(e))
            inserted = 0
        finally:
            progress.hide()
            progress.deleteLater()
            QApplication.processEvents()  # гарантируем закрытие до следующего диалога

        # ── Результат ─────────────────────────────
        if errors:
            error_preview = "\n".join(errors[:10])
            suffix = f"\n...и ещё {len(errors) - 10} ошибок" if len(errors) > 10 else ""
            QMessageBox.warning(
                self, "Загружено с ошибками",
                f"Загружено записей: {inserted}\n\nОшибки:\n{error_preview}{suffix}"
            )
        else:
            QMessageBox.information(
                self, "Успех",
                f"Закупки успешно загружены!\nДобавлено/обновлено записей: {inserted}"
            )

    def show_contracts_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JSONL files (*.jsonl);;All files (*.*)")
        file_dialog.setWindowTitle("Выберите файл контрактов из парсера (.jsonl)")

        if not file_dialog.exec_():
            return

        selected_file = file_dialog.selectedFiles()[0]
        if not selected_file.endswith(".jsonl"):
            QMessageBox.warning(self, "Неверный формат", "Выберите файл .jsonl")
            return

        progress = QDialog(self)
        progress.setWindowTitle("Загрузка...")
        progress.setFixedSize(350, 80)
        progress.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        QVBoxLayout(progress).addWidget(QLabel("Идёт загрузка контрактов, подождите...", progress))
        progress.show()
        QApplication.processEvents()

        inserted, errors = 0, []
        try:
            inserted, errors = insert_contracts(selected_file, self.user, self.role)
        except Exception as e:
            errors.append(str(e))
        finally:
            progress.hide()
            progress.deleteLater()
            QApplication.processEvents()

        if errors:
            error_preview = "\n".join(errors[:10])
            suffix = f"\n...и ещё {len(errors) - 10} ошибок" if len(errors) > 10 else ""
            QMessageBox.warning(self, "Загружено с ошибками",
                                f"Загружено: {inserted}\n\nОшибки:\n{error_preview}{suffix}")
        else:
            QMessageBox.information(self, "Успех",
                                    f"Контракты успешно загружены!\nДобавлено/обновлено: {inserted}")
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
        selected_rows = set(index.row() for index in self.users_table_widget.selectionModel().selectedIndexes())
        if selected_rows:
            selected_row = selected_rows.pop()
            user_id_item = self.users_table_widget.item(selected_row, 0)
            user_id = int(user_id_item.text())  
        dialog = EditUserDialog(user_id)
        if dialog.exec() == QDialog.Accepted:
            self.load_user_roles()

    def delete_user(self):
        selected_rows = set(index.row() for index in self.users_table_widget.selectionModel().selectedIndexes())
        if selected_rows:
            selected_row = selected_rows.pop()
            user_id_item = self.users_table_widget.item(selected_row, 0)
            user_id = int(user_id_item.text())  
            try:
                user = User.get(User.id == user_id)
                # Находим и удаляем все связанные записи в таблице UserRole
                UserRole.delete().where(UserRole.user == user).execute()
                # Удаляем пользователя из базы данных
                user.delete_instance()
                # Обновляем отображение таблицы
                self.load_user_roles()
                QMessageBox.information(self, "Успешно", "Пользователь успешно удален.")
            except User.DoesNotExist:
                QMessageBox.warning(self, "Ошибка", "Пользователь с указанным ID не найден.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не выбран для удаления.")

    def show_customers_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JSONL files (*.jsonl);;All files (*.*)")
        file_dialog.setWindowTitle("Выберите файл заказчиков из парсера (.jsonl)")

        if not file_dialog.exec_():
            return

        selected_file = file_dialog.selectedFiles()[0]
        if not selected_file.endswith(".jsonl"):
            QMessageBox.warning(self, "Неверный формат", "Выберите файл .jsonl")
            return

        progress = QDialog(self)
        progress.setWindowTitle("Загрузка...")
        progress.setFixedSize(350, 80)
        progress.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        QVBoxLayout(progress).addWidget(QLabel("Идёт загрузка заказчиков, подождите...", progress))
        progress.show()
        QApplication.processEvents()

        inserted, errors = 0, []
        try:
            inserted, errors = insert_customers(selected_file, self.user, self.role)
        except Exception as e:
            errors.append(str(e))
        finally:
            progress.hide()
            progress.deleteLater()
            QApplication.processEvents()

        if errors:
            error_preview = "\n".join(errors[:10])
            suffix = f"\n...и ещё {len(errors) - 10} ошибок" if len(errors) > 10 else ""
            QMessageBox.warning(self, "Загружено с ошибками",
                                f"Загружено: {inserted}\n\nОшибки:\n{error_preview}{suffix}")
        else:
            QMessageBox.information(self, "Успех",
                                    f"Заказчики успешно загружены!\nДобавлено/обновлено: {inserted}")

    def show_suppliers_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("JSONL files (*.jsonl);;All files (*.*)")
        file_dialog.setWindowTitle("Выберите файл поставщиков из парсера (.jsonl)")

        if not file_dialog.exec_():
            return

        selected_file = file_dialog.selectedFiles()[0]
        if not selected_file.endswith(".jsonl"):
            QMessageBox.warning(self, "Неверный формат", "Выберите файл .jsonl")
            return

        progress = QDialog(self)
        progress.setWindowTitle("Загрузка...")
        progress.setFixedSize(350, 80)
        progress.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        QVBoxLayout(progress).addWidget(QLabel("Идёт загрузка поставщиков, подождите...", progress))
        progress.show()
        QApplication.processEvents()

        inserted, errors = 0, []
        try:
            inserted, errors = insert_suppliers(selected_file, self.user, self.role)
        except Exception as e:
            errors.append(str(e))
        finally:
            progress.hide()
            progress.deleteLater()
            QApplication.processEvents()

        if errors:
            error_preview = "\n".join(errors[:10])
            suffix = f"\n...и ещё {len(errors) - 10} ошибок" if len(errors) > 10 else ""
            QMessageBox.warning(self, "Загружено с ошибками",
                                f"Загружено: {inserted}\n\nОшибки:\n{error_preview}{suffix}")
        else:
            QMessageBox.information(self, "Успех",
                                    f"Поставщики успешно загружены!\nДобавлено/обновлено: {inserted}")
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = DebugWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec_())
#