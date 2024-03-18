from PySide6.QtWidgets import *
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination,CurrencyRate
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import QColor,QIcon,QFont
from PySide6.QtCore import QDate
from peewee import JOIN
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
import os, sys
import subprocess

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
        self.QwordFinder = QPushButton("Нормативные документы")
        self.QwordFinder.setIcon(QIcon("Pics/right-arrow.png"))
        self.QwordFinder.setMaximumWidth(300)
        self.QwordFinder.clicked.connect(self.toggle_menu)
        self.SecSys = QPushButton("Руководство БД НМЦК")
        self.SecSys.setIcon(QIcon("Pics/right-arrow.png"))
        self.SecSys.setMaximumWidth(300)
        self.SecSys.clicked.connect(self.toggle_menu_2)
        self.SecSys2 = QPushButton("Руководство данной системой")
        self.SecSys2.setIcon(QIcon("Pics/right-arrow.png"))
        self.SecSys2.setMaximumWidth(300)
        self.SecSys2.clicked.connect(self.toggle_menu_3)
        self.SecSys2.setStyleSheet(style)
        self.QwordFinder.setStyleSheet(style)
        self.SecSys.setStyleSheet(style)

        # self.list_widget = QListWidget()
        # self.list_widget.itemClicked.connect(self.open_file)
        #меню по ключевому слову
        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        self.Qword = QLabel("Список нормативных документов")
        
        menu_layout.addWidget(self.Qword)
        self.files = os.listdir("HelpFiles")
        for file in self.files[:1]:
            if file.endswith(".docx"):
                button = QPushButton(file)
                button.setFixedSize(400, 30)
                button.clicked.connect(lambda checked: self.open_file(file))
                menu_layout.addWidget(button)
       
        menu_layout.addWidget(button,alignment=Qt.AlignmentFlag.AlignTop)
        self.menu_content.setLayout(menu_layout)
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(QVBoxLayout())
        self.menu_frame.layout().addWidget(self.menu_content)
        self.menu_frame.setVisible(False)
        #меню по ключевому слову
        self.menu_content2 = QWidget()
        menu_layout2 = QVBoxLayout()
        self.Qword2 = QLabel("Список документов БД НМЦК")
        
        menu_layout2.addWidget(self.Qword2)
        self.files = os.listdir("HelpFiles")
        for file in self.files[1:2]:
            if file.endswith(".docx"):
                button = QPushButton(file)
                button.setFixedSize(400, 30)
                button.clicked.connect(lambda checked:  self.open_file(file))
                menu_layout2.addWidget(button)
       
        menu_layout2.addWidget(button,alignment=Qt.AlignmentFlag.AlignTop)
        self.menu_content2.setLayout(menu_layout2)
        self.menu_frame2 = QFrame()
        self.menu_frame2.setLayout(QVBoxLayout())
        self.menu_frame2.layout().addWidget(self.menu_content2)
        self.menu_frame2.setVisible(False)
        #меню по ключевому слову
        # self.menu_content3 = QWidget()
        # menu_layout3 = QVBoxLayout()
        # self.Qword3 = QLabel("Перечень документов по управлению системой")
        
        # menu_layout3.addWidget(self.Qword3)
        # self.files = os.listdir("HelpFiles")
        # for file in self.files[2:3]:
        #     if file.endswith(".docx"):
        #         button = QPushButton(file)
        #         button.setFixedSize(400, 30)
        #         button.clicked.connect(lambda checked:  self.open_file(file))
        #         menu_layout3.addWidget(button)
       
        # menu_layout3.addWidget(button,alignment=Qt.AlignmentFlag.AlignTop)
        # self.menu_content3.setLayout(menu_layout3)
        # self.menu_frame3 = QFrame()
        # self.menu_frame3.setLayout(QVBoxLayout())
        # self.menu_frame3.layout().addWidget(self.menu_content3)
        # self.menu_frame3.setVisible(False)
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
    def toggle_menu_3(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame3.setVisible(not self.menu_frame3.isVisible())
        if self.menu_frame3.isVisible():
            self.SecSys2.setIcon(QIcon("Pics/arrow-down.png"))
        else:
            self.SecSys2.setIcon(QIcon("Pics/right-arrow.png"))

    def open_file(self, file):
        file_path = os.path.join("HelpFiles", file)
        os.startfile(file_path)

   



if __name__ == '__main__':
    app = QApplication(sys.argv)
    csv_loader_widget = HelpPanel()
    csv_loader_widget.show()
    sys.exit(app.exec())