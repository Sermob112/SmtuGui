from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import FinalDetermination
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
db = SqliteDatabase('test.db')

class InsertWidgetCEIA(QWidget):
    def __init__(self, purchase_id):
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.setWindowTitle("Окно ввода даных ЦКЕИ")
        self.setGeometry(100, 100, 800, 400)
        # Создаем лейблы

        
        label1 = QLabel("Способ направления запросов о предоставлении ценовой информации")
        label2 = QLabel("Способ использования общедоступной информации")
        label3 = QLabel("НМЦК, полученная различными способами")
        label4 = QLabel("НМЦК на основе затратного метода, руб. (в случае его применения)")
        label5 = QLabel("Цена сравнимой продукции")
        label6 = QLabel("НМЦК, полученная с применением двух методов")
        label7 = QLabel("ЦКЕИ на основе метода сопоставимых рыночных цен")
        label8 = QLabel("ЦКЕИ на основе затратного метода, руб. (в случае его применения)")
        label9 = QLabel("ЦКЕИ, полученная с применением двух методов")


        # Создаем поля ввода
        self.RequestMethod = QLineEdit(self)
        self.PublicInformationMethod = QLineEdit(self)
        self.NMCObtainedMethods = QLineEdit(self)
        self.CostMethodNMC = QLineEdit(self)
        self.ComparablePrice = QLineEdit(self)
        self.NMCMethodsTwo = QLineEdit(self)
        self.CEIComparablePrices = QLineEdit(self)
        self.CEICostMethod = QLineEdit(self)
        self.CEIMethodsTwo = QLineEdit(self)
   
      

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
        layout5 = QHBoxLayout(self)
        layout6 = QHBoxLayout(self)
        layout7 = QHBoxLayout(self)
        layout8 = QHBoxLayout(self)
        layout9 = QHBoxLayout(self)


        layout2.addWidget(label1)
        layout2.addWidget(self.RequestMethod)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layout3.addWidget(label2)
        layout3.addWidget(self.PublicInformationMethod)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label3)
        layout4.addWidget(self.NMCObtainedMethods)

        layout5.addWidget(label4)
        layout5.addWidget(self.CostMethodNMC)

        layout6.addWidget(label5)
        layout6.addWidget(self.ComparablePrice)

        layout7.addWidget(label6)
        layout7.addWidget(self.NMCMethodsTwo)

        layout7.addWidget(label7)
        layout7.addWidget(self.CEIComparablePrices)

        layout8.addWidget(label8)
        layout8.addWidget(self.CEICostMethod)
        layout9.addWidget(label9)
        layout9.addWidget(self.CEIMethodsTwo)


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

        self.add_tkp_button = QPushButton("Добавить Данные")
        self.add_tkp_button.clicked.connect(self.save_tkp_data)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.layout1)
        scroll_area.setWidget(scroll_widget)
      
        self.form_layout = QVBoxLayout ()
        self.layout1.addLayout(self.form_layout)
        self.form_layout.addWidget(self.add_tkp_button)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
    
    def save_tkp_data(self):

        contract = FinalDetermination(purchase=self.purchase_id,
                         
                            RequestMethod=self.RequestMethod.text() if self.RequestMethod.text() else 'нет данных',
                            PublicInformationMethod=self.PublicInformationMethod.text() if self.PublicInformationMethod.text() else 'нет данных',
                            NMCObtainedMethods=self.NMCObtainedMethods.text() if self.NMCObtainedMethods.text() else 'нет данных',
                            CostMethodNMC=self.CostMethodNMC.text() if self.CostMethodNMC.text() else 'нет данных',
                            ComparablePrice=self.ComparablePrice.text() if self.ComparablePrice.text() else 'нет данных',
                            NMCMethodsTwo=self.NMCMethodsTwo.text() if self.NMCMethodsTwo.text() else 'нет данных',
                            CEIComparablePrices=self.CEIComparablePrices.text() if self.CEIComparablePrices.text() else 'нет данных',
                            CEICostMethod=self.CEICostMethod.text() if self.CEICostMethod.text() else 'нет данных',
                            CEIMethodsTwo=self.CEIMethodsTwo.text() if self.CEIMethodsTwo.text() else 'нет данных',
                     
                         
                            )
       
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
#     window = InsertWidgetCEIA(3)
#     window.show()
#     sys.exit(app.exec())
        
