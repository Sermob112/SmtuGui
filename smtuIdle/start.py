from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QFormLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from auth import *
from models import UserLog
from PySide6.QtWidgets import *
from initialize_db import initialize_database
from MainWindow import Ui_MainWindow
from PySide6.QtGui import QFont,QIcon,QPixmap
from datetime import datetime
from PySide6.QtCore import Qt,QRect,QCoreApplication
class GrandWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.stack_layout = QStackedLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.stack_layout)
        self.setCentralWidget(self.central_widget)

        self.auth_window = AuthWindow(self)
        self.db_connection_window = DBConnectionWindow(self.stack_layout)

        self.stack_layout.addWidget(self.auth_window)
        self.stack_layout.addWidget(self.db_connection_window)

        self.auth_window.connect_button.clicked.connect(self.switch_to_db_connection_window)

    def switch_to_db_connection_window(self):
        self.stack_layout.setCurrentIndex(1)



class DBConnectionWindow(QWidget):
    def __init__(self, stack_layout):
        super().__init__()
        self.setWindowTitle("Окно подключения к БД")
        self.setGeometry(100, 100, 600, 400)
        self.stack_layout = stack_layout
        # Создаем элементы управления для ввода информации о подключении
        layout = QVBoxLayout()
        
        self.db_name_edit = QLineEdit()
        self.db_name_edit.setFixedWidth(320)

        self.db_user_edit = QLineEdit()
        self.db_user_edit.setFixedWidth(320)

        self.db_password_edit = QLineEdit()
        self.db_password_edit.setFixedWidth(320)

        self.db_host_edit = QLineEdit()
        self.db_host_edit.setFixedWidth(320)

        self.db_port_edit = QLineEdit()
        self.db_port_edit.setFixedWidth(320)
        label_db_name = QLabel("Имя базы данных:")
        label_db_name.setMaximumWidth(100)

        label_db_user = QLabel("Пользователь:")
        label_db_user.setMaximumWidth(100)

        label_db_password = QLabel("Пароль:")
        label_db_password.setMaximumWidth(100)

        label_db_host = QLabel("Хост:")
        label_db_host.setMaximumWidth(100)

        label_db_port = QLabel("Порт:")
        label_db_port.setMaximumWidth(100)

        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()
        layout4 = QHBoxLayout()
        layout5 = QHBoxLayout()
        layout6 = QHBoxLayout()
        layout7 = QHBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(label_db_name)
        layout1.addWidget(self.db_name_edit)

        layout2 = QHBoxLayout()
        layout2.addWidget(label_db_user)
        layout2.addWidget(self.db_user_edit)

        layout3 = QHBoxLayout()
        layout3.addWidget(label_db_password)
        layout3.addWidget(self.db_password_edit)

        layout4 = QHBoxLayout()
        layout4.addWidget(label_db_host)
        layout4.addWidget(self.db_host_edit)

        layout5 = QHBoxLayout()
        layout5.addWidget(label_db_port)
        layout5.addWidget(self.db_port_edit)
        connect_button = QPushButton("Подключиться")
        connect_button.setFixedWidth(320)
        connect_button.clicked.connect(self.connect_to_database)
        
        layout6.addWidget(connect_button)
        
        back_button = QPushButton("Назад")
        back_button.setFixedWidth(320)
        back_button.clicked.connect(self.switch_to_auth_window)
        
        layout7.addWidget(back_button)
        
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        layout.addLayout(layout4)
        layout.addLayout(layout5)
        layout.addLayout(layout6)
        layout.addLayout(layout7)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        
    def connect_to_database(self):
        success = initialize_database(self.db_name_edit.text(), self.db_user_edit.text(),
                                    self.db_password_edit.text(), self.db_host_edit.text(),
                                    self.db_port_edit.text())
        if success:
            QMessageBox.information(self, "Успешное подключение к БД", "Успешное подключение к БД")
        else:
            QMessageBox.warning(self, "Неудачное подключение к БД", "Неудачное подключение к БД")

    def switch_to_auth_window(self):
        self.stack_layout.setCurrentIndex(0)

       
        
class AuthWindow(QWidget):
    def __init__(self, main_wind):
        super(AuthWindow, self).__init__()
        self.main_wind = main_wind
        self.setWindowTitle("Окно авторизации")
        self.setGeometry(100, 100, 1000, 600)
        self.auth = AuthManager()
        style = QStyleFactory.create('Fusion')
        app = QApplication.instance()
        app.setStyle(style)
        # initialize_database()

        main_layout = QVBoxLayout()
        pics_layout = QHBoxLayout()
        connect_layout = QHBoxLayout()
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
        self.connect_button = QPushButton("Подключиться к БД")
        self.connect_button.setFixedWidth(320)
        # self.connect_button.clicked.connect(self.switch_to_new_window)

        connect_layout.addWidget(self.connect_button,alignment=Qt.AlignCenter)
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
        self.label.setText("БАЗА ДАННЫХ ОБОСНОВАНИЙ НАЧАЛЬНЫХ (МАКСИМАЛЬНЫХ) ЦЕН КОНТРАКТОВ И ЦЕН КОНТРАКТОВ, ЗАКЛЮЧАЕМЫХ С ЕДИНСТВЕННЫМ ПОСТАВЩИКОМ, А ТАКЖЕ ЦЕН ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ")
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
        verticalSpacer1 = QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(verticalSpacer1)
        main_layout.addLayout(label_layout)
        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)
        main_layout.addItem(verticalSpacer)
        main_layout.addLayout(form_logPass)
        main_layout.addLayout(connect_layout)
        # main_layout.addLayout(form_layout)
    # def switch_to_new_window(self):
    #     self.db_connection_window = DBConnectionWindow()
    #     self.db_connection_window.show()
    #     self.hide()
    #     self.db_connection_window.closed.connect(self.show)


    def authenticate(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        user = self.auth.authenticate(username, password)
        if user:
            QMessageBox.information(self, "Успех", "Вы успешно авторизировались!")
            UserLog.create(username=username, login_time=datetime.now())

            
            ui = Ui_MainWindow(username)
            ui.show()

            self.main_wind.close()

        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка входа")


       
if __name__ == "__main__":
    app = QApplication([])
    main_window = GrandWindow()
    main_window.show()
    app.exec()