from PySide6.QtWidgets import QApplication,QMainWindow
import os
import sys
from QT.pyStartWindow import Ui_StartWindow
from QT.pyLoginWindow import Ui_LoginWindow
from QT.pyFilterWindow import Ui_FilterWindow
from auth import *
from PySide6.QtCore import Signal
from  initialize_db import *
class StartWindow(QMainWindow):
    def __init__(self, parent = None):
        super(StartWindow, self).__init__(parent)
        self.ui = Ui_StartWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.open_login_window)
        
    def open_login_window(self):
        login_window = LoginWindow(self)
        login_window.closed.connect(self.show_start_window)
        login_window.show()
        self.hide()
    def show_start_window(self):
        self.show()

class LoginWindow(QMainWindow):
    closed = Signal()
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self.ui.Login.clicked.connect(self.auth)
        self.destroyed.connect(self.on_window_closed)

    def auth(self):
        username = self.ui.LoginEdit.toPlainText()
        password = self.ui.PasswordEdit.toPlainText()

        auth_manager = AuthManager()
        user = auth_manager.authenticate(username, password)

        if user:
            print(f"User {username} authenticated!")
            filter = FilterWindow(self)
            filter.show()
        else:
            print("Authentication failed!")
    def on_window_closed(self):
        self.closed.emit()


class FilterWindow(QMainWindow):
    def __init__(self, parent = None):
        super(FilterWindow, self).__init__(parent)
        self.ui = Ui_FilterWindow()
        self.ui.setupUi(self)

        
   

if __name__ == '__main__':
    # Получаем путь к текущему исполняемому файлу
    initialize_database()
    app= QApplication()
    window = StartWindow()
    window.show()
    sys.exit(app.exec_())