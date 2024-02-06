from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from auth import *
from PySide6.QtWidgets import *
from initialize_db import initialize_database
from MainWindow import Ui_MainWindow
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt,QRect,QCoreApplication
class AuthWindow(QWidget):
    def __init__(self):
        super(AuthWindow, self).__init__()

        self.setWindowTitle("Окно авторизации")
        self.setGeometry(100, 100, 1000, 600)
        self.auth = AuthManager()
        style = QStyleFactory.create('Fusion')
        app = QApplication.instance()
        app.setStyle(style)
        initialize_database()

        main_layout = QVBoxLayout()

        # Создайте макет для формы
        form_layout = QVBoxLayout()
        form_logPass = QVBoxLayout()
        form_layoutForLogPAs = QFormLayout()
        label_layout = QVBoxLayout()

        self.label = QLabel()
        self.label.setMaximumWidth(400)
        self.label.setWordWrap(True)
        self.label.setText("БАЗА ДАННЫХ ОБОСНОВАНИЙ НАЧАЛЬНЫХ (МАКСИМАЛЬНЫХ) ЦЕН КОНТРАКТОВ И ЦЕН КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ, ЗАКЛЮЧАЕМЫХ С ЕДИНСТВЕННЫМ ПОСТАВЩИКОМ, А ТАКЖЕ ЦЕН ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(self.width())
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.username_label = QLabel("Имя пользователя:")
        self.username_edit = QLineEdit("")
        self.username_edit.setPlaceholderText("Введите ваше имя пользователя")
        self.username_edit.setMaximumWidth(200)  # Установите максимальную ширину

        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Введите ваш пароль")
        self.password_edit.setMaximumWidth(200)  # Установите максимальную ширину
        self.password_edit.setAlignment(Qt.AlignLeft)
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)
        self.login_button.setFixedWidth(300)
        label_layout.addWidget(self.label)
        label_layout.setAlignment(Qt.AlignCenter)
        self.label.move(0, -100)
        form_layoutForLogPAs.addRow(self.username_label, self.username_edit)
        form_layoutForLogPAs.addRow(self.password_label, self.password_edit)
        form_layoutForLogPAs.setFormAlignment(Qt.AlignCenter) 
        form_layout.addWidget(self.login_button)
        form_layout.setAlignment(Qt.AlignCenter)
        form_logPass.addLayout(form_layoutForLogPAs)
        form_logPass.addLayout(form_layout)
        # Добавьте макет формы в центральный макет
        main_layout.addLayout(label_layout)
        main_layout.addLayout(form_logPass)
        # main_layout.addLayout(form_layout)

        # # Выровняйте форму по центру окна
        form_logPass.setAlignment(Qt.AlignCenter)
        form_logPass.setContentsMargins (0,0,0,200)
       
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
            ui.show()
            self.close()

        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка входа")

if __name__ == "__main__":
    app = QApplication([])
    auth_window = AuthWindow()
    auth_window.show()
    app.exec()