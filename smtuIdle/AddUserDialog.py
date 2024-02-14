from PySide6.QtWidgets import *
from models import UserRole, Role,User

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Добавление пользователя')
        
        layout = QVBoxLayout(self)
        label1 = QLabel(f"Выбирите роль")
        self.role_combo = QComboBox()
        self.populate_roles()
        layout.addWidget(label1)
        layout.addWidget(self.role_combo)
        label2 = QLabel(f"Введите имя пользователя")
        self.username_edit = QLineEdit()
        layout.addWidget(label2)
        layout.addWidget(self.username_edit)
        label3 = QLabel(f"Введите пароль ")
        self.upassword_edit = QLineEdit()
        layout.addWidget(label3)
        layout.addWidget( self.upassword_edit)

        self.add_button = QPushButton('Добавить')
        self.add_button.clicked.connect(self.add_user)
        layout.addWidget(self.add_button)

    def populate_roles(self):
        roles = Role.select()
        for role in roles:
            self.role_combo.addItem(role.name, role.id)

    def add_user(self):
        selected_role_id = self.role_combo.currentData()
        selected_role = Role.get(Role.id == selected_role_id)
        username = self.username_edit.text()
        password = self.upassword_edit.text()
        if username:
        # Создаем пользователя
            new_user = User.create(username=username, password =password )

            # Присваиваем ему роль
            UserRole.create(user=new_user, role=selected_role)

            self.accept()
        else:
            QMessageBox.warning(self, 'Внимание', 'Введите имя пользователя.')

# Где-то в вашем коде, вероятно в методе add_user_dialog, создайте и отобразите диалог:

