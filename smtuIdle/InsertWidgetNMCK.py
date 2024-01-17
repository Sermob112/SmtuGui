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
db = SqliteDatabase('test.db')

class InsertWidgetNMCK(QWidget):
    def __init__(self,purchase_id):
        
        super().__init__()
        self.tkp_data = {}
        self.purchase_id = purchase_id
        self.setWindowTitle("Окно ввода даных НМЦК")
        self.setGeometry(100, 100, 600, 200)
        # Создаем лейблы
        label1 = QLabel("1. Ввод данных - Метод сопоставимых рыночных цен (анализ рынка)")
        label2 = QLabel("Количество запросов ТКП:")
        label3 = QLabel("Количество ответов ТКП:")
        label4 = QLabel("Лимит финансирования, руб.:")


        # Создаем поля ввода
        self.edit1 = QLineEdit(self)
        self.edit1.setValidator(QIntValidator())
        self.edit1.textChanged.connect(self.update_fields)
        self.edit2 = QLineEdit(self)
        self.edit2.setValidator(QIntValidator())
        self.edit3 = QLineEdit(self)
        self.edit3.setValidator(QIntValidator())

        layout1 = QVBoxLayout(self)
        layout2 = QHBoxLayout(self)
        layout3 = QHBoxLayout(self)
        layout4 = QHBoxLayout(self)
        layout5 = QVBoxLayout(self)

        # Добавляем лейбл и поле ввода в первую строку
        layout2.addWidget(label2)
        layout2.addWidget(self.edit1)
        
        # Добавляем лейбл и поле ввода во вторую строку
        layout3.addWidget(label3)
        layout3.addWidget(self.edit2)

        # Добавляем лейбл и поле ввода в третью строку
        layout4.addWidget(label4)
        layout4.addWidget(self.edit3)

        # Добавляем все строки в вертикальный контейнер
        layout1.addWidget(label1)
        layout1.addLayout(layout2)
        layout1.addLayout(layout3)
        layout1.addLayout(layout4)

        self.form_layout = QVBoxLayout()
        layout1.addLayout(self.form_layout)

        self.setLayout(layout1)

    def update_fields(self):
        num_fields = int(self.edit1.text())
        if num_fields > 10:
            num_fields = 10
        elif num_fields < 0:
            num_fields = 1

        # Удаляем все существующие поля ввода из формы
        self.clear_layout(self.form_layout)

        # Создаем и добавляем новые поля ввода в форму
        for i in range(num_fields):
            label = QLabel(f"Ценовое предложение №{i + 1}:")
            edit = QLineEdit(self)
            edit.setValidator(QIntValidator())
            self.form_layout.addWidget(label)
            self.form_layout.addWidget(edit)
            # key = f"ТКП {i + 1}"
            # self.tkp_data[key] = int(edit.text()) if edit.text() else 0
        self.add_tkp_button = QPushButton("Добавить ТКП")
        self.form_layout.addWidget(self.add_tkp_button)
        self.add_tkp_button.clicked.connect(self.save_tkp_data)
        self.update()
    def save_tkp_data(self):
        # Преобразовываем словарь с данными в строку JSON
 
        self.tkp_data = {}

        # Заполняем словарь данными из динамических полей
        for i in range(0,self.form_layout.count() - 1,2):  # -1, чтобы не включать кнопку
            key = f"ТКП {i}"
            edit = self.form_layout.itemAt(i+1).widget()
            self.tkp_data[key] = int(edit.text()) if edit.text() else 0

        tkp_json = json.dumps(self.tkp_data,ensure_ascii=False)
        tkp_values_all = [int(value) for value in  self.tkp_data.values()]
        if tkp_values_all:
                
                max_tkp = max(tkp_values_all)
                min_tkp = min(tkp_values_all)
                avg_tkp = sum(tkp_values_all) / len(tkp_values_all)
                standard_deviation = statistics.stdev(tkp_values_all)
                cv = (standard_deviation / avg_tkp) * 100
     
        
        purchase = Purchase.update(
                            TKPData=tkp_json,
                            QueryCount=int(self.edit1.text()) if self.edit1.text() else 0,
                            ResponseCount=int(self.edit2.text()) if self.edit2.text() else 0,
                            FinancingLimit=int(self.edit3.text()) if self.edit3.text() else 0,
                            AveragePrice = avg_tkp if avg_tkp else 0,
                            MinPrice = min_tkp if min_tkp else 0,
                            MaxPrice = max_tkp if max_tkp else 0,
                            StandardDeviation = standard_deviation if standard_deviation else 0,
                            CoefficientOfVariation = cv if cv else 0,
                            NMCKMarket = avg_tkp if avg_tkp else 0,
                            ).where(Purchase.Id == self.purchase_id)
        try:
            # Попытка сохранения данных
            purchase.execute()
        
            db.close()

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
        
