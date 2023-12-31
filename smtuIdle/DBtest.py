from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,QPushButton,QHeaderView
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase
from PySide6.QtWidgets import QSizePolicy
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.

# Создаем соединение с базой данных
db = SqliteDatabase('test.db')




class PurchasesWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)  # Установите количество столбцов по своему усмотрению
        # self.table.setHorizontalHeaderLabels(["Идентификатор", "Номер заказа", "Предмет аукциона"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Создаем кнопки для навигации
        self.prev_button = QPushButton("Назад", self)
        self.next_button = QPushButton("Вперед", self)

        # Устанавливаем обработчики событий для кнопок
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)
        # Скрыть номера строк и столбцов
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        # Текущая позиция записи
        self.current_position = 0

        # Создаем макет и добавляем элементы
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)

        # Получаем данные из базы данных и отображаем первую запись
        purchases = Purchase.select().limit(10)
        self.purchases_list = list(purchases)
        self.show_current_purchase()

    def show_current_purchase(self):
        # Очищаем таблицу перед добавлением новых данных
        self.table.setRowCount(0)

        # Получаем текущую запись
        current_purchase = self.purchases_list[self.current_position]

        # Добавляем данные в виде "название поля - значение поля"
        self.add_row_to_table("Идентификатор", str(current_purchase.Id))
        self.add_row_to_table("Закон", current_purchase.PurchaseOrder)
        self.add_row_to_table("Реестровый номер", current_purchase.RegistryNumber)
        self.add_row_to_table("Метод закупки", current_purchase.ProcurementMethod)
        self.add_row_to_table("Наименование закупки", current_purchase.PurchaseName)
        self.add_row_to_table("Предмет аукциона", current_purchase.AuctionSubject)
        self.add_row_to_table("Код идентификации закупки", current_purchase.PurchaseIdentificationCode)
        self.add_row_to_table("Номер лота", str(current_purchase.LotNumber))
        self.add_row_to_table("Наименование лота", current_purchase.LotName)
        self.add_row_to_table("Начальная максимальная цена контракта", str(current_purchase.InitialMaxContractPrice))
        self.add_row_to_table("Валюта", current_purchase.Currency)
        self.add_row_to_table("Начальная максимальная цена контракта в валюте", str(current_purchase.InitialMaxContractPriceInCurrency))
        self.add_row_to_table("Валюта контракта", current_purchase.ContractCurrency)
        self.add_row_to_table("Классификация ОКДП", current_purchase.OKDPClassification)
        self.add_row_to_table("Классификация ОКПД", current_purchase.OKPDClassification)
        self.add_row_to_table("Классификация ОКПД2", current_purchase.OKPD2Classification)
        self.add_row_to_table("Код позиции", current_purchase.PositionCode)
        self.add_row_to_table("Наименование заказчика", current_purchase.CustomerName)
        self.add_row_to_table("Организация закупки", current_purchase.ProcurementOrganization)
        self.add_row_to_table("Дата размещения", str(current_purchase.PlacementDate))
        self.add_row_to_table("Дата обновления", str(current_purchase.UpdateDate))
        self.add_row_to_table("Этап закупки", current_purchase.ProcurementStage)
        self.add_row_to_table("Особенности закупки", current_purchase.ProcurementFeatures)
        self.add_row_to_table("Дата начала заявки", str(current_purchase.ApplicationStartDate))
        self.add_row_to_table("Дата окончания заявки", str(current_purchase.ApplicationEndDate))
        self.add_row_to_table("Дата аукциона", str(current_purchase.AuctionDate))
        self.add_row_to_table("Количество запросов", str(current_purchase.QueryCount))
        self.add_row_to_table("Количество ответов", str(current_purchase.ResponseCount))
        self.add_row_to_table("Среднее значение цены", str(current_purchase.AveragePrice))
        self.add_row_to_table("Минимальная цена", str(current_purchase.MinPrice))
        self.add_row_to_table("Максимальная цена", str(current_purchase.MaxPrice))
        self.add_row_to_table("Среднее квадратичное отклонение", str(current_purchase.StandardDeviation))
        self.add_row_to_table("Коэффициент вариации", str(current_purchase.CoefficientOfVariation))
        self.add_row_to_table("НМЦК рыночная", str(current_purchase.NMCKMarket))
        self.add_row_to_table("Лимит финансирования", str(current_purchase.FinancingLimit))
       

    def add_row_to_table(self, label_text, value_text):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        label_item = QTableWidgetItem(label_text)
        value_item = QTableWidgetItem(value_text)

        self.table.setItem(row_position, 0, label_item)
        self.table.setItem(row_position, 1, value_item)

    def show_previous(self):
        if self.current_position > 0:
            self.current_position -= 1
            self.show_current_purchase()

    def show_next(self):
        if self.current_position < len(self.purchases_list) - 1:
            self.current_position += 1
            self.show_current_purchase()
    

# Создаем экземпляр виджета
# widget = PurchasesWidget()

# Отображаем виджет
# widget.show()

# # Запускаем главный цикл приложения
# app.exec_()
