from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,QPushButton
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.

# Создаем соединение с базой данных
db = SqliteDatabase('test.db')



# Создаем виджет для отображения данных
class PurchasesWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)  # Установите количество столбцов по своему усмотрению
        self.table.setHorizontalHeaderLabels(["Идентификатор", "Номер заказа", "Предмет аукциона"])

        # Создаем кнопки для навигации
        self.prev_button = QPushButton("Назад", self)
        self.next_button = QPushButton("Вперед", self)

        # Устанавливаем обработчики событий для кнопок
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)

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

        # Заполняем таблицу данными из текущей записи
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(str(current_purchase.Id)))
        self.table.setItem(row_position, 1, QTableWidgetItem(current_purchase.PurchaseOrder))
        self.table.setItem(row_position, 2, QTableWidgetItem(current_purchase.AuctionSubject))

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
