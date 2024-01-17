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

class InsertWidgetCurrency(QWidget):
    closed_signal = Signal()
    def __init__(self, purchase_id):
        super().__init__()
        self.setWindowTitle("Окно определения валюты")
        self.setGeometry(100, 100, 600, 200)
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.purchase = Purchase.get(Purchase.Id == self.purchase_id)

        labelInfo = QLabel(f"Реестровый номер закупки: {self.purchase.RegistryNumber} .Текущая валюта {self.purchase.Currency} ")
        label1 = QLabel("Цифровое значение валюты")
        # label2 = QLabel("Дата изменения значения валюты")
        label3 = QLabel("Дата курса валюты")
      

        # Создаем поля ввода
        self.CurrencyValue = QLineEdit(self)
        # self.DateValueChanged = QDateEdit(self)
        self.CurrencyRateDate = QDateEdit(self)
 
   
      

        self.layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
      
        layout2.addWidget(label1)
        layout2.addWidget(self.CurrencyValue)
        
        # Добавляем лейбл и поле ввода во вторую строку
        # layout3.addWidget(label2)
        # layout3.addWidget(self.DateValueChanged)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label3)
        layout4.addWidget(self.CurrencyRateDate)

       


        # Добавляем все строки в вертикальный контейнер
        self.layout1.addWidget(labelInfo)
        self.layout1.addWidget(label1)

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
            currency = CurrencyRate(purchase=self.purchase_id,
                                CurrentCurrency = "RUB",
                                CurrencyValue= float(self.CurrencyValue.text()) if self.CurrencyValue.text() else 0,
                                DateValueChanged=datetime.now().strftime("%d-%m-%Y"),
                                CurrencyRateDate=self.CurrencyRateDate.text() if self.CurrencyRateDate.text() else 'нет данных',
                                PreviousCurrency = str(self.purchase.Currency) if self.purchase else 'нет данных'
                        
                                )
            purchaseToAdd = Purchase.update(
                    Currency = "RUB",
                    InitialMaxContractPrice = float(self.purchase.InitialMaxContractPrice) * float(self.CurrencyValue.text()),
                    isChanged = True
            ).where(Purchase.Id == self.purchase_id)
            try:
                # Попытка сохранения данных
                purchaseToAdd.execute()
                currency.save()
                db.close()

                # Выводим сообщение об успешном сохранении
                self.show_message("Успех", "Данные успешно добавлены")
                self.close()
            except Exception as e:
                # Выводим сообщение об ошибке
                self.show_message("Ошибка", f"Произошла ошибка: {str(e)}")
            # print("ТКПData сохранены:", tkp_json)
            
    def update_currency(self):
        currency = CurrencyRate.update(
                            CurrentCurrency = "RUB",
                            CurrencyValue= float(self.CurrencyValue.text()) if self.CurrencyValue.text() else 0,
                            DateValueChanged=datetime.now().strftime("%d-%m-%Y"),
                            CurrencyRateDate=self.CurrencyRateDate.text() if self.CurrencyRateDate.text() else 'нет данных',
                            PreviousCurrency = str(self.purchase.Currency) if self.purchase else 'нет данных'
                    
                            ).where(CurrencyRate.purchase ==self.purchase_id)
        purchaseToAdd = Purchase.update(
                Currency = "RUB",
                InitialMaxContractPrice = float(self.purchase.InitialMaxContractPrice) * float(self.CurrencyValue.text()),
                isChanged = True
        ).where(Purchase.Id == self.purchase_id)
        try:
            # Попытка сохранения данных
            currency.execute()
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
#     window = InsertWidgetCurrency(1)
#     window.show()
#     sys.exit(app.exec())
        
