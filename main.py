from PySide6.QtWidgets import QApplication,QMainWindow
import sys
from QT.pyStartWindow import Ui_StartWindow
from QT.pyLoginWindow import Ui_LoginWindow
class StartWindow(QMainWindow):
    def __init__(self, parent = None):
        super(StartWindow, self).__init__(parent)
        self.ui = Ui_StartWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.open_login_window)


    def open_login_window(self):
        login_window = LoginWindow(self)
        login_window.show()
        self.hide()

class LoginWindow(QMainWindow):
    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)

if __name__ == '__main__':
    app= QApplication()
    window = StartWindow()
    window.show()
    sys.exit(app.exec_())