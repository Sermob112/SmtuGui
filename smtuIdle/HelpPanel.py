from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import os, sys

from functools import partial
class HelpPanel(QWidget):
    def __init__(self):
        super().__init__()
        style = """
    QPushButton {
       
        font-size: 11pt;
        text-align: left;
        padding-left: 10px;
    }
"""
        self.QwordFinder = QPushButton("Описание БД ЦиЭПК")
        self.QwordFinder.setIcon(QIcon("Pics/right-arrow.png"))
        self.QwordFinder.setMaximumWidth(300)
        self.QwordFinder.clicked.connect(self.toggle_menu)
        self.SecSys = QPushButton("Руководство пользователя")
        self.SecSys.setIcon(QIcon("Pics/right-arrow.png"))
        self.SecSys.setMaximumWidth(300)
        self.SecSys.clicked.connect(self.toggle_menu_2)

        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        self.Qword = QLabel("Описание БД ЦиЭПК")
        menu_layout.addWidget(self.Qword)

        self.files = os.listdir("HelpFiles")
        target_file_11 = next(
            (f for f in self.files if f.startswith("11") and f.lower().endswith(".docx")),
            None
        )
        if target_file_11:
            button = QPushButton(target_file_11)
            button.setFixedSize(400, 30)
            button.clicked.connect(partial(self.open_file, target_file_11))
            menu_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignTop)

        self.menu_content.setLayout(menu_layout)
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(QVBoxLayout())
        self.menu_frame.layout().addWidget(self.menu_content)
        self.menu_frame.setVisible(False)

        self.menu_content2 = QWidget()
        menu_layout2 = QVBoxLayout()
        self.Qword2 = QLabel("Руководство пользователя")
        menu_layout2.addWidget(self.Qword2)

        target_file_12 = next(
            (f for f in self.files if f.startswith("12") and f.lower().endswith(".docx")),
            None
        )
        if target_file_12:
            button2 = QPushButton(target_file_12)
            button2.setFixedSize(400, 30)
            button2.clicked.connect(partial(self.open_file, target_file_12))
            menu_layout2.addWidget(button2, alignment=Qt.AlignmentFlag.AlignTop)

        self.menu_content2.setLayout(menu_layout2)
        self.menu_frame2 = QFrame()
        self.menu_frame2.setLayout(QVBoxLayout())
        self.menu_frame2.layout().addWidget(self.menu_content2)
        self.menu_frame2.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.QwordFinder)
        layout.addWidget(self.menu_frame)
        layout.addWidget(self.SecSys)
        layout.addWidget(self.menu_frame2)
        # layout.addWidget(self.SecSys2)
        # layout.addWidget(self.menu_frame3)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    def toggle_menu(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.QwordFinder.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.QwordFinder.setIcon(QIcon("Pics/right-arrow.png"))

    def toggle_menu_2(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame2.setVisible(not self.menu_frame2.isVisible())
        if self.menu_frame2.isVisible():
            self.SecSys.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.SecSys.setIcon(QIcon("Pics/right-arrow.png"))

    def open_file(self, file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "HelpFiles", file)
        print("Текущая рабочая директория:", os.getcwd())
        print("Директория скрипта:", base_dir)
        print("Итоговый путь:", file_path)
        print("Существует:", os.path.exists(file_path))
        ...

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", f"Файл не найден:\n{file_path}")
            return

        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка открытия файла", str(e))


#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = HelpPanel()
#     csv_loader_widget.show()
#     sys.exit(app.exec())