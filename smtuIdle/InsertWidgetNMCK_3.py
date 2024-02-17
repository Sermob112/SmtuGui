from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase,ChangedDate
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
import shutil
import os
import datetime
db = SqliteDatabase('test.db')

class InsertWidgetNMCK_3(QWidget):
    def __init__(self,purchase_id,db_wind,role,user,changer):
        
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        self.role = role
        self.user = user
        self.changer = changer
        self.setWindowTitle("3.Определение НМЦК затратным методом")
        self.setGeometry(100, 100, 600, 200)
        # Создаем лейблы
        label1 = QLabel("3. Ввод данных - Определение НМЦК затратным методом")
        label1.setAlignment(Qt.AlignCenter)
        label2 = QLabel("Наименование организации, производившей расчет")
        label3 = QLabel("Дата расчета")
         
        
        labelNMCK5 = QLabel("Выбирите файл")
        #файл диалог
        self.notification_link_edit = QLineEdit(self)
        browse_button = QPushButton("Обзор", self)
        browse_button.clicked.connect(self.browse_file)
        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit2 = QDateEdit(self)
        self.edit2.setCalendarPopup(True)
        # self.edit3 = QLineEdit(self)
        # self.edit3.setValidator(QIntValidator())

        layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
        # layout5 = QHBoxLayout(self)

        # Добавляем лейбл и поле ввода в первую строку
        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        layout3.addWidget(label3)
        layout3.addWidget(self.edit2)

    
        layout4.addWidget(labelNMCK5)
        layout4.addWidget(self.notification_link_edit)
        layout4.addWidget(browse_button)
        # Добавляем все строки в вертикальный контейнер
        layout1.addWidget(label1)
        layout1.addLayout(layout2)
        layout1.addLayout(layout3)
        layout1.addLayout(layout4)
        # layout1.addLayout(layout5)

        self.form_layout = QVBoxLayout()
        layout1.addLayout(self.form_layout)
        self.add_tkp_button = QPushButton("Добавить Данные")
        self.add_tkp_button.clicked.connect(self.save_tkp_data)
        self.form_layout.addWidget(self.add_tkp_button)
        self.setLayout(layout1)
    # def browse_file(self):
    #     file_dialog = QFileDialog()
    #     file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
    #     if file_path:
    #         self.notification_link_edit.setText(file_path)

    # def update_fields(self):
    #      # Очищаем форму от предыдущих полей
    #     self.clear_layout(self.form_layout)
      
     
    #     num_fields = int(self.edit1.text())
    #     if num_fields > 10:
    #         num_fields = 10
    #     elif num_fields < 0:
    #         num_fields = 1
        
    #     #Создаем и добавляем новые поля ввода в форму
    #     for i in range(num_fields ):
    #         label = QLabel(f"Цена судна приведенная к уровню цен года его поставки №{i + 1}:")
    #         edit = QLineEdit(self)
    #         edit.setValidator(QIntValidator())
    #         self.form_layout.addWidget(label)
    #         self.form_layout.addWidget(edit)
    #         label2 = QLabel(f"Цена судна приведенная к уровню цен первого года периода строительства судна №{i + 1}:")
    #         edit2 = QLineEdit(self)
    #         self.form_layout.addWidget(label2)
    #         self.form_layout.addWidget(edit2)

    #         label3 = QLabel(f"Цена судна приведенная к уровню цен текущих лет на периода строительства судна №{i + 1}:")
    #         edit3 = QLineEdit(self)
    #         self.form_layout.addWidget(label3)
    #         self.form_layout.addWidget(edit3)
        
    #     print(self.form_layout.count())
    #     self.add_tkp_button = QPushButton("Добавить Данные")
    #     self.form_layout.addWidget(self.add_tkp_button)

    #     self.add_tkp_button.clicked.connect(self.save_tkp_data)
    #     self.update()
    def browse_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
        if file_path:
            self.notification_link_edit.setText(file_path)
    def save_tkp_data(self):
        self.db_folder = "файлы бд"
        os.makedirs(self.db_folder, exist_ok=True)
        try:
            source_path = self.notification_link_edit.text()
            absolute_db_folder = os.path.abspath(self.db_folder)
        
            destination_path = os.path.join(absolute_db_folder, os.path.basename(source_path))
            shutil.copy2(source_path, destination_path)
        except:
            pass
     
        
        purchase = Purchase.update(
                            
                            
                            organization_name = self.edit1.text() if self.edit1.text() else 0,
                            organization_name_date = self.edit2.text() if self.edit2.text() else 0,
                            organization_name_file = destination_path
                            # ResponseCount=int(self.edit2.text()) if self.edit2.text() else 0,
                            # FinancingLimit=int(self.edit3.text()) if self.edit3.text() else 0,
                            # AveragePrice = avg_tkp if avg_tkp else 0,
                            # MinPrice = min_tkp if min_tkp else 0,
                            # MaxPrice = max_tkp if max_tkp else 0,
                            # StandardDeviation = standard_deviation if standard_deviation else 0,
                            # CoefficientOfVariation = cv if cv else 0,
                            # NMCKMarket = avg_tkp if avg_tkp else 0,
                            # notification_link=destination_path if destination_path else "нет данных",
                            ).where(Purchase.Id == self.purchase_id)
        try:
            # Попытка сохранения данных
            self.updateLog()
            self.changer.populate_table()
            purchase.execute()
        
            db.close()
            self.db_window.reload_data_id(self.purchase_id)
            self.db_window.show_current_purchase()
            # Выводим сообщение об успешном сохранении
            self.show_message("Успех", "Данные успешно добавлены")

        except Exception as e:
            # Выводим сообщение об ошибке
            self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")
        # print("ТКПData сохранены:", tkp_json)
    def clear_layout(self,layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    def updateLog(self):
        purchase = Purchase.get(Purchase.Id == self.purchase_id)
                
       
        changed_date = ChangedDate(
            RegistryNumber=purchase.RegistryNumber,
            username=self.user,
            chenged_time=datetime.datetime.now(),
            PurchaseName=purchase.PurchaseName,
            Role=self.role,
            Type=f'Добавлены данные по Определение НМЦК затратным методом'
        )
        changed_date.save()
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetNMCK()
#     window.show()
#     sys.exit(app.exec())
        
