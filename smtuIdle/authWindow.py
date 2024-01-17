from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from auth import *
from PySide6.QtWidgets import *
from initialize_db import initialize_database
from MainWindow import Ui_MainWindow
from PySide6.QtCore import Qt
class AuthWindow(QWidget):
    def __init__(self):
        super(AuthWindow, self).__init__()

        self.setWindowTitle("Окно авторизации")
        self.setGeometry(100, 100, 400, 200)
        self.auth = AuthManager()
        style = QStyleFactory.create('Fusion')
        app = QApplication.instance()
        app.setStyle(style)
        initialize_database()

        main_layout = QVBoxLayout()

        # Создайте макет для формы
        form_layout = QFormLayout()

        self.username_label = QLabel("Имя пользователя:")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Введите ваше имя пользователя")
        self.username_edit.setMaximumWidth(200)  # Установите максимальную ширину

        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Введите ваш пароль")
        self.password_edit.setMaximumWidth(200)  # Установите максимальную ширину

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)

        form_layout.addRow(self.username_label, self.username_edit)
        form_layout.addRow(self.password_label, self.password_edit)
        form_layout.addRow(self.login_button)

        # Добавьте макет формы в центральный макет
        main_layout.addLayout(form_layout)

        # Выровняйте форму по центру окна
        main_layout.setAlignment(Qt.AlignCenter)

        # Установите центральный макет
        self.setLayout(main_layout)

        # # Добавьте стили для улучшения внешнего вида
        # style = """
        #     QWidget {
        #         background-color: #f0f0f0;
        #     }
        #     QLabel {
        #         font-size: 14px;
        #     }
        #     QLineEdit {
        #         padding: 5px;
        #         font-size: 14px;
        #         border: 1px solid #ccc;
        #         border-radius: 3px;
        #     }
        #     QPushButton {
        #         padding: 5px;
        #         font-size: 14px;
        #         background-color: #4CAF50;
        #         color: white;
        #         border: none;
        #         border-radius: 3px;
        #     }
        #     QPushButton:hover {
        #         background-color: #45a049;
        #     }
        # """

        # self.setStyleSheet(style)

        
         # Убрать рамку окна для более современного вида
        self.main_window = QMainWindow()

    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        user = self.auth.authenticate(username, password)
        if user:
            QMessageBox.information(self, "Успех", "Вы успешно авторизировались!")
            

            
            ui = Ui_MainWindow(username)
            ui.setupUi(self.main_window)
            self.main_window.show()
            self.close()

        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка входа")

if __name__ == "__main__":
    app = QApplication([])
    auth_window = AuthWindow()
    auth_window.show()
    app.exec()