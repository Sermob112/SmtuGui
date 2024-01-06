from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Contract
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
db = SqliteDatabase('test.db')

class InsertWidgetContract(QWidget):
    def __init__(self, purchase_id):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        # Создаем лейблы
        label1 = QLabel("Ввод данных по заявкам")
        label2 = QLabel("Количество заявок на участие в закупке:")
        label3 = QLabel("Количество допущенных заявок на участие в закупке:")
        label4 = QLabel("Количество отклоненных заявок на участие в закупке:")
      

        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit1.setValidator(QIntValidator())
        self.edit1.textChanged.connect(self.update_fields)
        self.edit2 = QLineEdit(self)
        self.edit2.setValidator(QIntValidator())
        self.edit3 = QLineEdit(self)
        self.edit3.setValidator(QIntValidator())

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
    
        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layout3.addWidget(label3)
        layout3.addWidget(self.edit2)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label4)
        layout4.addWidget(self.edit3)

        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(label1)
        self.layout1.addLayout(layout2)
        self.layout1.addLayout(layout3)
        self.layout1.addLayout(layout4)
       
        self.form_layout = QVBoxLayout ()
        self.layout1.addLayout(self.form_layout)

        self.setLayout(self.layout1)
    
    def update_fields(self):
         # Очищаем форму от предыдущих полей
        self.clear_layout(self.form_layout)
      
     
        num_fields = int(self.edit1.text())
        
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
        
        print(self.form_layout.count())
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
        price_proposal_json = json.dumps(self.price_proposal,ensure_ascii=False)
        applicant_json = json.dumps(self.applicant,ensure_ascii=False)
        status_json = json.dumps(self.status,ensure_ascii=False)
        contract = Contract(purchase=self.purchase_id,
                            TotalApplications=int(self.edit1.text()) if self.edit1.text() else 0,
                            AdmittedApplications=int(self.edit2.text()) if self.edit2.text() else 0,
                            RejectedApplications=int(self.edit3.text()) if self.edit3.text() else 0,
                            
                            PriceProposal=price_proposal_json, Applicant=applicant_json, Applicant_satatus=status_json)
       
        try:
            # Попытка сохранения данных
            contract.save()
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

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetContract()
#     window.show()
#     sys.exit(app.exec())
        
