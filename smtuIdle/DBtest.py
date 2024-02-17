from PySide6.QtWidgets import *
from peewee import SqliteDatabase, Model, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from datetime import date
from models import Purchase, Contract, FinalDetermination,CurrencyRate
from PySide6.QtCore import *
from PySide6.QtGui import QColor
import sys, json
from PySide6.QtGui import QFont
from peewee import JOIN
from insertPanel import InsertWidgetPanel
from InsertWidgetContract import InsertWidgetContract
from InsertWidgetNMCK import InsertWidgetNMCK
from InsertWidgetCEIA import InsertWidgetCEIA
from InsertWidgetCurrency import InsertWidgetCurrency
from parserV3 import delete_records_by_id, export_to_excel
from datetime import datetime
from PySide6.QtWidgets import QSizePolicy
import os
import subprocess
from openpyxl import Workbook
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('test.db')
cursor = db.cursor()



class PurchasesWidget(QWidget):
    def __init__(self,main_window,role, user, changer):
        super().__init__()
        self.main_win = main_window
        self.selected_text = None
        self.role = role
        self.user = user
        self.changer = changer
        # Создаем таблицу для отображения данных
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # Устанавливаем первой колонке режим изменения размера по содержимому
        self.table.horizontalHeader().setStretchLastSection(True) # Растягиваем вторую колонку на оставшееся пространство
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setColumnWidth(0, 500)
        self.table.setWordWrap(True) # Разрешаем перенос текста в ячейках
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.current_position =0
        self.BackButton = QPushButton("Назад", self)
        self.BackButton.clicked.connect(self.go_back)
        self.addButtonContract = QPushButton("Добавить обоснование начальной (максимальной) цены контракта", self)
        
        self.addButtonContract.setMaximumWidth(400)
        # self.addButtonTKP = QPushButton("Добавить обоснование начальной (максимальной) цены контракта", self)
        # self.addButtonCIA = QPushButton("Добавить ЦКЕИ", self)
        self.addButtonCurrency= QPushButton("Экспорт в excel файл", self)
        self.addButtonCurrency.setMaximumWidth(300)


         # Устанавливаем обработчики событий для кнопок
        self.addButtonContract.clicked.connect(self.add_button_contract_clicked)
        # self.addButtonTKP.clicked.connect(self.add_button_tkp_clicked)
        # self.addButtonCIA.clicked.connect(self.add_button_cia_clicked)

        self.addButtonCurrency.clicked.connect(self.show_current_purchase_to_excel)
        
         # Создаем метку
        self.label = QLabel("Текущая запись:", self)
        # Устанавливаем обработчики событий для кнопок


        button_layout = QHBoxLayout()
    
        self.butlayout = QHBoxLayout()
        self.butlayout.addWidget(self.BackButton )
        self.butlayout.setAlignment(Qt.AlignLeft)
        button_layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignHCenter)
        # Создаем горизонтальный макет и добавляем элементы
        button_layout2 = QHBoxLayout()

        
        # button_layout2.addWidget(self.addButtonTKP)
        button_layout2.addWidget(self.addButtonContract, alignment=Qt.AlignLeft)
        # button_layout2.addWidget(self.addButtonCIA)
        button_layout2.addWidget(self.addButtonCurrency,alignment=Qt.AlignLeft)
        button_layout2.setAlignment(Qt.AlignLeft)
   

 
       # Создаем горизонтальный макет и добавляем элементы
        layout = QVBoxLayout(self)

        # Создаем горизонтальный макет для минимальной и максимальной цены
        self.table.itemClicked.connect(self.open_file)
        # Добавляем таблицу и остальные элементы в макет
        layout.addLayout( self.butlayout)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addLayout(button_layout2)
  
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

        if self.role == "Гость":
            self.addButtonCurrency.hide()
        else:
            self.addButtonCurrency.show()

        if self.role == "Гость" or self.role == "Пользователь":
            self.addButtonContract.hide()
        else:
            self.addButtonCurrency.show()

    def show_current_purchase(self):
     
        if len(self.purchases_list) != 0:
            current_purchase = self.purchases_list[self.current_position]
            # Отображаем информацию о текущей записи в лейбле
            self.label.setText(f"Запись {self.current_position + 1} из {len(self.purchases_list)}")
            # Дополнительный код для отображения записи в таблице (замените на свой код)
            # self.table.setItem(row, column, QTableWidgetItem(str(current_purchase.some_property)))
        else:
            self.label.setText("Нет записей")
        # Очищаем таблицу перед добавлением новых данных
        self.table.setRowCount(0)
        if len(self.purchases_list) != 0:
            # Получаем текущую запись
            self.current_purchase = self.purchases_list[self.current_position]

            # Добавляем данные в виде "название поля - значение поля"
            self.add_section_to_table("Описание закупки")
            self.add_row_to_table("№ПП", str(current_purchase.Id))
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
            self.add_row_to_table("Количество единиц", str(current_purchase.quantity_units))
            self.add_row_to_table("НМЦК за единицу", str(current_purchase.nmck_per_unit))
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
            self.add_row_to_table("Извещение о закупке", str(current_purchase.notification_link))
            self.add_row_to_table("файл НМЦК", str(current_purchase.nmck_file))
            self.add_row_to_table("файл протокола", str(current_purchase.protocol_file))
            self.add_section_to_table("Определение НМЦК и ЦКЕИ")
            self.add_section_to_table("1.Определение НМЦК методом сопоставимых рыночных цен")
            tkp_proposal_dict = {}
            if current_purchase.TKPData:
                tkp_proposal_dict = json.loads(current_purchase.TKPData)
            if not tkp_proposal_dict:
                self.add_row_to_table("ТКП", "нет данных")
            else:
                for key, value in tkp_proposal_dict.items():
                        self.add_row_to_table(key, str(value))
            self.add_row_to_table("Количество запросов", str(current_purchase.QueryCount))
            self.add_row_to_table("Количество ответов", str(current_purchase.ResponseCount))
            self.add_row_to_table("Среднее значение цены", str(current_purchase.AveragePrice))
            self.add_row_to_table("Минимальная цена", str(current_purchase.MinPrice))
            self.add_row_to_table("Максимальная цена", str(current_purchase.MaxPrice))
            self.add_row_to_table("Среднее квадратичное отклонение", str(current_purchase.StandardDeviation))
            self.add_row_to_table("Коэффициент вариации", str(current_purchase.CoefficientOfVariation))
            self.add_row_to_table("НМЦК рыночная", str(current_purchase.NMCKMarket))
            self.add_row_to_table("Лимит финансирования", str(current_purchase.FinancingLimit))
            self.add_section_to_table("2.Определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информании")
            nmc_1_proposal_dict = {}
            if current_purchase.NMCK_1:
                nmc_1_proposal_dict = json.loads(current_purchase.NMCK_1)
            if not nmc_1_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен года его поставки", "нет данных")
            else:
                for key, value in nmc_1_proposal_dict.items():
                    self.add_row_to_table(key, str(value))
                    
            nmc_2_proposal_dict = {}
            if current_purchase.NMCK_2:
                nmc_2_proposal_dict = json.loads(current_purchase.NMCK_2)
            if not nmc_2_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен первого года периода строительства судна", "нет данных")
            else:
                for key, value in nmc_2_proposal_dict.items():
                    self.add_row_to_table(key, str(value))
                
            nmc_3_proposal_dict = {}
            if current_purchase.NMCK_3:
                nmc_3_proposal_dict = json.loads(current_purchase.NMCK_3)
            if not nmc_3_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен текущих лет на периода строительства судна", "нет данных")
            else:
                for key, value in nmc_3_proposal_dict.items():
                    self.add_row_to_table(key, str(value))
            self.add_section_to_table("3.Определение НМЦК затратным методом")
            self.add_row_to_table("Наименование организации", str(current_purchase.organization_name) if current_purchase.organization_name else "нет данных")
            self.add_row_to_table("Дата расчета", str(current_purchase.organization_name_date) if current_purchase.organization_name_date else "нет данных")
            self.add_row_to_table("Файл расчета", str(current_purchase.organization_name_file) if current_purchase.organization_name_file else "нет данных")
            self.add_section_to_table("4.Итоговое определение НМЦК с использованием нескольких методов")
            self.add_row_to_table("Способ направления запросов о предоставлении ценовой информации потенциальным исполнителям", 
                      str(current_purchase.method_direction_requests) if current_purchase.method_direction_requests else "нет данных")
            self.add_row_to_table("Способ использования общедоступной информации при осуществлении поиска ценовой информации в реестре государственных контрактов", 
                      str(current_purchase.method_usage_information) if current_purchase.method_usage_information else "нет данных")
            self.add_row_to_table("НМЦК, полученный различными способами в рамках метода сопостовимых рыночных цен", 
                      str(current_purchase.nmc_various_methods) if current_purchase.nmc_various_methods else "нет данных")
            self.add_row_to_table("НМЦК на основе затратного метода", 
                      str(current_purchase.nmc_cost_method) if current_purchase.nmc_cost_method else "нет данных")
            self.add_row_to_table("Цена сравнимой продукции, приведенная в соответствие к условиям закупки судна, НМЦК которого определяется", 
                      str(current_purchase.comparable_product_price) if current_purchase.comparable_product_price else "нет данных")
            self.add_row_to_table("НМЦК, полученная с применением двух методов: метода сопоставимых рыночных цен и затратного метода", 
                      str(current_purchase.nmc_two_methods) if current_purchase.nmc_two_methods else "нет данных")
            self.add_row_to_table("Файл 4 метода", 
                      str(current_purchase.file_4) if current_purchase.file_4 else "нет данных")

            # Получаем связанные записи из модели Contract
            self.contracts = Contract.select().where(Contract.purchase == current_purchase)
            for contract in self.contracts:
                
                self.add_section_to_table("Определение победителя")
                self.add_row_to_table("Общее количество заявок", str(contract.TotalApplications))
                self.add_row_to_table("Общее количество допущенных заявок", str(contract.AdmittedApplications))
                self.add_row_to_table("Общее количество отклоненных заявок", str(contract.RejectedApplications))
                price_proposal_dict = json.loads(contract.PriceProposal)
                for key, value in price_proposal_dict.items():
                    self.add_row_to_table(key, str(value))
                Applicant_dict = json.loads( contract.Applicant)
                for key, value in Applicant_dict.items():
                    self.add_row_to_table(key, str(value))
                Applicant_satatus = json.loads(contract.Applicant_satatus)
                for key, value in Applicant_satatus.items():
                    self.add_row_to_table(key, str(value))
                self.add_section_to_table("Заключение контракта")
                self.add_row_to_table("Победитель-исполнитель контракта", contract.WinnerExecutor)
                self.add_row_to_table("Заказчик по контракту", contract.ContractingAuthority)
                self.add_row_to_table("Идентификатор договора", contract.ContractIdentifier)
                self.add_row_to_table("Реестровый номер договора", contract.RegistryNumber)
                self.add_row_to_table("№ договора", contract.ContractNumber)
                self.add_row_to_table("Дата начала/подписания", str(contract.StartDate))
                self.add_row_to_table("Дата окончания/исполнения", str(contract.EndDate))
                self.add_row_to_table("Цена договора, руб.", str(contract.ContractPrice))
                self.add_row_to_table("Размер авансирования, руб./(%)", str(contract.AdvancePayment))
                self.add_row_to_table("Снижение НМЦК, руб.", str(contract.ReductionNMC))
                self.add_row_to_table("Снижение НМЦК, %", str(contract.ReductionNMCPercent))
                self.add_row_to_table("Протоколы определения поставщика (выписка)", contract.SupplierProtocol)
                self.add_row_to_table("Договор", contract.ContractFile)

            self.finalDetermination = FinalDetermination.select().where(FinalDetermination.purchase == current_purchase)
            for det in self.finalDetermination:
        
                self.add_section_to_table("Итоговое определение НМЦК с использованием нескольких методов.")
                self.add_row_to_table("Способ направления запросов о предоставлении ценовой информации", str(det.RequestMethod))
                self.add_row_to_table("Способ использования общедоступной информации", str(det.PublicInformationMethod))
                self.add_row_to_table("НМЦК, полученная различными способами", str(det.NMCObtainedMethods))
                self.add_section_to_table("НМЦК, полученная различными способами в рамках метода сопоставимых рыночных цен (анализа рынка),")
                self.add_row_to_table("НМЦК на основе затратного метода, руб. (в случае его применения)", str(det.CostMethodNMC))
                self.add_row_to_table("Цена сравнимой продукции, приведенная в соответствие к условиям закупки судна", str(det.ComparablePrice))
                self.add_row_to_table("НМЦК, полученная с применением двух методов", str(det.NMCMethodsTwo))
                self.add_section_to_table("Итоговое определение ЦКЕИ с использованием нескольких методов ЦКЕИ ")
                self.add_row_to_table("ЦКЕИ на основе метода сопоставимых рыночных цен )", str(det.CEICostMethod))
                self.add_row_to_table("ЦКЕИ, полученная с применением двух методов", str(det.CEIMethodsTwo))
          
            # if current_purchase.isChanged == True:
            #     self.currency = CurrencyRate.select().where(CurrencyRate.purchase == current_purchase)
            #     for curr in self.currency:
            #         self.add_section_to_table("Изминения валюты")
            #         self.add_row_to_table("Значение валюты", str(curr.CurrencyValue))
            #         self.add_row_to_table("Текущая валюта", str(curr.CurrentCurrency))
            #         self.add_row_to_table("Дата изменения значения валюты", str(curr.DateValueChanged))
            #         self.add_row_to_table("Дата курса валюты", str(curr.CurrencyRateDate))
            #         self.add_row_to_table("Предыдущая валюта", str(curr.PreviousCurrency))
        else:
            self.label.setText("Нет записей")

    def add_row_to_table(self, label_text, value_text):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        label_item = QTableWidgetItem()
        label_item.setText(label_text)
        label_item.setFlags(label_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        label_font = QFont()
        label_font.setPointSize(10)
        label_item.setFont(label_font)

        value_item = QTableWidgetItem()
        value_item.setText(value_text)
        value_item.setFlags(value_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        value_font = QFont()
        value_font.setPointSize(10)
        value_item.setFont(value_font)
       

        self.table.setItem(row_position, 0, label_item)
        self.table.setItem(row_position, 1, value_item)

        # # Adjust row height
        self.table.resizeRowsToContents()
        # max_height = 40  # Установите желаемую максимальную высоту здесь
        # self.table.setRowHeight(row_position, min(max_height, self.table.rowHeight(row_position)))

    def add_section_to_table(self, section_text):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        section_item = QTableWidgetItem(section_text)
        section_item.setFlags(section_item.flags() & ~Qt.ItemIsEditable)  # Заголовок не редактируемый
        # section_item.setBackground(QColor(200, 200, 200))  # Цвет фона заголовка
        section_item.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(row_position, 0, section_item)
        self.table.setSpan(row_position, 0, 1, 2)  # Занимаем два столбца


    def add_button_contract_clicked(self):
        
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
     
            self.insert_cont = InsertWidgetPanel(purchase_id,self,self.role,self.user,self.changer)
            self.insert_cont.show()
    
    def open_file(self, item):
        column = item.column()
        if column == 1:  # Проверяем, что кликнули по значению (колонка с путем к файлу)
            file_path = item.text()
            if os.path.isfile(file_path):
                # subprocess.Popen(['start', 'excel', file_path], shell=True)  # Открываем файл
                if file_path.lower().endswith(('.docx', '.doc')):
                    subprocess.Popen(['start', 'winword', file_path], shell=True)
                elif file_path.lower().endswith('.pdf'):
                    subprocess.Popen(['start', 'winword', file_path], shell=True)
                elif file_path.lower().endswith(('.xlsx', '.xls','.csv')):
                    subprocess.Popen(['start', 'excel', file_path], shell=True)
                else:
                    self.show_warning("Неизвестный формат файла", "Невозможно определить программу для открытия.")
            else:
                pass
            #    self.show_warning("Неизвестный формат файла", "Невозможно определить программу для открытия.")


    def add_button_tkp_clicked(self):
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
            self.tkp_shower = InsertWidgetNMCK(purchase_id,self)
            self.tkp_shower.show()
    
    def add_button_cia_clicked(self):
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
            self.cia_shower = InsertWidgetCEIA(purchase_id,self)
            self.cia_shower.show()
    def go_back(self):
        if self.window:
            self.main_win.stackedWidget.setCurrentIndex(0)
     

    # def file_exit(self):
    #     if len(self.purchases_list) != 0:
    #         self.current_purchase = self.purchases_list[self.current_position]
    #         purchase_id = self.current_purchase.Id
    #         self.curr_shower = InsertWidgetCurrency(purchase_id)
    #         self.curr_shower.show()
    # def update_currency(self):
    #     if len(self.purchases_list) != 0:
    #         self.current_purchase = self.purchases_list[self.current_position]
    #         purchase_id = self.current_purchase.Id
    #         self.curr_shower = InsertWidgetCurrency(purchase_id)
    #         self.curr_shower.show()
    
        
    def reload_data(self):
        self.purchases = Purchase.select()
        self.purchases_list = list(self.purchases)
        self.update()
        self.show_current_purchase()

    def reload_data_id(self,id):
        self.purchases = Purchase.select().where(Purchase.Id == id)
        self.purchases_list = list(self.purchases)
        self.update()
        self.show_current_purchase()
        

    def show_warning(self, title, text):
        warning = QMessageBox.warning(self, title, text, QMessageBox.Ok)
    def show_current_purchase_to_excel(self):
        wb = Workbook()
        ws = wb.active
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item_text = item.text()
                if item_text.startswith("Описание закупки") or \
                item_text.startswith("Определение НМЦК и ЦКЕИ") or \
                item_text.startswith("Определение победителя") or \
                item_text.startswith("Заключение контракта") or \
                item_text.startswith("1.Определение НМЦК методом сопоставимых рыночных цен") or \
                item_text.startswith("2.Определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информании") or \
                item_text.startswith("3.Определение НМЦК затратным методом") or \
                item_text.startswith("4.Итоговое определение НМЦК с использованием нескольких методов"):
                    ws.append([item_text])  # Добавляем заголовок раздела
                else:
                    label_item = self.table.item(row, 0)
                    value_item = self.table.item(row, 1)
                    if label_item is not None and value_item is not None:
                        label_text = label_item.text()
                        value_text = value_item.text()
                        if label_text and value_text:  # Проверка на пустую строку
                            ws.append([label_text, value_text])
        
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)
        self.purchases = Purchase.select()
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                wb.save(f'{selected_file}\данные_по_закупке №{self.current_purchase.RegistryNumber}.xlsx')
                QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
       

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec())