from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
import statistics
from peewee import *
import pandas as pd
from models import Contract
import sys
class ContractWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Создаем виджеты ввода для каждого поля модели Contract
        self.total_applications_edit = QtWidgets.QLineEdit(self)
        self.admitted_applications_edit = QtWidgets.QLineEdit(self)
        self.rejected_applications_edit = QtWidgets.QLineEdit(self)
        # Добавьте другие поля, как необходимо

        # Создаем макет формы
        layout = QtWidgets.QFormLayout(self)

        # Добавляем метки и поля ввода в макет
        layout.addRow("Общее количество заявок:", self.total_applications_edit)
        layout.addRow("Общее количество допущенных заявок:", self.admitted_applications_edit)
        layout.addRow("Общее количество отклоненных заявок:", self.rejected_applications_edit)
        # Добавьте другие строки, как необходимо

        # Добавляем кнопку "Сохранить"
        save_button = QtWidgets.QPushButton("Сохранить", self)
        save_button.clicked.connect(self.save_contract)
        layout.addRow(save_button)

    def save_contract(self):
        # Получаем значения из полей ввода и сохраняем их в объект Contract
        contract = Contract.create(
            TotalApplications=self.total_applications_edit.text(),
            AdmittedApplications=self.admitted_applications_edit.text(),
            RejectedApplications=self.rejected_applications_edit.text(),
            # Задайте другие поля, как необходимо
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    csv_loader_widget = ContractWidget()
    csv_loader_widget.show()
    sys.exit(app.exec())