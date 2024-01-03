from PySide6.QtWidgets import QApplication, QCompleter,QMainWindow,QLabel,QLineEdit,QComboBox, QTableWidget,QHBoxLayout, QTableWidgetItem, QVBoxLayout, QWidget,QPushButton,QHeaderView
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase
from PySide6.QtCore import Qt, QStringListModel
import sys


from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('test.db')
cursor = db.cursor()



class PurchasesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_text = None
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.current_position = 0   

         # Создаем выпадающее меню
        self.sort_options = QComboBox(self)
        self.sort_options.addItems(["Сортировать по возрастанию цены", "Сортировать по убыванию цены",
                                    
                                    "Сортировать по Дате (Убывание)","Сортировать по Дате (возростание)"])
         # Устанавливаем обработчик событий для выпадающего меню
        unique_purchase_orders = Purchase.select(Purchase.PurchaseOrder).distinct()
        self.sort_by_putch_order = QComboBox(self)
        self.sort_by_putch_order.addItem("Сортировать по Закону")
        for order in unique_purchase_orders:
            self.sort_by_putch_order.addItem(str(order.PurchaseOrder))
        # Создаем метки и поля для ввода минимальной и максимальной цены
        self.min_price_label = QLabel("Минимальная цена", self)
        self.min_price_input = QLineEdit(self)
        self.min_price_input.setFixedWidth(100)
        self.max_price_label = QLabel("Максимальная цена", self)
        self.max_price_input = QLineEdit(self)
        self.max_price_input.setFixedWidth(100)

        self.min_data_label = QLabel("Начальная дата", self)
        self.min_data_input = QLineEdit(self)
        self.min_data_input.setPlaceholderText("Формат: дд-мм-гггг")
        self.min_data_input.setFixedWidth(150)
        self.max_data_label = QLabel("Конечная дата", self)
        self.max_data_input = QLineEdit(self)
        self.max_data_input.setPlaceholderText("Формат: дд-мм-гггг")
        self.max_data_input.setFixedWidth(150)
         #  кнопка "Сбросить фильтры" 
        self.reset_filters_button = QPushButton("Сбросить фильтры", self)
        self.reset_filters_button.clicked.connect(self.resetFilters)
        # Создаем поле ввода для поиска
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Поиск...")
        self.unique_values_query = self.findUnic()
        completer = QCompleter(self.unique_values_query )
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated.connect(self.handleActivated)
        self.search_input.setCompleter(completer)


        
        # Создаем макет и добавляем элементы
     
  
       

        # Устанавливаем автозавершение для поля ввода
        self.search_input.setCompleter(completer)
       

        # Создаем автозавершение
     
        # Создаем кнопки для навигации
        self.prev_button = QPushButton("Назад", self)
        self.next_button = QPushButton("Вперед", self)

         # Создаем метку
        self.label = QLabel("Текущая запись:", self)
        # Устанавливаем обработчики событий для кнопок
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)

        # Добавляем кнопку "Применить фильтр"
        self.apply_filter_button = QPushButton("Применить фильтр", self)
        self.apply_filter_button.clicked.connect(self.apply_filter)

        # Создаем горизонтальный макет и добавляем элементы
        button_layout = QHBoxLayout()
    
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.label)
        button_layout.addWidget(self.next_button)

       # Создаем горизонтальный макет и добавляем элементы
        layout = QVBoxLayout(self)
        layout.addWidget(self.search_input)
 
        # Добавляем выпадающее меню
        layout.addWidget(self.sort_options)
        layout.addWidget(self.sort_by_putch_order)
        # Создаем горизонтальный макет для минимальной и максимальной цены
        price_layout = QHBoxLayout()
        price_layout.addWidget(self.min_price_label)
        price_layout.addWidget(self.min_price_input)
        price_layout.addWidget(self.max_price_label)
        price_layout.addWidget(self.max_price_input)
        layout.addLayout(price_layout)

        # Создаем горизонтальный макет для начальной и конечной даты
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.min_data_label)
        date_layout.addWidget(self.min_data_input)
        date_layout.addWidget(self.max_data_label)
        date_layout.addWidget(self.max_data_input)
        layout.addLayout(date_layout)

        # Добавляем кнопку "Применить фильтр"
        layout.addWidget(self.apply_filter_button)
        layout.addWidget(self.reset_filters_button)
        # Добавляем таблицу и остальные элементы в макет
        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        # Получаем данные из базы данных и отображаем первую запись
        purchases = Purchase.select()
        self.purchases_list = list(purchases)
        self.show_current_purchase()
    def show_current_purchase(self):

        if self.purchases_list:
            current_purchase = self.purchases_list[self.current_position]
            # Отображаем информацию о текущей записи в лейбле
            self.label.setText(f"Запись {self.current_position + 1} из {len(self.purchases_list)}")
            # Дополнительный код для отображения записи в таблице (замените на свой код)
            # self.table.setItem(row, column, QTableWidgetItem(str(current_purchase.some_property)))
        else:
            self.label.setText("Нет записей")
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

    def apply_filter(self):
        selected_option = self.sort_options.currentText()

        if selected_option == "Сортировать по возрастанию цены":
            order_by = Purchase.InitialMaxContractPrice
        elif selected_option == "Сортировать по убыванию цены":
            order_by = Purchase.InitialMaxContractPrice.desc()
        elif selected_option == "Сортировать по Дате (Убывание)":
            order_by = Purchase.PlacementDate.desc()
        elif selected_option == "Сортировать по Дате (возростание)":
            order_by = Purchase.PlacementDate
  

        # Получаем минимальную и максимальную цены из полей ввода
        min_price = float(self.min_price_input.text()) if self.min_price_input.text() else float('-inf')
        max_price = float(self.max_price_input.text()) if self.max_price_input.text() else float('inf')

        min_date_str = self.min_data_input.text()
        max_date_str = self.max_data_input.text()

        min_date = datetime.strptime(min_date_str, '%d-%m-%Y').date() if min_date_str else None
        max_date = datetime.strptime(max_date_str, '%d-%m-%Y').date() if max_date_str else None
        
        # Выполняем запрос с фильтрацией по диапазону цен и сортировкой
        # Фильтр по цене
        purchases = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(min_price, max_price))
        ).order_by(order_by)
        # Фильтр по дате
        if min_date and max_date:
            purchases = purchases.where(
                (Purchase.PlacementDate.between(min_date, max_date))
            )

        # Фильтр по цене и дате
        purchases_query_combined = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(min_price, max_price)) &
            (Purchase.PlacementDate.between(min_date, max_date) if min_date and max_date else True)
        )
        # Фильтр по законам
       
        selected_order = self.sort_by_putch_order.currentText()
        if selected_order != "Сортировать по Закону":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.PurchaseOrder == selected_order
            )
       
        keyword = self.selected_text

    # Добавляем фильтр по ключевому слову (RegistryNumber)
        if keyword:
            purchases_query_combined = purchases_query_combined.where(
                (Purchase.RegistryNumber.contains(keyword)) |
                (Purchase.ProcurementOrganization.contains(keyword)) |
                     (Purchase.RegistryNumber.contains(keyword)) |
                     (Purchase.CustomerName.contains(keyword))
            )
        
        purchases = purchases_query_combined.order_by(order_by)

        self.purchases_list = list(purchases)
        self.show_current_purchase()

         # Фильтр по ключевым словам
        # selected_order_key = str(self.selected_text)
        # if selected_order_key:
        #     purchases_query_combined = purchases_query_combined.where(
        #         (
        #             (Purchase.PurchaseName == selected_order_key) |
        #             (Purchase.ProcurementOrganization == selected_order_key) |
        #             (Purchase.RegistryNumber == selected_order_key) |
        #             (Purchase.CustomerName == selected_order_key)
        #         )
        #     )

    def findUnic(self):
            unique_values_list = []
            unique_values_query = Purchase.select(
            Purchase.PurchaseName, 
            Purchase.ProcurementOrganization, 
            Purchase.RegistryNumber, 
            Purchase.CustomerName
            ).distinct()

            # Получаем все значения из результата запроса
            unique_values = [
                (
                    purchase.PurchaseName,
                    purchase.ProcurementOrganization,
                    purchase.RegistryNumber,
                    purchase.CustomerName
                ) 
                for purchase in unique_values_query
            ]

            # Преобразуем все значения в список строк
           

            for purchase_name, procurement_organization, registry_number, customer_name in unique_values:
                unique_values_list.extend([
                    str(purchase_name) if purchase_name is not None else None,
                    str(procurement_organization) if procurement_organization is not None else None,
                    str(registry_number) if registry_number is not None else None,
                    str(customer_name) if customer_name is not None else None
                ])
            unique_values_list = [value for value in unique_values_list if value is not None]
            return unique_values_list
    def handleActivated(self, text):
        # Обработка выбора элемента из автозаполнения
        self.selected_text = text

    def resetFilters(self):
        # Очищаем все поля ввода
        self.min_price_input.clear()
        self.max_price_input.clear()
        self.min_data_input.clear()
        self.max_data_input.clear()
        self.sort_by_putch_order.setCurrentIndex(0)  # Сбрасываем выбранное значение в выпадающем списке
        self.search_input.clear()

        # Очищаем и снова получаем уникальные значения для автозаполнения
        self.unique_values_query = self.findUnic()
        
        
        # Возвращаем записи в исходное состояние без применения каких-либо фильтров
        purchases_query_combined = Purchase.select()
        self.purchases_list = list(purchases_query_combined)
        self.show_current_purchase()

        
        

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec())