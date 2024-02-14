from PySide6.QtWidgets import *
from models import UserRole, Role,User

class EditUserDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Редактирование пользователя')
        self.user_id = user_id

        layout = QVBoxLayout(self)

        label1 = QLabel("Выбирите роль")
        self.role_combo = QComboBox()
        self.populate_roles()
        layout.addWidget(label1)
        layout.addWidget(self.role_combo)

        label2 = QLabel("Изменить имя пользователя")
        self.username_edit = QLineEdit()
        layout.addWidget(label2)
        layout.addWidget(self.username_edit)

        self.edit_button = QPushButton('Редактировать')
        self.edit_button.clicked.connect(self.edit_user)
        layout.addWidget(self.edit_button)

        # Получите данные о пользователе и заполните поля
        self.populate_user_data()

    def populate_roles(self):
        roles = Role.select()
        for role in roles:
            self.role_combo.addItem(role.name, role.id)

    def populate_user_data(self):
        # Получите данные о пользователе и заполните поля
        user = User.get(User.id == self.user_id)
        self.username_edit.setText(user.username)
        # Дополнительно заполните поле пароля, если это необходимо

        # Выберите роль пользователя в выпадающем списке
        user_role = UserRole.get(UserRole.user == user)
        role_index = self.role_combo.findData(user_role.role.id)
        if role_index != -1:
            self.role_combo.setCurrentIndex(role_index)

    def edit_user(self):
        selected_role_id = self.role_combo.currentData()
        selected_role = Role.get(Role.id == selected_role_id)
        username = self.username_edit.text()

        if username:
            user = User.get(User.id == self.user_id)
            user.username = username
            user.save()

            # Обновите роль пользователя
            UserRole.update(role=selected_role).where(UserRole.user == user).execute()
            self.accept()
        else:
            QMessageBox.warning(self, 'Внимание', 'Введите имя пользователя.')


# Где-то в вашем коде, вероятно в методе add_user_dialog, создайте и отобразите диалог:

