from PySide6.QtWidgets import *
from peewee import SqliteDatabase

from datetime import date
from models import Contract
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
from models import Purchase, Contract,ChangedDate
import os
import shutil
from peewee import DoesNotExist
import datetime
from InsertWidgetContract import InsertWidgetContract
from InsertWidgetContract2 import InsertWidgetContract2
db = SqliteDatabase('test.db')

class InsertPanelContract(QWidget):
    def __init__(self, purchase_id, db_wind,role,user,changer ):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        self.role = role
        self.user = user
        self.changer = changer
        # Создаем лейблы
        self.setWindowTitle("Добавить результаты закупки")
        self.setGeometry(100, 100, 600, 150)
        
        label1 = QLabel("Определение победителя закупки")
        label1.setAlignment(Qt.AlignCenter)
 
     
        button_NMCK_method_1= QPushButton("1.Добавить результаты закупки")
        button_NMCK_method_2= QPushButton("2.Добавить данные победителя закупки")
        # Создаем поля ввода
        # self.ContractFile = QLineEdit(self)
        
      
        # Устанавливаем максимальную ширину для кнопок
        fixed_width = 300
        button_NMCK_method_1.setFixedWidth(fixed_width)
        button_NMCK_method_2.setFixedWidth(fixed_width)
       
        button_NMCK_method_1.setStyleSheet("text-align: left;")
        button_NMCK_method_2.setStyleSheet("text-align: left;")
        

        
        # Устанавливаем политику размера для автоматического изменения высоты кнопки
        # button_NMCK_method_1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # button_NMCK_method_2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # button_NMCK_method_3.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # button_NMCK_method_4.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # browse_button_NMCK.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # browse_button_izvesh.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # browse_button_contract.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # browse_button_protocol.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)


        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)


        # Выравниваем кнопки налево
        layout2.addWidget(button_NMCK_method_1, alignment=Qt.AlignLeft)
        layout3.addWidget(button_NMCK_method_2, alignment=Qt.AlignLeft)
       
        # Добавляем лейбл и поле ввода во вторую строку
        
        button_NMCK_method_1.clicked.connect(self.add_button_tkp_clicked)
        button_NMCK_method_2.clicked.connect(self.add_button_cia_clicked)
     
 
        

        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(label1)
        self.layout1.addLayout(layout2)
        self.layout1.addLayout(layout3)


        
       
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout1)
        scroll_area.setWidget(scroll_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
    

    def add_button_tkp_clicked(self):
            self.tkp_shower = InsertWidgetContract(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.tkp_shower.setParent(self) 
            self.tkp_shower.show()
    
    def add_button_cia_clicked(self):   
            self.cia_shower = InsertWidgetContract2(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.cia_shower.setParent(self)
            self.cia_shower.show()

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetPanel(3)
#     window.show()
#     sys.exit(app.exec())
        
