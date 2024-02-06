from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
import shutil
import os
db = SqliteDatabase('test.db')

class InsertWidgetNMCK_2(QWidget):
    def __init__(self,purchase_id,db_wind):
        
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.db_window = db_wind
        self.setWindowTitle("2.Определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информании")
        self.setGeometry(100, 100, 600, 200)
        # Создаем лейблы
        label1 = QLabel("2. Ввод данных - Метод сопоставимых рыночных цен (анализ рынка)")
        label1.setAlignment(Qt.AlignCenter)
        label2 = QLabel("Количество контрактов :")
        
        # labelNMCK5 = QLabel("Выбирите файл извещения о закупке")
        #файл диалог
        # self.notification_link_edit = QLineEdit(self)
        # browse_button = QPushButton("Обзор", self)
        # browse_button.clicked.connect(self.browse_file)
        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit1.setValidator(QIntValidator())
        self.edit1.textChanged.connect(self.update_fields)
        # self.edit2 = QLineEdit(self)
        # self.edit2.setValidator(QIntValidator())
        # self.edit3 = QLineEdit(self)
        # self.edit3.setValidator(QIntValidator())

        layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        # layout3 = QHBoxLayout(self)
        # layout4 = QHBoxLayout(self)
        # layout5 = QHBoxLayout(self)

        # Добавляем лейбл и поле ввода в первую строку
        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        

    
        # layout5.addWidget(labelNMCK5)
        # layout5.addWidget(self.notification_link_edit)
        # layout5.addWidget(browse_button)
        # Добавляем все строки в вертикальный контейнер
        layout1.addWidget(label1)
        layout1.addLayout(layout2)
        # layout1.addLayout(layout3)
        # layout1.addLayout(layout4)
        # layout1.addLayout(layout5)

        self.form_layout = QVBoxLayout()
        layout1.addLayout(self.form_layout)

        self.setLayout(layout1)
    # def browse_file(self):
    #     file_dialog = QFileDialog()
    #     file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf)")
        
    #     if file_path:
    #         self.notification_link_edit.setText(file_path)

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
            label = QLabel(f"Цена судна приведенная к уровню цен года его поставки №{i + 1}:")
            edit = QLineEdit(self)
            edit.setValidator(QIntValidator())
            self.form_layout.addWidget(label)
            self.form_layout.addWidget(edit)
            label2 = QLabel(f"Цена судна приведенная к уровню цен первого года периода строительства судна №{i + 1}:")
            edit2 = QLineEdit(self)
            self.form_layout.addWidget(label2)
            self.form_layout.addWidget(edit2)

            label3 = QLabel(f"Цена судна приведенная к уровню цен текущих лет на периода строительства судна №{i + 1}:")
            edit3 = QLineEdit(self)
            self.form_layout.addWidget(label3)
            self.form_layout.addWidget(edit3)
        
        print(self.form_layout.count())
        self.add_tkp_button = QPushButton("Добавить Данные")
        self.form_layout.addWidget(self.add_tkp_button)

        self.add_tkp_button.clicked.connect(self.save_tkp_data)
        self.update()
    def save_tkp_data(self):
        
        self.price_proposal = {}
        self.applicant = {}
        self.status = {}
        
        j = 1
        total_elements = self.form_layout.count()
        
        for i in range(0, total_elements - 1, 6):  # Учитывает 3 виджета для ценового предложения и 3 виджета для заявителя
            price_proposal_edit = self.form_layout.itemAt(i + 1).widget()

            if price_proposal_edit:
                key_price = f"Цена судна приведенная к уровню цен года его поставки №{j}"
                self.price_proposal[key_price] = int(price_proposal_edit.text()) if price_proposal_edit.text() else "[]"

            applicant_edit = self.form_layout.itemAt(i + 3).widget()
            if applicant_edit:
                key_applicant = f"Цена судна приведенная к уровню цен первого года периода строительства судна №{j}"
                self.applicant[key_applicant] = applicant_edit.text() if applicant_edit.text() else "[]"

            status_edit = self.form_layout.itemAt(i + 5).widget()
            if status_edit:
                key_status = f"Цена судна приведенная к уровню цен текущих лет на периода строительства судна №{j}"
                self.status[key_status] = status_edit.text() if status_edit.text() else "[]"

            j += 1
       

        price_proposal_json = json.dumps(self.price_proposal,ensure_ascii=False)
        applicant_json = json.dumps(self.applicant,ensure_ascii=False)
        status_json = json.dumps(self.status,ensure_ascii=False)
        # tkp_values_all = [int(value) for value in  self.tkp_data.values()]
        # if tkp_values_all:
                
        #         max_tkp = max(tkp_values_all)
        #         min_tkp = min(tkp_values_all)
        #         avg_tkp = sum(tkp_values_all) / len(tkp_values_all)
        #         standard_deviation = statistics.stdev(tkp_values_all)
        #         cv = (standard_deviation / avg_tkp) * 100
     
        
        purchase = Purchase.update(
                            
                            ContractCount=int(self.edit1.text()) if self.edit1.text() else 0,
                            NMCK_1 = price_proposal_json,
                            NMCK_2 = applicant_json,
                            NMCK_3 = status_json
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

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetNMCK()
#     window.show()
#     sys.exit(app.exec())
        