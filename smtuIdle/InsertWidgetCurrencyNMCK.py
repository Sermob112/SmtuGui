from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import CurrencyRate, Purchase
from PySide6.QtCore import Qt,Signal, QStringListModel
from PySide6.QtGui import *
import sys, json
import statistics
import pandas as pd
from datetime import datetime
db = SqliteDatabase('test.db')

class InsertWidgetCurrencyNMCK(QWidget):
    closed_signal = Signal()
    def __init__(self, purchase_id):
        super().__init__()
        self.setWindowTitle("Окно определения валюты")
        self.setGeometry(100, 100, 600, 200)
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.purchase = Purchase.get(Purchase.Id == self.purchase_id)
        self.currency = CurrencyRate.get(CurrencyRate.purchase == self.purchase_id)
        labelInfo = QLabel(f"Реестровый номер закупки: {self.purchase.RegistryNumber}")
        labelInfo2 = QLabel(f"Текущая валюта: {self.currency.PreviousCurrency}")
        labelInfo23 = QLabel(f"Новое значение валюты в рублях для указанного курса : {self.currency.CurrencyValue} {self.currency.CurrentCurrency}")
        labelInfo3 = QLabel(f"Текущая НМЦК: {self.purchase.InitialMaxContractPrice} {self.currency.PreviousCurrency}")
        labelInfo4 = QLabel(f"Новое НМЦК будет: {self.purchase.InitialMaxContractPrice} * {self.currency.CurrencyValue} = {self.purchase.InitialMaxContractPrice * self.currency.CurrencyValue} {self.currency.CurrentCurrency}" )

    
 
   
      

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
      


       


        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(labelInfo)
        self.layout1.addWidget(labelInfo2)
        self.layout1.addWidget(labelInfo23)
        self.layout1.addWidget(labelInfo3)
        self.layout1.addWidget(labelInfo4)
        self.layout1.addLayout(layout2)
        self.layout1.addLayout(layout3)
        self.layout1.addLayout(layout4)

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
        if self.purchase.isChanged == True:
            self.update_currency()

        else:
            purchaseToAdd = Purchase.update(
                    Currency = "RUB",
                      InitialMaxContractPriceOld = float(self.purchase.InitialMaxContractPrice),
                    InitialMaxContractPrice = float(self.purchase.InitialMaxContractPrice) * float(self.currency.CurrencyValue),
                    isChanged = True
            ).where(Purchase.Id == self.purchase_id)
            try:
                # Попытка сохранения данных
                purchaseToAdd.execute()
              
                db.close()

                # Выводим сообщение об успешном сохранении
                self.show_message("Успех", "Данные успешно добавлены")
                self.close()
            except Exception as e:
                # Выводим сообщение об ошибке
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")
            # print("ТКПData сохранены:", tkp_json)
            
    def update_currency(self):

        purchaseToAdd = Purchase.update(
                Currency = "RUB",
                InitialMaxContractPriceOld = float(self.purchase.InitialMaxContractPrice),
                InitialMaxContractPrice = float(self.purchase.InitialMaxContractPrice) * float(self.CurrencyValue.text()),
                isChanged = True
        ).where(Purchase.Id == self.purchase_id)
        try:
            # Попытка сохранения данных
            purchaseToAdd.execute()
            db.close()

            # Выводим сообщение об успешном сохранении
            self.show_message("Успех", "Данные успешно добавлены")
            self.close()
        except Exception as e:
            # Выводим сообщение об ошибке
            self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")


    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    def closeEvent(self, event):
        self.closed_signal.emit()
        super().closeEvent(event)
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = InsertWidgetCurrencyNMCK(3)
#     window.show()
#     sys.exit(app.exec())
        
