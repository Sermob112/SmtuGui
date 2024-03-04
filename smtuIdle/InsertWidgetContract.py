from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Contract, ChangedDate,Purchase
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
import os
import shutil
from peewee import DoesNotExist
import datetime
db = SqliteDatabase('test.db')

class InsertWidgetContract(QWidget):
    def __init__(self, purchase_id,db_wind,role,user,changer):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        self.role = role
        self.user = user
        self.changer = changer
        # Создаем лейблы
        self.setWindowTitle("Результаты закупки")
        self.setGeometry(100, 100, 900, 200)
        
        label1 = QLabel("Результаты закупки")
        label1.setAlignment(Qt.AlignCenter)
        label2 = QLabel("Количество заявок на участие в закупке:")
        label3 = QLabel("Количество допущенных заявок на участие в закупке:")
        label4 = QLabel("Количество отклоненных заявок на участие в закупке:")
    
       
        # label17 = QLabel("Договор:")

        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit1.setValidator(QIntValidator(QIntValidator(1, 1, self)))
        self.edit1.textChanged.connect(self.update_fields)
        self.edit2 = QLineEdit(self)
        self.edit2.setValidator(QIntValidator())
        self.edit3 = QLineEdit(self)
        self.edit3.setValidator(QIntValidator())


        # self.ContractFile = QLineEdit(self)
      

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)

   

        # layout17 = QHBoxLayout(self)
        # self.notification_link_edit_contratc = QLineEdit()
        # browse_button_contratc = QPushButton("Обзор")
        # browse_button_contratc.clicked.connect(self.browse_file_contract)
        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layout3.addWidget(label3)
        layout3.addWidget(self.edit2)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label4)
        layout4.addWidget(self.edit3)





        # layout17.addWidget(label17)
        # layout17.addWidget(self.notification_link_edit_contratc)
        # layout17.addWidget(browse_button_contratc)

        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(label1)
        self.layout1.addLayout(layout2)
        self.layout1.addLayout(layout3)
        self.layout1.addLayout(layout4)




        # self.layout1.addLayout(layout17)
       
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout1)
        scroll_area.setWidget(scroll_widget)
      
        self.form_layout = QVBoxLayout ()
        self.layout1.addLayout(self.form_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
    
    def update_fields(self):
         # Очищаем форму от предыдущих полей
        self.clear_layout(self.form_layout)
      
     
        num_fields = int(self.edit1.text())
        if num_fields > 10:
            num_fields = 10
        elif num_fields < 0:
            num_fields = 1
        
        #Создаем и добавляем новые поля ввода в форму
        for i in range(num_fields ):
            label = QLabel(f"Ценовое предложение №{i + 1}:")
            edit = QLineEdit(self)
            edit.setValidator(QIntValidator())
            self.form_layout.addWidget(label)
            self.form_layout.addWidget(edit)
            label2 = QLabel(f"Заявитель №{i + 1}:")
            edit2 = QLineEdit(self)
            self.form_layout.addWidget(label2)
            self.form_layout.addWidget(edit2)

            label3 = QLabel(f"Статус заявителя №{i + 1}:")
            edit3 = QLineEdit(self)
            self.form_layout.addWidget(label3)
            self.form_layout.addWidget(edit3)
        
        # print(self.form_layout.count())
        self.add_tkp_button = QPushButton("Добавить Данные")
        self.form_layout.addWidget(self.add_tkp_button)

        self.add_tkp_button.clicked.connect(self.save_tkp_data)
        self.update()
    def clear_layout(self,layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
    def save_tkp_data(self):
        # self.db_folder = "файлы бд"
        
        # os.makedirs(self.db_folder, exist_ok=True)
        self.price_proposal = {}
        self.applicant = {}
        self.status = {}
        
        j = 1
        total_elements = self.form_layout.count()
        
        for i in range(0, total_elements - 1, 6):  # Учитывает 3 виджета для ценового предложения и 3 виджета для заявителя
            price_proposal_edit = self.form_layout.itemAt(i + 1).widget()

            if price_proposal_edit:
                key_price = f"Ценовое предложение №{j}"
                self.price_proposal[key_price] = int(price_proposal_edit.text()) if price_proposal_edit.text() else "[]"

            applicant_edit = self.form_layout.itemAt(i + 3).widget()
            if applicant_edit:
                key_applicant = f"Заявитель №{j}"
                self.applicant[key_applicant] = applicant_edit.text() if applicant_edit.text() else "[]"

            status_edit = self.form_layout.itemAt(i + 5).widget()
            if status_edit:
                key_status = f"Статус заявителя №{j}"
                self.status[key_status] = status_edit.text() if status_edit.text() else "[]"

            j += 1
        # try:
        #     source_path_contract = self.notification_link_edit_contratc.text()
        #     absolute_db_folder = os.path.abspath(self.db_folder)
        
        #     destination_path_contract = os.path.join(absolute_db_folder, os.path.basename(source_path_contract))
        #     shutil.copy2(source_path_contract, destination_path_contract)
        # except:
        #     pass
        price_proposal_json = json.dumps(self.price_proposal,ensure_ascii=False)
        applicant_json = json.dumps(self.applicant,ensure_ascii=False)
        status_json = json.dumps(self.status,ensure_ascii=False)
        try:
            Contract.get(Contract.purchase == self.purchase_id)
            Contract.update(
                                TotalApplications=int(self.edit1.text()) if self.edit1.text() else 0,
                                AdmittedApplications=int(self.edit2.text()) if self.edit2.text() else 0,
                                RejectedApplications=int(self.edit3.text()) if self.edit3.text() else 0,
                                
                          
                                # ContractFile= destination_path_contract if destination_path_contract else "нет данных",
                                PriceProposal=price_proposal_json, Applicant=applicant_json, Applicant_satatus=status_json).where(Contract.purchase == self.purchase_id).execute()
        except DoesNotExist:
                Contract.create( purchase = self.purchase_id,

                TotalApplications=int(self.edit1.text()) if self.edit1.text() else 0,
                                AdmittedApplications=int(self.edit2.text()) if self.edit2.text() else 0,
                                RejectedApplications=int(self.edit3.text()) if self.edit3.text() else 0,

                                # ContractFile= destination_path_contract if destination_path_contract else "нет данных",
                                PriceProposal=price_proposal_json, Applicant=applicant_json, Applicant_satatus=status_json)
        try:
            # Попытка сохранения данных
            self.db_window.reload_data_id(self.purchase_id)
            self.db_window.show_current_purchase()
            self.updateLog()
            self.changer.populate_table()
            db.close()

            # Выводим сообщение об успешном сохранении
            self.show_message("Успех", "Данные успешно добавлены")

        except Exception as e:
            # Выводим сообщение об ошибке
            self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")
        # print("ТКПData сохранены:", tkp_json)
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
            Type=f'Добавлены данные по закупкам'
        )
        changed_date.save()
    # def browse_file_contract(self):
    #     file_dialog = QFileDialog()
    #     file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
    #     if file_path:
    #         self.notification_link_edit_contratc.setText(file_path)
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetContract(3)
#     window.show()
#     sys.exit(app.exec())
        
