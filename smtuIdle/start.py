from auth import *
from smtuIdle.BD.models import UserLog
from PySide6.QtWidgets import *
from smtuIdle.BD.initialize_db import initialize_database
from smtuIdle.UI.MainWindow import Ui_MainWindow
from PySide6.QtGui import QFont, QIcon, QPixmap, QKeySequence, QShortcut
from datetime import datetime
from PySide6.QtCore import Qt


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
        form_layout = QVBoxLayout()
        form_logPass = QVBoxLayout()
        form_layoutForLogPAs = QFormLayout()
        label_layout = QVBoxLayout()

        form_logPass.setAlignment(Qt.AlignCenter)
        form_logPass.setContentsMargins(0, 0, 0, 200)

        # Изображения в шапке
        image_label_top_left = QLabel()
        pixmap = QPixmap("Pics/4.png")
        pixmap = pixmap.scaledToWidth(50)
        image_label_top_left.setPixmap(pixmap)
        image_label_top_left.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        pics_layout.addWidget(image_label_top_left)

        image_label_top_right = QLabel()
        pixmap = QPixmap("Pics/4.png")
        pixmap = pixmap.scaledToWidth(50)
        image_label_top_right.setPixmap(pixmap)
        image_label_top_right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        pics_layout.addWidget(image_label_top_right)
        main_layout.addLayout(pics_layout)

        self.setLayout(main_layout)
        self.main_window = QMainWindow()

        # Заголовок
        self.label = QLabel()
        self.label.setMaximumWidth(400)
        self.label.setWordWrap(True)
        self.label.setText("БАЗА ДАННЫХ ЦЕН И ЭКОНОМИЧЕСКИХ ПОКАЗАТЕЛЕЙ ВЫПОЛНЕНИЯ ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(self.width())
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)

        # Поля ввода
        self.username_label = QLabel("Имя пользователя:")
        self.username_edit = QLineEdit("")
        self.username_edit.setPlaceholderText("Введите ваше имя пользователя")
        self.username_edit.setMaximumWidth(200)
        lock_icon = QIcon("Pics/icons8-пользователь-30.png")
        self.username_edit.addAction(lock_icon, QLineEdit.LeadingPosition)

        self.password_label = QLabel("Пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Введите ваш пароль")
        self.password_edit.setMaximumWidth(200)
        self.password_edit.setAlignment(Qt.AlignLeft)
        lock_icon = QIcon("Pics/icons8-пароль-30.png")
        self.password_edit.addAction(lock_icon, QLineEdit.LeadingPosition)

        # Кнопка входа — Enter тоже срабатывает
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.authenticate)
        self.login_button.setFixedWidth(320)
        self.login_button.setDefault(True)  # Enter = нажать кнопку
        login_icon = QIcon("Pics/icons8-вход-в-систему,-в-кружке,-стрелка-вправо-30.png")
        self.login_button.setIcon(login_icon)

        # Нажатие Enter в полях тоже вызывает authenticate
        self.username_edit.returnPressed.connect(self.authenticate)
        self.password_edit.returnPressed.connect(self.authenticate)

        # -------------------------------------------------------
        # Аварийный вход без логина/пароля: Ctrl+Shift+F12
        # -------------------------------------------------------
        self.emergency_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F12"), self)
        self.emergency_shortcut.activated.connect(self.emergency_login)
        # -------------------------------------------------------

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

        main_layout.addLayout(label_layout)
        main_layout.addLayout(form_logPass)

    def open_main_window(self, username: str):
        """Открывает главное окно без лишних диалогов."""
        UserLog.create(username=username, login_time=datetime.now())
        ui = Ui_MainWindow(username)
        ui.show()
        self.close()

    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        user = self.auth.authenticate(username, password)
        if user:
            # Убрали QMessageBox — сразу открываем главное окно
            self.open_main_window(username)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def emergency_login(self):
        """Аварийный вход по Ctrl+Shift+F12 без проверки логина/пароля."""
        self.open_main_window("Администратор")


if __name__ == "__main__":
    app = QApplication([])
    auth_window = AuthWindow()
    auth_window.show()
    app.exec()