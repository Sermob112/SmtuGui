from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from auth import *
from models import UserLog
from PySide6.QtWidgets import *
from initialize_db import initialize_database
from MainWindow import Ui_MainWindow
from PySide6.QtGui import QFont,QIcon,QPixmap
from datetime import datetime
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
        pics_layout = QHBoxLayout()
        # Создайте макет для формы
        form_layout = QVBoxLayout()
        form_logPass = QVBoxLayout()
        form_layoutForLogPAs = QFormLayout()
        label_layout = QVBoxLayout()
         # # Выровняйте форму по центру окна
        form_logPass.setAlignment(Qt.AlignCenter)
        form_logPass.setContentsMargins (0,0,0,200)
   

        # Добавление изображения в верхний левый угол
        image_label_top_left = QLabel()
        pixmap = QPixmap("Pics/4.png")
        pixmap = pixmap.scaledToWidth(50)  # Масштабирование изображения по ширине
        image_label_top_left.setPixmap(pixmap)
        image_label_top_left.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        pics_layout.addWidget(image_label_top_left)
        
        image_label_top_right = QLabel()
        pixmap = QPixmap("Pics/4.png")
        pixmap = pixmap.scaledToWidth(50)  # Масштабирование изображения по ширине
        image_label_top_right.setPixmap(pixmap)
        image_label_top_right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        pics_layout.addWidget(image_label_top_right)
        main_layout.addLayout(pics_layout)
        # Установите центральный макет
        self.setLayout(main_layout)
        self.main_window = QMainWindow()
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
        lock_icon = QIcon("Pics/icons8-пользователь-30.png")  # Путь к вашей иконке
        self.username_edit.addAction(lock_icon, QLineEdit.LeadingPosition)
        
        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Введите ваш пароль")
        self.password_edit.setMaximumWidth(200)  # Установите максимальную ширину
        self.password_edit.setAlignment(Qt.AlignLeft)
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)
        self.login_button.setFixedWidth(320)
        lock_icon = QIcon("Pics/icons8-пароль-30.png")  # Путь к вашей иконке
        self.password_edit.addAction(lock_icon, QLineEdit.LeadingPosition)
        login_icon = QIcon("Pics/icons8-вход-в-систему,-в-кружке,-стрелка-вправо-30.png")
        self.login_button.setIcon(login_icon)

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

       

    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        user = self.auth.authenticate(username, password)
        if user:
            QMessageBox.information(self, "Успех", "Вы успешно авторизировались!")
            UserLog.create(username=username, login_time=datetime.now())

            
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