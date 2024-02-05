from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Contract,Purchase
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
import shutil
import os
from peewee import DoesNotExist
db = SqliteDatabase('test.db')

class InsertWidgetContract(QWidget):
    def __init__(self, purchase_id,db_wind):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        # Создаем лейблы
        self.setWindowTitle("Окно ввода даных Контрактов")
        self.setGeometry(100, 100, 1000, 800)
        main_layout = QVBoxLayout(self)
        self.layout1 = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
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
        #Контракт
        label1 = QLabel("2.Расчет НМЦК методом использования общедоступной информации")
        label1.setAlignment(Qt.AlignCenter)
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
        self.edit1 = QLineEdit()
        self.edit1.setValidator(QIntValidator())
        self.edit1.textChanged.connect(self.update_fields)
        self.edit2 = QLineEdit()
        self.edit2.setValidator(QIntValidator())
        self.edit3 = QLineEdit()
        self.edit3.setValidator(QIntValidator())
        self.WinnerExecutor = QLineEdit()
        self.ContractingAuthority = QLineEdit()
        self.ContractIdentifier = QLineEdit()
        self.RegistryNumber = QLineEdit()
        self.ContractNumber = QLineEdit()
        self.StartDate = QDateEdit()
        self.StartDate.setCalendarPopup(True)
        self.EndDate = QDateEdit()
        self.EndDate.setCalendarPopup(True)
        self.ContractPrice = QLineEdit()
        self.ContractPrice.setValidator(QIntValidator())
        self.AdvancePayment = QLineEdit()
        self.AdvancePayment.setValidator(QDoubleValidator())
        self.ReductionNMC = QLineEdit()
        self.ReductionNMC.setValidator(QIntValidator())
        self.ReductionNMCPercent = QLineEdit()
        self.ReductionNMCPercent.setValidator(QDoubleValidator())
        self.SupplierProtocol = QLineEdit()
        self.ContractFile = QLineEdit()
           #файл диалог
        self.notification_link_edit_contratc = QLineEdit()
        browse_button_contratc = QPushButton("Обзор")
        browse_button_contratc.clicked.connect(self.browse_file_contract)

       
      

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
        layout17.addWidget(self.notification_link_edit_contratc)
        layout17.addWidget(browse_button_contratc)
         #НМЦК -ТКП
        labelNMCK1 = QLabel("1. Расчет НМЦК затратным методом")
        labelNMCK1.setAlignment(Qt.AlignCenter)
        labelNMCK2 = QLabel("Количество запросов ТКП:")
        labelNMCK3 = QLabel("Количество ответов ТКП:")
        labelNMCK4 = QLabel("Лимит финансирования, руб.:")
        labelNMCK5 = QLabel("Выбирите файл извещения о закупке")
         #файл диалог
        self.notification_link_edit = QLineEdit(self)
        browse_button = QPushButton("Обзор", self)
        browse_button.clicked.connect(self.browse_file)
        #  Создаем поля ввода
        self.editNMCK1 = QLineEdit()
        self.editNMCK1.setValidator(QIntValidator())
        self.editNMCK1.textChanged.connect(self.update_fields_nmck)
        self.editNMCK2 = QLineEdit()
        self.editNMCK2.setValidator(QIntValidator())
        self.editNMCK3 = QLineEdit()
        self.editNMCK3.setValidator(QIntValidator())

    
        layoutNMCK2 = QHBoxLayout(self)
        layoutNMCK3 = QHBoxLayout(self)
        layoutNMCK4 = QHBoxLayout(self)
        layoutNMCK5 = QHBoxLayout(self)
           # Добавляем лейбл и поле ввода в первую строку
        layoutNMCK2.addWidget(labelNMCK2)
        layoutNMCK2.addWidget(self.editNMCK1)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layoutNMCK3.addWidget(labelNMCK3)
        layoutNMCK3.addWidget(self.editNMCK2)

        # # Добавляем лейбл и поле ввода в третью строку
        layoutNMCK4.addWidget(labelNMCK4)
        layoutNMCK4.addWidget(self.editNMCK3)
        layoutNMCK5.addWidget(labelNMCK5)
        layoutNMCK5.addWidget(self.notification_link_edit)
        layoutNMCK5.addWidget(browse_button)
        self.form_layout_NMCK = QVBoxLayout()
        # Добавляем все строки в вертикальный контейнер NMCK
        self.layout1.addWidget(labelNMCK1)
        self.layout1.addLayout(layoutNMCK2)
        self.layout1.addLayout(layoutNMCK3)
        self.layout1.addLayout(layoutNMCK4)
        self.layout1.addLayout(layoutNMCK5)
        self.layout1.addLayout(self.form_layout_NMCK)
        # Добавляем все строки в вертикальный контейнер COntract
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
        
        self.form_layout = QVBoxLayout ()
        self.layout1.addLayout(self.form_layout)
        self.add_tkp_button = QPushButton("Добавить Данные")
        self.form_layout.addWidget(self.add_tkp_button)
        self.add_tkp_button.clicked.connect(self.save_tkp_data)
       
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout1)
        scroll_area.setWidget(scroll_widget)


       

        # self.form_layout = QVBoxLayout ()
        # self.layout1.addLayout(self.form_layout)
        # self.add_tkp_button = QPushButton("Добавить Данные")
        # self.form_layout.addWidget(self.add_tkp_button)

        # self.add_tkp_button.clicked.connect(self.save_tkp_data)
        
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
    def update_fields_nmck(self):
        num_fields = int(self.editNMCK1.text())
        if num_fields > 10:
            num_fields = 10
        elif num_fields <= 1:
            num_fields = 2

        # Удаляем все существующие поля ввода из формы
        self.clear_layout(self.form_layout_NMCK)

        # Создаем и добавляем новые поля ввода в форму
        for i in range(num_fields):
            labelNMCK = QLabel(f"Ценовое предложение №{i + 1}:")
            editNMCK = QLineEdit(self)
            editNMCK.setValidator(QIntValidator())
            self.form_layout_NMCK.addWidget(labelNMCK)
            self.form_layout_NMCK.addWidget(editNMCK)
            # key = f"ТКП {i + 1}"
            # self.tkp_data[key] = int(edit.text()) if edit.text() else 0
        # self.add_tkp_button = QPushButton("Добавить ТКП")
        # self.form_layout_NMCK.addWidget(self.add_tkp_button)
        # self.add_tkp_button.clicked.connect(self.save_tkp_data)
        self.update()
    def save_tkp_data(self):
        # TKP
        self.db_folder = "файлы бд"
        os.makedirs(self.db_folder, exist_ok=True)
        self.tkp_data = {}

        # Заполняем словарь данными из динамических полей
        for i in range(0,self.form_layout_NMCK.count() - 1,2):  # -1, чтобы не включать кнопку
            key = f"ТКП {i}"
            edit = self.form_layout_NMCK.itemAt(i+1).widget()
            self.tkp_data[key] = int(edit.text()) if edit.text() else 0

        tkp_json = json.dumps(self.tkp_data,ensure_ascii=False)
        tkp_values_all = [int(value) for value in  self.tkp_data.values()]
        if tkp_values_all:
                
                max_tkp = max(tkp_values_all)
                min_tkp = min(tkp_values_all)
                avg_tkp = sum(tkp_values_all) / len(tkp_values_all) 
                standard_deviation = statistics.stdev(tkp_values_all) 
                cv = (standard_deviation / avg_tkp) * 100 
        else:
    # Set default values if tkp_values_all is empty or None
            max_tkp = min_tkp = avg_tkp = standard_deviation = cv = 0
        try:
            source_path = self.notification_link_edit.text()
            absolute_db_folder = os.path.abspath(self.db_folder)
        
            destination_path = os.path.join(absolute_db_folder, os.path.basename(source_path))
            shutil.copy2(source_path, destination_path)
        except:
            pass

        # Сохранение пути файла в базе данных
       
        purchase = Purchase.update(
                            TKPData=tkp_json,
                            QueryCount=int(self.editNMCK1.text()) if self.editNMCK1.text() else 0,
                            ResponseCount=int(self.editNMCK2.text()) if self.editNMCK2.text() else 0,
                            FinancingLimit=int(self.editNMCK3.text()) if self.editNMCK3.text() else 0,
                            
                            AveragePrice = avg_tkp if avg_tkp else 0,
                            
                            MinPrice = min_tkp if min_tkp else 0,
                            MaxPrice = max_tkp if max_tkp else 0,
                            StandardDeviation = standard_deviation if standard_deviation else 0,
                            CoefficientOfVariation = cv if cv else 0,
                            NMCKMarket = avg_tkp if avg_tkp else 0,
                            notification_link=destination_path if destination_path else "нет данных",
                            ).where(Purchase.Id == self.purchase_id)
        #Контракты
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
        try:
            source_path_contract = self.notification_link_edit_contratc.text()
            absolute_db_folder = os.path.abspath(self.db_folder)
        
            destination_path_contract = os.path.join(absolute_db_folder, os.path.basename(source_path_contract))
            shutil.copy2(source_path_contract, destination_path_contract)
        except:
            pass
        price_proposal_json = json.dumps(self.price_proposal,ensure_ascii=False)
        applicant_json = json.dumps(self.applicant,ensure_ascii=False)
        status_json = json.dumps(self.status,ensure_ascii=False)
        try:
            contract = Contract.get(Contract.Id == self.purchase_id)
            contract = Contract.update(
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
                                ContractFile= destination_path_contract if destination_path_contract else "нет данных",
                                PriceProposal=price_proposal_json, Applicant=applicant_json, Applicant_satatus=status_json).where(Contract.Id == self.purchase_id).execute()
        except DoesNotExist:
                contract = Contract.create( purchase = self.purchase_id,

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
                                ContractFile= destination_path_contract if destination_path_contract else "нет данных",
                                PriceProposal=price_proposal_json, Applicant=applicant_json, Applicant_satatus=status_json)
        try:
            # Попытка сохранения данных
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
    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
  
    def browse_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
        if file_path:
            self.notification_link_edit.setText(file_path)
            

    def browse_file_contract(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
        if file_path:
            self.notification_link_edit_contratc.setText(file_path)
            

  
       

       
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetContract(3)
#     window.show()
#     sys.exit(app.exec())
        
