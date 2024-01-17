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
        self.setWindowTitle("Окно ввода даных Контрактов")
        self.setGeometry(100, 100, 600, 400)
        
        label1 = QLabel("Ввод данных по заявкам")
        label2 = QLabel("Количество заявок на участие в закупке:")
        label3 = QLabel("Количество допущенных заявок на участие в закупке:")
        label4 = QLabel("Количество отклоненных заявок на участие в закупке:")
        label5 = QLabel("Победитель-исполнитель контракта:")
        label6 = QLabel("Заказчик по контракту:")
        label7 = QLabel("Идентификатор договора:")
        label8 = QLabel("Реестровый номер договора:")
        label9 = QLabel("№ договора:")
        label10 = QLabel("Дата начала/подписания:")
        label11 = QLabel("Дата окончания/исполнения:")
        label12 = QLabel("Цена договора, руб.:")
        label13 = QLabel("Размер авансирования, руб./(%)")
        label14 = QLabel("Снижение НМЦК, руб.:")
        label15 = QLabel("Снижение НМЦК, %:")
        label16 = QLabel("Протоколы определения поставщика (выписка):")
        label17 = QLabel("Договор:")

        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit1.setValidator(QIntValidator(QIntValidator(1, 1, self)))
        self.edit1.textChanged.connect(self.update_fields)
        self.edit2 = QLineEdit(self)
        self.edit2.setValidator(QIntValidator())
        self.edit3 = QLineEdit(self)
        self.edit3.setValidator(QIntValidator())
        self.WinnerExecutor = QLineEdit(self)
        self.ContractingAuthority = QLineEdit(self)
        self.ContractIdentifier = QLineEdit(self)
        self.RegistryNumber = QLineEdit(self)
        self.ContractNumber = QLineEdit(self)
        self.StartDate = QDateEdit(self)
        self.EndDate = QDateEdit(self)
        self.ContractPrice = QLineEdit(self)
        self.ContractPrice.setValidator(QIntValidator())
        self.AdvancePayment = QLineEdit(self)
        self.AdvancePayment.setValidator(QDoubleValidator())
        self.ReductionNMC = QLineEdit(self)
        self.ReductionNMC.setValidator(QIntValidator())
        self.ReductionNMCPercent = QLineEdit(self)
        self.ReductionNMCPercent.setValidator(QDoubleValidator())
        self.SupplierProtocol = QLineEdit(self)
        self.ContractFile = QLineEdit(self)
      

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
        layout5 = QHBoxLayout(self)
        layout6 = QHBoxLayout(self)
        layout7 = QHBoxLayout(self)
        layout8 = QHBoxLayout(self)
        layout9 = QHBoxLayout(self)
        layout10 = QHBoxLayout(self)
        layout11 = QHBoxLayout(self)
        layout12 = QHBoxLayout(self)
        layout13 = QHBoxLayout(self)
        layout14 = QHBoxLayout(self)
        layout15 = QHBoxLayout(self)
        layout16 = QHBoxLayout(self)
        layout17 = QHBoxLayout(self)

        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layout3.addWidget(label3)
        layout3.addWidget(self.edit2)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label4)
        layout4.addWidget(self.edit3)

        layout5.addWidget(label5)
        layout5.addWidget(self.WinnerExecutor)

        layout6.addWidget(label6)
        layout6.addWidget(self.ContractingAuthority)

        layout7.addWidget(label7)
        layout7.addWidget(self.ContractIdentifier)

        layout7.addWidget(label8)
        layout7.addWidget(self.RegistryNumber)

        layout8.addWidget(label9)
        layout8.addWidget(self.ContractNumber)
        
        layout9.addWidget(label10)
        layout9.addWidget(self.StartDate)

        layout11.addWidget(label11)
        layout11.addWidget(self.EndDate)

        layout12.addWidget(label12)
        layout12.addWidget(self.ContractPrice)

        layout13.addWidget(label13)
        layout13.addWidget(self.AdvancePayment)

        layout14.addWidget(label14)
        layout14.addWidget(self.ReductionNMC)

        layout15.addWidget(label15)
        layout15.addWidget(self.ReductionNMCPercent)

        layout16.addWidget(label16)
        layout16.addWidget(self.SupplierProtocol)

        layout17.addWidget(label17)
        layout17.addWidget(self.ContractFile)

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
        self.layout1.addLayout(layout10)
        self.layout1.addLayout(layout11)
        self.layout1.addLayout(layout12)
        self.layout1.addLayout(layout13)
        self.layout1.addLayout(layout14)
        self.layout1.addLayout(layout15)
        self.layout1.addLayout(layout16)
        self.layout1.addLayout(layout17)

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
                            WinnerExecutor=self.WinnerExecutor.text() if self.WinnerExecutor.text() else 0,
                            ContractingAuthority=self.ContractingAuthority.text() if self.ContractingAuthority.text() else 0,
                            ContractIdentifier=self.ContractIdentifier.text() if self.ContractIdentifier.text() else 0,
                            RegistryNumber=self.RegistryNumber.text() if self.RegistryNumber.text() else 0,
                            ContractNumber=self.ContractNumber.text() if self.ContractNumber.text() else 0,
                            StartDate=self.StartDate.text() if self.StartDate.text() else 0,
                            EndDate=self.EndDate.text() if self.EndDate.text() else 0,
                            ContractPrice=int(self.ContractPrice.text()) if self.ContractPrice.text() else 0,
                            AdvancePayment=float(self.AdvancePayment.text()) if self.AdvancePayment.text() else 0,
                            ReductionNMC=int(self.ReductionNMC.text()) if self.ReductionNMC.text() else 0,
                            ReductionNMCPercent=float(self.ReductionNMCPercent.text()) if self.ReductionNMCPercent.text() else 0,
                            SupplierProtocol=self.SupplierProtocol.text() if self.SupplierProtocol.text() else 0,
                            ContractFile=self.ContractFile.text() if self.ContractFile.text() else 0,
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
#     window = InsertWidgetContract(3)
#     window.show()
#     sys.exit(app.exec())
        
