from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from auth import *
from initialize_db import initialize_database
from MainWindow import Ui_MainWindow

class AuthWindow(QWidget):
    def __init__(self):
        super(AuthWindow, self).__init__()

        self.setWindowTitle("Окно авторизации")
        self.setGeometry(100, 100, 400, 200)
        self.auth = AuthManager()
       
        initialize_database()
        layout = QVBoxLayout()

        self.username_label = QLabel("Имя пользователя:")
        self.username_edit = QLineEdit()

        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.login_button)

        self.setLayout(layout)
        # Создайте атрибут класса для сохранения ссылки на Ui_MainWindow
        self.main_window = QMainWindow()

    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        user = self.auth.authenticate(username, password)
        if user:
            QMessageBox.information(self, "Успех", "Вы успешно авторизировались!")
            


            ui = Ui_MainWindow()
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