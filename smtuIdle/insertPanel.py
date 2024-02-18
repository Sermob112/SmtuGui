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
from InsertWidgetNMCK import InsertWidgetNMCK
from InsertWidgetCEIA import InsertWidgetCEIA
from InsertWidgetNMCK_2 import InsertWidgetNMCK_2
from InsertWidgetNMCK_3 import InsertWidgetNMCK_3
from InsertWidgetNMCK_4 import InsertWidgetNMCK_4
db = SqliteDatabase('test.db')

class InsertWidgetPanel(QWidget):
    def __init__(self, purchase_id, db_wind,role,user,changer ):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        self.role = role
        self.user = user
        self.changer = changer
        # Создаем лейблы
        self.setWindowTitle("Добавить НМЦК")
        self.setGeometry(100, 100, 900, 300)
        
        label1 = QLabel("Добавить НМЦК")
        label1.setAlignment(Qt.AlignCenter)
 
     
        button_NMCK_method_1= QPushButton("1.Добавить определение НМЦК методом сопоставимых рыночных цен")
        button_NMCK_method_2= QPushButton("2.Добавить определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информании")
        button_NMCK_method_3= QPushButton("3.Добавить определение НМЦК затратным методом")
        button_NMCK_method_4= QPushButton("4.Итоговое определение НМЦК с использованием нескольких методов")
        browse_button_NMCK= QPushButton("Добавить файл НМЦК")
        browse_button_izvesh= QPushButton("Добавить файл Извещения")
        browse_button_contract= QPushButton("Добавить файл Контрактов")
        browse_button_protocol= QPushButton("Добавить файл Протокол")
        # Создаем поля ввода
        browse_button_NMCK.clicked.connect(self.browse_file_NMCK)
        browse_button_izvesh.clicked.connect(self.browse_file_izvesh)
        browse_button_contract.clicked.connect(self.browse_file_contract)
        browse_button_protocol.clicked.connect(self.browse_file_protocol)
        # self.ContractFile = QLineEdit(self)
        
        button_style_pressed = """
        QPushButton:pressed {
            background-color: #C8C8C8;
        }
        """
        # Устанавливаем максимальную ширину для кнопок
        fixed_width = 800
        button_NMCK_method_1.setFixedWidth(fixed_width)
        button_NMCK_method_2.setFixedWidth(fixed_width)
        button_NMCK_method_3.setFixedWidth(fixed_width)
        button_NMCK_method_4.setFixedWidth(fixed_width)
        browse_button_NMCK.setFixedWidth(fixed_width)
        browse_button_izvesh.setFixedWidth(fixed_width)
        browse_button_contract.setFixedWidth(fixed_width)
        browse_button_protocol.setFixedWidth(fixed_width)
        button_NMCK_method_1.setStyleSheet("text-align: left;")
        button_NMCK_method_2.setStyleSheet("text-align: left;")
        button_NMCK_method_3.setStyleSheet("text-align: left;")
        button_NMCK_method_4.setStyleSheet("text-align: left;")
        browse_button_NMCK.setStyleSheet("text-align: left;")
        browse_button_izvesh.setStyleSheet("text-align: left;")
        browse_button_contract.setStyleSheet("text-align: left;")
        browse_button_protocol.setStyleSheet("text-align: left;")
        

        
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
        layout4 = QHBoxLayout(self)
        layout5 = QHBoxLayout(self)
        layout6 = QHBoxLayout(self)
        layout7 = QHBoxLayout(self)
        layout8 = QHBoxLayout(self)
        layout9 = QHBoxLayout(self)

        # Выравниваем кнопки налево
        layout2.addWidget(button_NMCK_method_1, alignment=Qt.AlignLeft)
        layout3.addWidget(button_NMCK_method_2, alignment=Qt.AlignLeft)
        layout4.addWidget(button_NMCK_method_3, alignment=Qt.AlignLeft)
        layout5.addWidget(button_NMCK_method_4, alignment=Qt.AlignLeft)
        layout6.addWidget(browse_button_NMCK, alignment=Qt.AlignLeft)
        layout7.addWidget(browse_button_izvesh, alignment=Qt.AlignLeft)
        layout8.addWidget(browse_button_contract, alignment=Qt.AlignLeft)
        layout9.addWidget(browse_button_protocol, alignment=Qt.AlignLeft)
        # Добавляем лейбл и поле ввода во вторую строку
        
        button_NMCK_method_1.clicked.connect(self.add_button_tkp_clicked)
        button_NMCK_method_2.clicked.connect(self.add_button_contract_clicked)
        button_NMCK_method_3.clicked.connect(self.add_button_cia_clicked)
        button_NMCK_method_4.clicked.connect(self.add_button_4_clicked)
       
 
        

        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(label1)
        self.layout1.addLayout(layout2)
        self.layout1.addLayout(layout3)
        self.layout1.addLayout(layout4)
        self.layout1.addLayout(layout5)
        self.layout1.addLayout(layout6)
        self.layout1.addLayout(layout7)
        self.layout1.addLayout(layout8)
        self.layout1.addLayout(layout9)

        
       
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout1)
        scroll_area.setWidget(scroll_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
    

    def add_button_tkp_clicked(self):
            self.tkp_shower = InsertWidgetNMCK(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.tkp_shower.setParent(self) 
            self.tkp_shower.show()
    
    def add_button_cia_clicked(self):   
            self.cia_shower = InsertWidgetNMCK_3(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.cia_shower.setParent(self)
            self.cia_shower.show()

    def add_button_contract_clicked(self):
            self.insert_cont = InsertWidgetNMCK_2(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.insert_cont.setParent(self)
            self.insert_cont.show()
    def add_button_4_clicked(self):

            self.insert_cont_4 = InsertWidgetNMCK_4(self.purchase_id, self.db_window,self.role,self.user,self.changer)
            # self.insert_cont_4.setParent(self)
            self.insert_cont_4.show()

    def browse_file_NMCK(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        self.db_folder = "файлы бд"
        
        if file_path:
            try:
                source_path = file_path
                # absolute_db_folder = os.path.abspath(self.db_folder)
                purchase = Purchase.get(Purchase.Id == self.purchase_id)
                purchase_folder = os.path.join(self.db_folder, str(purchase.RegistryNumber))
                if not os.path.exists(purchase_folder):
                    os.makedirs(purchase_folder)
                # destination_path = os.path.join(absolute_db_folder, os.path.basename(source_path))
                destination_path_1 = os.path.join(purchase_folder, os.path.basename(source_path))
                destination_path = os.path.basename(destination_path_1)
                shutil.copy2(source_path, destination_path)
            except:
                pass
            try:
                Purchase.update(nmck_file=destination_path if destination_path else "нет данных").where(Purchase.Id == self.purchase_id).execute()
                db.close()
                self.updateLog(destination_path)
                self.changer.populate_table()
                self.db_window.reload_data_id(self.purchase_id)
                self.db_window.show_current_purchase()
                # Выводим сообщение об успешном сохранении
                self.show_message("Успех", "Данные успешно добавлены")
            except Exception as e:
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")

    def browse_file_izvesh(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        self.db_folder = "файлы бд"
        
        if file_path:
            try:
                source_path = file_path
                purchase = Purchase.get(Purchase.Id == self.purchase_id)
                purchase_folder = os.path.join(self.db_folder, str(purchase.RegistryNumber))

                # Создаем папку, если ее нет
                if not os.path.exists(purchase_folder):
                    os.makedirs(purchase_folder)

                # Определяем путь для копирования файла
                destination_path_1 = os.path.join(purchase_folder, os.path.basename(source_path))
                destination_path = os.path.basename(destination_path_1)

                # Копируем файл
                shutil.copy2(source_path, destination_path_1)
            except:
                pass
            try:
                Purchase.update(notification_link=destination_path if destination_path else "нет данных").where(Purchase.Id == self.purchase_id).execute()
                self.updateLog(destination_path)
                self.changer.populate_table()
                self.db_window.reload_data_id(self.purchase_id)
                self.db_window.show_current_purchase()
                db.close()
                # Выводим сообщение об успешном сохранении
                self.show_message("Успех", "Данные успешно добавлены")
            except Exception as e:
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")

    def browse_file_contract(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        self.db_folder = "файлы бд"
        
        if file_path:
            try:
               
                source_path = file_path
                purchase = Purchase.get(Purchase.Id == self.purchase_id)
                purchase_folder = os.path.join(self.db_folder, str(purchase.RegistryNumber))
                if not os.path.exists(purchase_folder):
                    os.makedirs(purchase_folder)
                # destination_path = os.path.join(absolute_db_folder, os.path.basename(source_path))
                destination_path_1 = os.path.join(purchase_folder, os.path.basename(source_path))
                destination_path = os.path.basename(destination_path_1)
                shutil.copy2(source_path, destination_path)
            except:
                pass
            try:
                try:
                    Contract.get(Contract.purchase == self.purchase_id)
                    Contract.update(ContractFile= destination_path if destination_path else "нет данных").where(Contract.purchase == self.purchase_id).execute()
                    self.updateLog(destination_path)
                    self.changer.populate_table()
                    db.close()
                    self.db_window.reload_data_id(self.purchase_id)
                    self.db_window.show_current_purchase()
                    self.show_message("Успех", "Данные успешно добавлены")
                except :
                    
                    # Contract.create( purchase = self.purchase_id,ContractFile= destination_path if destination_path else "нет данных")
         
                    self.show_message("Внимание", "Невозможно добавить файл контракта, когда не внесены данные по контракту")
            except Exception as e:
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")

    def browse_file_protocol(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        self.db_folder = "файлы бд"
        
        if file_path:
            try:
                source_path = file_path
                purchase = Purchase.get(Purchase.Id == self.purchase_id)
                purchase_folder = os.path.join(self.db_folder, str(purchase.RegistryNumber))
                if not os.path.exists(purchase_folder):
                    os.makedirs(purchase_folder)
                # destination_path = os.path.join(absolute_db_folder, os.path.basename(source_path))
                destination_path_1 = os.path.join(purchase_folder, os.path.basename(source_path))
                destination_path = os.path.basename(destination_path_1)
                shutil.copy2(source_path, destination_path)
            except:
                pass
            try:
                Purchase.update(protocol_file=destination_path if destination_path else "нет данных").where(Purchase.Id == self.purchase_id).execute()
                db.close()
                self.db_window.reload_data_id(self.purchase_id)
                self.db_window.show_current_purchase()
                self.updateLog(destination_path)
                self.changer.populate_table()
                # Выводим сообщение об успешном сохранении
                self.show_message("Успех", "Данные успешно добавлены")
            except Exception as e:
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")

    
    def updateLog(self,destination_path):
        purchase = Purchase.get(Purchase.Id == self.purchase_id)
                
       
        changed_date = ChangedDate(
            RegistryNumber=purchase.RegistryNumber,
            username=self.user,
            chenged_time=datetime.datetime.now(),
            PurchaseName=purchase.PurchaseName,
            Role=self.role,
            Type=f'Добавлен файл {destination_path}'
        )
        changed_date.save()    
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
        
