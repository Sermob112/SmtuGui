from PySide6.QtWidgets import *
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination,CurrencyRate
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import QColor
import sys, json
from peewee import JOIN
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('test.db')
cursor = db.cursor()



class PurchasesWidgetAll(QWidget):
    def __init__(self,main):
        super().__init__()
        # self.main_win = main_window
        self.selected_text = None
        self.main_window = main
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(9)

        # Устанавливаем заголовки колонок
        column_headers = ["№ПП", "Закон", "Реестровый номер",
                          "Наименование закупки", "Предмет аукциона", "Начальная максимальная цена контракта",
                          "Валюта", "Наименование заказчика", "Дата размещения"]
        self.table.resizeColumnsToContents()
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalHeaderLabels(column_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.current_position = 0   
        self.label = QLabel("Всего записей", self)
        self.table.cellClicked.connect(self.handle_cell_click)
         # Создаем выпадающее меню
        self.sort_options = QComboBox(self)
        self.sort_options.addItems(["Сортировать по возрастанию цены", "Сортировать по убыванию цены",
                                    
                                    "Сортировать по Дате (Убывание)","Сортировать по Дате (возростание)"])
         # Устанавливаем обработчик событий для выпадающего меню
       
        self.sort_options.setFixedWidth(250)
        unique_purchase_orders = Purchase.select(Purchase.PurchaseOrder).distinct()
        self.sort_by_putch_order = QComboBox(self)
        self.sort_by_putch_order.addItem("Сортировать по Закону")
        self.sort_by_putch_order.setFixedWidth(250)
        for order in unique_purchase_orders:
            self.sort_by_putch_order.addItem(str(order.PurchaseOrder))
        # Создаем метки и поля для ввода минимальной и максимальной цены
        self.min_price_label = QLabel("Минимальная цена", self)
        self.min_price_input = QLineEdit(self)
        self.min_price_input.setFixedWidth(100)
        self.max_price_label = QLabel("Максимальная цена", self)
        self.max_price_input = QLineEdit(self)
        self.max_price_input.setFixedWidth(100)
        self.toExcel = QPushButton("Экспорт в Excel", self)
        self.toExcel.clicked.connect(self.export_to_excel_clicked)

        self.min_data_label = QLabel("Начальная дата", self)
        self.min_data_input = QDateEdit(self)
        self.min_data_input.setCalendarPopup(True)
        # self.min_data_input.setDate(self.min_data_input.date().currentDate())
        self.min_data_input.setFixedWidth(150)
        self.max_data_label = QLabel("Конечная дата", self)
        self.max_data_input = QDateEdit(self)
        self.max_data_input.setCalendarPopup(True)
        self.max_data_input.setDate(self.max_data_input.date().currentDate())
        button_layout3 = QHBoxLayout()
        button_layout3.addWidget(self.toExcel)
        self.max_data_input.setFixedWidth(150)
         #  кнопка "Сбросить фильтры" 
        self.reset_filters_button = QPushButton("Сбросить фильтры", self)
        self.reset_filters_button.setFixedWidth(150)
        self.reset_filters_button.clicked.connect(self.resetFilters)
        # Создаем поле ввода для поиска
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Поиск по Реестровому номеру, заказчику, наименованию объекта или организации")
        self.unique_values_query = self.findUnic()
        self.search_input.setFixedWidth(300)
        completer = QCompleter(self.unique_values_query )
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        completer.activated.connect(self.handleActivated)
        self.search_input.setCompleter(completer)
        # Устанавливаем автозавершение для поля ввода
        self.search_input.setCompleter(completer)
        # Создаем кнопки для навигации
       
    
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignHCenter)

        # Добавляем кнопку "Применить фильтр"
        self.apply_filter_button = QPushButton("Применить фильтр", self)
        self.apply_filter_button.clicked.connect(self.apply_filter)
        self.apply_filter_button.setFixedWidth(150)

 
    

       # Создаем горизонтальный макет и добавляем элементы
        layout = QVBoxLayout(self)
        layout.addWidget(self.search_input)
 
        # Добавляем выпадающее меню
        layout.addWidget(self.sort_options)
        layout.addWidget(self.sort_by_putch_order)
        # Создаем горизонтальный макет для минимальной и максимальной цены
        price_layout = QGridLayout()
        # Добавляем их в сетку
        price_layout.addWidget(self.min_price_label, 0, 0)
        price_layout.addWidget(self.min_price_input, 0, 1)
        price_layout.addWidget(self.max_price_label, 1, 0)
        price_layout.addWidget(self.max_price_input, 1, 1)
        # layout.addLayout(price_layout)

        # Создаем горизонтальный макет для начальной и конечной даты
        date_layout = QGridLayout()
        date_layout.addWidget(self.min_data_label, 0, 0)
        date_layout.addWidget(self.min_data_input, 0, 1)
        date_layout.addWidget(self.max_data_label, 1, 0)
        date_layout.addWidget(self.max_data_input, 1, 1)
        combined_layout = QHBoxLayout()
        combined_layout.addLayout(price_layout)
        combined_layout.addLayout(date_layout)
        combined_layout.addSpacing(200) 
        frame = QFrame()
        frame.setLayout(combined_layout)

        # Ограничиваем максимальную ширину frame
        frame.setMaximumWidth(850)
        layout.addWidget(frame)
        price_layout.setColumnStretch(2, 1)  # Растягиваем последний столбец
        date_layout.setColumnStretch(2, 1)

        # Добавляем кнопку "Применить фильтр"
        layout.addWidget(self.apply_filter_button)
        layout.addWidget(self.reset_filters_button)
        # Добавляем таблицу и остальные элементы в макет
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addLayout(button_layout3)
        # Получаем данные из базы данных и отображаем первую запись
        self.reload_data()
        # self.purchases = Purchase.select()
        # self.purchases = (Purchase
        #         .select()
        #         .join(Contract, JOIN.LEFT_OUTER)
        #           # Уточните условия, если нужно
        #         )
        # combined_list = (Purchase
        #         .select()
        #         .join(Contract, JOIN.LEFT_OUTER)
        #           # Уточните условия, если нужно
        #         .execute())
   
        # self.purchases_list = list(self.purchases)
        # self.purchases_list = list(self.purchases)
        # self.show_current_purchase()
    def show_all_purchases(self):
    # Очищаем таблицу перед добавлением новых данных
        self.table.setRowCount(0)
        self.label.setText(f"Всего записей {len(self.purchases_list)}")
        if len(self.purchases_list) != 0:
            for current_position, current_purchase in enumerate(self.purchases_list):
                # Добавляем новую строку для каждой записи
                self.table.insertRow(current_position)
                
                # Добавляем данные в каждую ячейку для текущей записи
                for col, value in enumerate([current_purchase.Id, current_purchase.PurchaseOrder, current_purchase.RegistryNumber
                                             , current_purchase.PurchaseName,current_purchase.AuctionSubject,
                                             str(current_purchase.InitialMaxContractPrice), current_purchase.Currency,
                                              current_purchase.CustomerName,str(current_purchase.PlacementDate)
                                             ]):
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(current_position, col, item)
            
                        
                    # Добавляем данные в виде "название поля    - значение поля" для каждой колонки
        else:
            self.label.setText("Нет записей")     

   

    
    def apply_filter(self):
        self.current_position = 0
        self.selected_option = self.sort_options.currentText()

        if  self.selected_option == "Сортировать по возрастанию цены":
            order_by = Purchase.InitialMaxContractPrice
        elif  self.selected_option == "Сортировать по убыванию цены":
            order_by = Purchase.InitialMaxContractPrice.desc()
        elif  self.selected_option == "Сортировать по Дате (Убывание)":
            order_by = Purchase.PlacementDate.desc()
        elif  self.selected_option == "Сортировать по Дате (возростание)":
            order_by = Purchase.PlacementDate
  

        # Получаем минимальную и максимальную цены из полей ввода
        self.min_price = float(self.min_price_input.text()) if self.min_price_input.text() else float('-inf')
        self.max_price = float(self.max_price_input.text()) if self.max_price_input.text() else float('inf')

        min_date_str = self.min_data_input.date()
        max_date_str = self.max_data_input.date()

        self.min_date = min_date_str.toPython() if min_date_str.isValid() else None
        self.max_date = max_date_str.toPython() if max_date_str.isValid() else None

        
        # Выполняем запрос с фильтрацией по диапазону цен и сортировкой
        # Фильтр по цене
        purchases = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(self.min_price, self.max_price))
        ).order_by(order_by)
        # Фильтр по дате
        if  self.min_date and  self.max_date:
            purchases = purchases.where(
                (Purchase.PlacementDate.between( self.min_date,  self.max_date))
            )

        # Фильтр по цене и дате
        purchases_query_combined = Purchase.select().where(
            (Purchase.InitialMaxContractPrice.between(self.min_price, self.max_price)) &
            (Purchase.PlacementDate.between( self.min_date,  self.max_date) if  self.min_date and  self.max_date else True)
        )
        # Фильтр по законам
       
        self.selected_order = self.sort_by_putch_order.currentText()
        if  self.selected_order != "Сортировать по Закону":
            purchases_query_combined = purchases_query_combined.where(
                Purchase.PurchaseOrder ==  self.selected_order
            )
       
   
        keyword = self.selected_text
        

    # Добавляем фильтр по ключевому слову (RegistryNumber)
        if keyword:
            purchases_query_combined = purchases_query_combined.where(
                (Purchase.RegistryNumber.contains(keyword)) |
                (Purchase.ProcurementOrganization.contains(keyword)) |
                     (Purchase.PurchaseName.contains(keyword)) |
                     (Purchase.CustomerName.contains(keyword))
            )
        
        self.purchases = purchases_query_combined.order_by(order_by)
 

        self.purchases_list = list(self.purchases)
       
        self.show_all_purchases()

  
    def handle_cell_click(self, row, column):
        # Получаем Id из выбранной строки и выводим в консоль

        selected_id = self.table.item(row, 0).text()
        self.window.stackedWidget.setCurrentIndex(2)
        self.window.purchaseViewer.reload_data_id(selected_id)
        # from DBtest import PurchasesWidget
        # self.wind = PurchasesWidget(selected_id)
        # self.wind.show()


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
        self.current_position = 0
        self.selected_text = None
        # Очищаем и снова получаем уникальные значения для автозаполнения
        self.unique_values_query = self.findUnic()
        
        
        # Возвращаем записи в исходное состояние без применения каких-либо фильтров
        self.reload_data()

     

    def remove_button_clicked(self):
        # reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
        #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        reply = QMessageBox()
        reply.setText('Вы точно хотите удалить выбранные записи?')
        reply.addButton("нет", QMessageBox.NoRole)
        reply.addButton("да", QMessageBox.YesRole)
        result = reply.exec()
        if result == 1:
            if self.current_purchase.Id:
                success = delete_records_by_id([self.current_purchase.Id])
                if success:
                    self.main_win.updatePurchaseLabel()
                    QMessageBox.information(self, "Успех", "Вы успешно удалили запись!")
                    self.resetFilters()
                else:
                    QMessageBox.information(self,"Ошибка", "Ошибка при удалении записей")
                    
                  
        else:
            pass
    def update_currency(self):
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
            self.curr_shower = InsertWidgetCurrency(purchase_id)
            self.curr_shower.show()
    def export_to_excel_clicked(self ):
        current_sort_option = self.sort_options.currentText()
        search_input = self.selected_text if self.selected_text is not None else None
        sort_options  = current_sort_option if current_sort_option is not None  else None
        sort_by_putch_order =  self.sort_by_putch_order.currentText() if self.sort_by_putch_order is not None  else None
        min_date = self.min_data_input.date().toPython() if self.min_data_input.date().toPython() is not None  else None
        max_date = self.max_data_input.date().toPython() if self.max_data_input.date().toPython() is not None  else None
        min_price = self.min_price_input.text() if self.min_price_input.text() is not None  else None
        max_price = self.max_price_input.text()  if self.max_price_input.text() is not None  else None
        filters = {
        'search_input': search_input,
        'filter_criteria': sort_options ,
        'purchase_order': sort_by_putch_order,
        'start_date': min_date,
        'end_date': max_date,
        'min_price': min_price,
        'max_price': max_price,
        
    }   
    
         
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                # query1 = self.purchases
                # query = self.purchases.select(Purchase, Contract).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                query = (
                    self.purchases
                    .select(Purchase.Id, Purchase.PurchaseOrder, Purchase.RegistryNumber, Purchase.ProcurementMethod,
        Purchase.PurchaseName, Purchase.AuctionSubject, Purchase.PurchaseIdentificationCode,
        Purchase.LotNumber, Purchase.LotName, Purchase.InitialMaxContractPrice, Purchase.Currency,
        Purchase.InitialMaxContractPriceInCurrency, Purchase.ContractCurrency,
        Purchase.OKDPClassification, Purchase.OKPDClassification, Purchase.OKPD2Classification,
        Purchase.PositionCode, Purchase.CustomerName, Purchase.ProcurementOrganization,
        Purchase.PlacementDate, Purchase.UpdateDate, Purchase.ProcurementStage,
        Purchase.ProcurementFeatures, Purchase.ApplicationStartDate, Purchase.ApplicationEndDate,
        Purchase.AuctionDate, Purchase.QueryCount, Purchase.ResponseCount, Purchase.AveragePrice,
        Purchase.MinPrice, Purchase.MaxPrice, Purchase.StandardDeviation, Purchase.CoefficientOfVariation,
        Purchase.TKPData, Purchase.NMCKMarket, Purchase.FinancingLimit, Purchase.InitialMaxContractPriceOld,
        Purchase.notification_link,Purchase.quantity_units,Purchase.nmck_per_unit,
        
        Contract.TotalApplications, Contract.AdmittedApplications, Contract.RejectedApplications,
        Contract.PriceProposal, Contract.Applicant, Contract.Applicant_satatus, Contract.WinnerExecutor,
        Contract.ContractingAuthority, Contract.ContractIdentifier, Contract.RegistryNumber,
        Contract.ContractNumber, Contract.StartDate, Contract.EndDate, Contract.ContractPrice,
        Contract.AdvancePayment, Contract.ReductionNMC, Contract.ReductionNMCPercent,
        Contract.SupplierProtocol, Contract.ContractFile, FinalDetermination.RequestMethod, FinalDetermination.PublicInformationMethod,
        FinalDetermination.NMCObtainedMethods, FinalDetermination.CostMethodNMC,
        FinalDetermination.ComparablePrice, FinalDetermination.NMCMethodsTwo,
        FinalDetermination.CEIComparablePrices, FinalDetermination.CEICostMethod,
        FinalDetermination.CEIMethodsTwo,  CurrencyRate.CurrencyValue, CurrencyRate.CurrentCurrency,
        CurrencyRate.DateValueChanged, CurrencyRate.CurrencyRateDate, CurrencyRate.PreviousCurrency)
                    .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                    .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                    .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                )     
                
                # query = (
                #     self.purchases
                #     .select(Purchase, Contract, FinalDetermination, CurrencyRate)
                #     .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                #     .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                #     .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                # )     
                records, data, user = self.main_window.return_variabels()
                # cleaned_filename = data.sub(r'[\\/*?:"<>| ]', '_', data)
                self.data = list(query.tuples())
                # print(self.data[0])
                if export_to_excel(self.data ,f'{selected_file}/Отфильтрованные данные__{data}_{records}_{user}.xlsx',filters=filters ) == True:
                    QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка записи")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")
           
        
    def reload_data(self):
        self.purchases = Purchase.select()
        self.purchases_list = list(self.purchases)
        self.update()
        self.show_all_purchases()
        

        
        

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidgetAll()
#     csv_loader_widget.show()
#     sys.exit(app.exec())