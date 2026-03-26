from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, FinalDetermination
from PySide6.QtCore import *
from PySide6.QtGui import QColor
import json
from PySide6.QtGui import QFont,QDesktopServices
from smtuIdle.insertPanel import InsertWidgetPanel
from smtuIdle.insertPanelContract import InsertPanelContract

# from InsertWidgetNMCK import InsertWidgetNMCK
# from InsertWidgetCEIA import InsertWidgetCEIA
from smtuIdle.parserV3 import delete_records_by_id
from PySide6.QtWidgets import QSizePolicy
import os
import subprocess
from openpyxl import Workbook
from PySide6.QtCore import Signal

from  locale import format_string,setlocale,LC_ALL
setlocale(LC_ALL, 'ru_RU.UTF-8')
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('database.db')
cursor = db.cursor()



class PurchasesWidget(QWidget):
    closingSignal = Signal()
    def __init__(self,main_window,role, user, changer):
        super().__init__()
        self.main_win = main_window
        self.selected_text = None
        self.role = role
        self.user = user
        self.symbol = ' ₽'
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
        self.deleteButton = QPushButton("Удалить запись", self)
        self.deleteButton.setFixedWidth(200)
        self.deleteButton.clicked.connect(self.remove_button_clicked)
        self.addButtonContract = QPushButton("Добавить обоснование НМЦК", self)
        self.BackButton.hide()
        self.addButtonContract.setMaximumWidth(400)
        
        self.addButtonTKP = QPushButton("Добавить результаты закупки", self)
        self.addButtonTKP.setMaximumWidth(400)
        # self.addButtonCIA = QPushButton("Добавить ЦКЕИ", self)
        self.addButtonCurrency= QPushButton("Экспорт в Еxcel Формуляра Закупок", self)
        self.addButtonCurrency.setMaximumWidth(300)
        self.label_form = QLabel() 
        self.label_form.setText("Редактирование Формуляра")

         # Устанавливаем обработчики событий для кнопок
        self.addButtonContract.clicked.connect(self.add_button_nmck_clicked)
        self.addButtonTKP.clicked.connect(self.add_button_contract_clicked)
        # self.addButtonCIA.clicked.connect(self.add_button_cia_clicked)

        self.addButtonCurrency.clicked.connect(self.show_current_purchase_to_excel)
        
         # Создаем метку
        self.label = QLabel("", self)
        # Устанавливаем обработчики событий для кнопок


        button_layout = QHBoxLayout()
        vertical_labels = QVBoxLayout()
        vertical_labels.addWidget(self.label_form)
        self.butlayout = QHBoxLayout()
        vertical_labels.addLayout(self.butlayout)
        self.butlayout.addWidget(self.addButtonContract )
        self.butlayout.addWidget(self.addButtonTKP )
        self.butlayout.setAlignment(Qt.AlignLeft)
        button_layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignHCenter)
        # Создаем горизонтальный макет и добавляем элементы
        button_layout2 = QHBoxLayout()

        # Добавляем первую кнопку
        button_layout2.addWidget(self.addButtonCurrency,alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addStretch()
        button_layout2.addWidget(self.deleteButton)
        # button_layout2.setAlignment(Qt.AlignCenter)

       # Создаем горизонтальный макет и добавляем элементы
        layout = QVBoxLayout(self)

        # Создаем горизонтальный макет для минимальной и максимальной цены
        self.table.itemClicked.connect(self.open_file)
        # Добавляем таблицу и остальные элементы в макет
        layout.addLayout( vertical_labels)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addLayout(button_layout2)
        
        # Получаем данные из базы данных и отображаем первую запись
        self.reload_data()

        if self.role == "Гость":
            self.addButtonCurrency.hide()
            self.label_form.hide()
        else:
            self.addButtonCurrency.show()
            self.label_form.hide()

        if self.role == "Гость" or self.role == "Пользователь":
            self.addButtonContract.hide()
            self.deleteButton.hide()
            self.addButtonTKP.hide()
        else:
            self.addButtonCurrency.show()
            self.deleteButton.show()
            self.addButtonTKP.show()
    def remove_button_clicked(self):
        # reply = QMessageBox.question(self, 'Подтверждение удаления', 'Вы точно хотите удалить выбранные записи?',
        #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        reply = QMessageBox()
        reply.setWindowTitle("Удаление")
        reply.setText('Вы точно хотите удалить текущую запись?')
        
        reply.addButton("Нет", QMessageBox.NoRole)
        reply.addButton("Да", QMessageBox.YesRole)
        result = reply.exec()
        if result == 1:
            if self.current_purchase.Id:
                success = delete_records_by_id([self.current_purchase.Id],user=self.user, role= self.role)
                if success:
                    self.main_win.updatePurchaseLabel()
                    self.changer.populate_table()
                    QMessageBox.information(self, "Успех", "Вы успешно удалили запись!")
                    self.reload_data()
                else:
                    QMessageBox.information(self,"Ошибка", "Ошибка при удалении записей")
                    
                  
        else:
            pass
    
    def closeEvent(self, event):
        self.closingSignal.emit()
        event.accept()
    def show_current_purchase(self):
     
        if len(self.purchases_list) != 0:
            current_purchase = self.purchases_list[self.current_position]

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
            self.add_row_to_table("Закон", current_purchase.PurchaseOrder if current_purchase.PurchaseOrder else "Нет данных")
            self.add_row_to_table("Реестровый номер", current_purchase.RegistryNumber if current_purchase.RegistryNumber else "Нет данных")
            self.add_row_to_table("Метод закупки", current_purchase.ProcurementMethod if current_purchase.ProcurementMethod else "Нет данных")
            self.add_row_to_table("Наименование закупки", current_purchase.PurchaseName if current_purchase.PurchaseName else "Нет данных")
            self.add_row_to_table("Предмет аукциона", current_purchase.AuctionSubject if current_purchase.AuctionSubject else "Нет данных")
            self.add_row_to_table("Код идентификации закупки", current_purchase.PurchaseIdentificationCode if current_purchase.PurchaseIdentificationCode else "Нет данных")
            self.add_row_to_table("Номер лота", str(current_purchase.LotNumber) if current_purchase.LotNumber is not None else "Нет данных")
            self.add_row_to_table("Наименование лота", current_purchase.LotName if current_purchase.LotName else "Нет данных")
            self.add_row_to_table("Начальная максимальная цена контракта", format_string("%.0f", current_purchase.InitialMaxContractPrice, grouping=True) + self.symbol if current_purchase.InitialMaxContractPrice is not None else "Нет данных")
            self.add_row_to_table("Валюта", current_purchase.Currency if current_purchase.Currency else "Нет данных")
            self.add_row_to_table("Начальная максимальная цена контракта в валюте", str(current_purchase.InitialMaxContractPriceInCurrency) if current_purchase.InitialMaxContractPriceInCurrency is not None else "Нет данных")
            self.add_row_to_table("Количество единиц", str(current_purchase.quantity_units) if current_purchase.quantity_units is not None else "Нет данных")
            self.add_row_to_table("НМЦК за единицу", format_string("%.0f",current_purchase.nmck_per_unit, grouping=True)+ self.symbol if current_purchase.nmck_per_unit is not None else "Нет данных")
            self.add_row_to_table("Валюта контракта", current_purchase.ContractCurrency if current_purchase.ContractCurrency else "Нет данных")
            self.add_row_to_table("Классификация ОКДП", current_purchase.OKDPClassification if current_purchase.OKDPClassification else "Нет данных")
            self.add_row_to_table("Классификация ОКПД", current_purchase.OKPDClassification if current_purchase.OKPDClassification else "Нет данных")
            self.add_row_to_table("Классификация ОКПД2", current_purchase.OKPD2Classification if current_purchase.OKPD2Classification else "Нет данных")
            self.add_row_to_table("Код позиции", current_purchase.PositionCode if current_purchase.PositionCode else "Нет данных")
            self.add_row_to_table("Наименование заказчика", current_purchase.CustomerName if current_purchase.CustomerName else "Нет данных")
            self.add_row_to_table("Организация закупки", current_purchase.ProcurementOrganization if current_purchase.ProcurementOrganization else "Нет данных")
            self.add_row_to_table("Дата размещения", str(current_purchase.PlacementDate) if current_purchase.PlacementDate else "Нет данных")
            self.add_row_to_table("Дата обновления", str(current_purchase.UpdateDate) if current_purchase.UpdateDate else "Нет данных")
            self.add_row_to_table("Этап закупки", current_purchase.ProcurementStage if current_purchase.ProcurementStage else "Нет данных")
            self.add_row_to_table("Особенности закупки", current_purchase.ProcurementFeatures if current_purchase.ProcurementFeatures else "Нет данных")
            self.add_row_to_table("Дата начала заявки", str(current_purchase.ApplicationStartDate) if current_purchase.ApplicationStartDate else "Нет данных")
            self.add_row_to_table("Дата окончания заявки", str(current_purchase.ApplicationEndDate) if current_purchase.ApplicationEndDate else "Нет данных")
            self.add_row_to_table("Дата аукциона", str(current_purchase.AuctionDate) if current_purchase.AuctionDate else "Нет данных")
            self.add_row_to_table("Извещение о закупке", str(current_purchase.notification_link) if current_purchase.notification_link else "Нет данных")
            self.add_row_to_table("Файл НМЦК", str(current_purchase.nmck_file) if current_purchase.nmck_file else "Нет данных")
            self.add_row_to_table("Файл протокола", str(current_purchase.protocol_file) if current_purchase.protocol_file else "Нет данных")
            self.add_section_to_table("Определение НМЦК и ЦКЕИ")
            self.add_section_to_table("1.Определение НМЦК методом сопоставимых рыночных цен")
            tkp_proposal_dict = {}
            if current_purchase.TKPData:
                tkp_proposal_dict = json.loads(current_purchase.TKPData)
            if not tkp_proposal_dict:
                self.add_row_to_table("ТКП", "нет данных")
            else:
                for key, value in tkp_proposal_dict.items():
                        self.add_row_to_table(key , format_string("%.0f" ,float(value),grouping=True) + self.symbol)
            self.add_row_to_table("Количество запросов", str(current_purchase.QueryCount) if current_purchase.QueryCount is not None else "Нет данных")
            self.add_row_to_table("Количество ответов", str(current_purchase.ResponseCount) if current_purchase.ResponseCount is not None else "Нет данных")
            self.add_row_to_table("Среднее значение цены", format_string("%.0f",current_purchase.AveragePrice,grouping=True) + self.symbol if current_purchase.AveragePrice is not None else "Нет данных")
            self.add_row_to_table("Минимальная цена", format_string("%.0f",current_purchase.MinPrice,grouping=True) + self.symbol if current_purchase.MinPrice is not None else "Нет данных")
            self.add_row_to_table("Максимальная цена", format_string("%.0f",current_purchase.MaxPrice,grouping=True) + self.symbol if current_purchase.MaxPrice is not None else "Нет данных")
            self.add_row_to_table("Среднее квадратичное отклонение", format_string("%.0f",current_purchase.StandardDeviation,grouping=True) + self.symbol if current_purchase.StandardDeviation is not None else "Нет данных")
            self.add_row_to_table("Коэффициент вариации %", format_string("%.0f",current_purchase.CoefficientOfVariation * 100,grouping=True) + ' %' if current_purchase.CoefficientOfVariation is not None else "Нет данных")
            self.add_row_to_table("НМЦК рыночная", format_string("%.0f",current_purchase.NMCKMarket,grouping=True) + self.symbol if current_purchase.NMCKMarket is not None else "Нет данных")
            self.add_row_to_table("Лимит финансирования", format_string("%.0f",current_purchase.FinancingLimit,grouping=True) + self.symbol if current_purchase.FinancingLimit is not None  else "Нет данных")
            self.add_section_to_table("2.Определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информации")
            nmc_1_proposal_dict = {}
            if current_purchase.NMCK_1:
                nmc_1_proposal_dict = json.loads(current_purchase.NMCK_1)
            if not nmc_1_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен года его поставки", "Нет данных")
            else:
                for key, value in nmc_1_proposal_dict.items():
                    self.add_row_to_table(key, format_string("%.0f" ,float(value),grouping=True) + self.symbol)
                    
            nmc_2_proposal_dict = {}
            if current_purchase.NMCK_2:
                nmc_2_proposal_dict = json.loads(current_purchase.NMCK_2)
            if not nmc_2_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен первого года периода строительства судна", "Нет данных")
            else:
                for key, value in nmc_2_proposal_dict.items():
                    self.add_row_to_table(key, format_string("%.0f" ,float(value),grouping=True) + self.symbol)
                
            nmc_3_proposal_dict = {}
            if current_purchase.NMCK_3:
                nmc_3_proposal_dict = json.loads(current_purchase.NMCK_3)
            if not nmc_3_proposal_dict:
                self.add_row_to_table("Цена судна приведенная к уровню цен текущих лет на периода строительства судна", "Нет данных")
            else:
                for key, value in nmc_3_proposal_dict.items():
                    self.add_row_to_table(key, format_string("%.0f" ,float(value),grouping=True) + self.symbol)
            self.add_section_to_table("3.Определение НМЦК затратным методом")
            self.add_row_to_table("Наименование организации", str(current_purchase.organization_name) if current_purchase.organization_name else "Нет данных")
            self.add_row_to_table("Дата расчета", str(current_purchase.organization_name_date) if current_purchase.organization_name_date else "Нет данных")
            self.add_row_to_table("Цена", format_string("%.0f",float(current_purchase.organization_price),grouping=True) + self.symbol if current_purchase.organization_price else "Нет данных")
            self.add_row_to_table("Файл расчета", str(current_purchase.organization_name_file) if current_purchase.organization_name_file else "Нет данных")
            self.add_section_to_table("4.Итоговое определение НМЦК с использованием нескольких методов")
            self.add_row_to_table("Способ направления запросов о предоставлении ценовой информации потенциальным исполнителям", 
                      str(current_purchase.method_direction_requests) if current_purchase.method_direction_requests else "Нет данных")
            self.add_row_to_table("Способ использования общедоступной информации при осуществлении поиска ценовой информации в реестре государственных контрактов", 
                      str(current_purchase.method_usage_information) if current_purchase.method_usage_information else "Нет данных")
            self.add_row_to_table("НМЦК, полученный различными способами в рамках метода сопоставимых рыночных цен", 
                      str(current_purchase.nmc_various_methods) if current_purchase.nmc_various_methods else "Нет данных")
            self.add_row_to_table("НМЦК на основе затратного метода", 
                      str(current_purchase.nmc_cost_method) if current_purchase.nmc_cost_method else "Нет данных")
            self.add_row_to_table("Цена сравнимой продукции, приведенная в соответствие к условиям закупки судна, НМЦК которого определяется", 
                      str(current_purchase.comparable_product_price) if current_purchase.comparable_product_price else "Нет данных")
            self.add_row_to_table("НМЦК, полученная с применением двух методов: метода сопоставимых рыночных цен и затратного метода", 
                      str(current_purchase.nmc_two_methods) if current_purchase.nmc_two_methods else "Нет данных")
            self.add_row_to_table("Файл итогового определения НМЦК с использованием нескольких методов", 
                      str(current_purchase.file_4) if current_purchase.file_4 else "Нет данных")

            # Получаем связанные записи из модели Contract
            self.contracts = Contract.select().where(Contract.purchase == current_purchase)
            for contract in self.contracts:
                
                self.add_section_to_table("Определение победителя")
                self.add_row_to_table("Общее количество заявок", str(contract.TotalApplications))
                self.add_row_to_table("Общее количество допущенных заявок", str(contract.AdmittedApplications))
                self.add_row_to_table("Общее количество отклоненных заявок", str(contract.RejectedApplications))
                if contract.PriceProposal:
                    price_proposal_data = json.loads(contract.PriceProposal)
                    if isinstance(price_proposal_data, dict):
                        for key, value in price_proposal_data.items():
                            try:
                                numeric_value = float(value)
                                self.add_row_to_table(key,
                                                      format_string('%.0f', numeric_value, grouping=True, symbol=''))
                            except (ValueError, TypeError):
                                self.add_row_to_table(key, str(value))
                    elif isinstance(price_proposal_data, list):
                        for idx, item in enumerate(price_proposal_data):
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    try:
                                        numeric_value = float(value)
                                        self.add_row_to_table(key, format_string('%.0f', numeric_value, grouping=True,
                                                                                 symbol=''))
                                    except (ValueError, TypeError):
                                        self.add_row_to_table(key, str(value))
                            else:
                                self.add_row_to_table(f"Предложение {idx + 1}", str(item))

                if contract.Applicant:
                    applicant_data = json.loads(contract.Applicant)
                    if isinstance(applicant_data, dict):
                        for key, value in applicant_data.items():
                            self.add_row_to_table(key, str(value))
                    elif isinstance(applicant_data, list):
                        for idx, item in enumerate(applicant_data):
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    self.add_row_to_table(key, str(value))
                            else:
                                self.add_row_to_table(f"Участник {idx + 1}", str(item))

                if contract.Applicant_satatus:
                    status_data = json.loads(contract.Applicant_satatus)
                    if isinstance(status_data, dict):
                        for key, value in status_data.items():
                            self.add_row_to_table(key, str(value))
                    elif isinstance(status_data, list):
                        for idx, item in enumerate(status_data):
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    self.add_row_to_table(key, str(value))
                            else:
                                self.add_row_to_table(f"Статус {idx + 1}", str(item))
                self.add_section_to_table("Заключение контракта")
                self.add_row_to_table("Победитель-исполнитель контракта", contract.WinnerExecutor)
                self.add_row_to_table("Заказчик по контракту", contract.ContractingAuthority)
                self.add_row_to_table("Идентификатор договора", contract.ContractIdentifier)
                self.add_row_to_table("Реестровый номер договора", contract.RegistryNumber)
                self.add_row_to_table("№ договора", contract.ContractNumber)
                self.add_row_to_table("Дата начала/подписания", str(contract.StartDate))
                self.add_row_to_table("Дата окончания/исполнения", str(contract.EndDate))
                self.add_row_to_table("Цена договора, руб.", format_string("%.0f", float(contract.ContractPrice), grouping=True) + self.symbol)
                self.add_row_to_table("Размер авансирования, руб", format_string("%.0f", float(contract.AdvancePayment), grouping=True) + self.symbol)
                self.add_row_to_table("Снижение НМЦК, руб.", format_string("%.0f", float(contract.ReductionNMC), grouping=True) + self.symbol)
                self.add_row_to_table("Снижение НМЦК, %", format_string("%.0f",float(contract.ReductionNMCPercent)) + " %")
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
          

        else:
            self.label.setText("Нет записи")

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
        
        if label_text == "Файл НМЦК" or label_text == "Файл протокола" or label_text == "Извещение о закупке" or label_text == "Файл расчета" or label_text == "Файл итогового определения НМЦК с использованием нескольких методов" or label_text == "Договор":
            if value_text != "Нет данных":
                # Установка цвета фона только для нужных ячеек
                label_item.setBackground(QColor(200, 255, 200))  # Светло-зеленый
                value_item.setBackground(QColor(200, 255, 200))  # Светло-зеленый
        if label_text == 'Реестровый номер':
            value_item.setData(Qt.UserRole, f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={self.purchases_list[self.current_position].RegistryNumber}&morphology=on&search-filter=Дате+размещения&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1')
            value_item.setForeground(Qt.blue)  # Голубой цвет текста
        
        self.table.setItem(row_position, 0, label_item)
        self.table.setItem(row_position, 1, value_item)
        

        # # Adjust row height
        self.table.resizeRowsToContents()
        max_height = 100
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, min(max_height, self.table.rowHeight(row)))

    def add_section_to_table(self, section_text):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        section_item = QTableWidgetItem(section_text)
        section_item.setFlags(section_item.flags() & ~Qt.ItemIsEditable)  # Заголовок не редактируемый
        # section_item.setBackground(QColor(200, 200, 200))  # Цвет фона заголовка
        section_item.setTextAlignment(Qt.AlignCenter)

        self.table.setItem(row_position, 0, section_item)
        self.table.setSpan(row_position, 0, 1, 2)  # Занимаем два столбца


    def add_button_nmck_clicked(self):
        
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
     
            self.insert_cont = InsertWidgetPanel(purchase_id,self,self.role,self.user,self.changer)
            # self.insert_cont.setParent(self)
            self.closingSignal.connect(self.insert_cont.close)
            self.insert_cont.show()

    def add_button_contract_clicked(self):
        
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
     
            self.insert_cont = InsertPanelContract(purchase_id,self,self.role,self.user,self.changer)
            # self.insert_cont.setParent(self)
            self.closingSignal.connect(self.insert_cont.close)
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
                    print('here3')
                else:
                    self.show_warning("Неизвестный формат файла", "Невозможно определить программу для открытия.")
            if "№" in item.text():
                print("Текст содержит символ '№'")
                url = item.data(Qt.UserRole)
                QDesktopServices.openUrl(QUrl(url))
            if "download" in item.text():
                url_for = item.text()
                QDesktopServices.openUrl(QUrl(url_for))

            else:
                pass
            #    self.show_warning("Неизвестный формат файла", "Невозможно определить программу для открытия.")



    def go_back(self):
        if hasattr(self.mainwin, 'navigate_back'):
            self.mainwin.navigate_back()
        else:
            self.mainwin.stackedWidget.setCurrentIndex(0)
     


        
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
                item_text.startswith("2.Определение НМЦК методом сопоставимых рыночных цен (анализа рынка) при использовании общедоступной информации") or \
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
                wb.save(f'{selected_file}\формуляр закупки {self.current_purchase.RegistryNumber}.xlsx')
                QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
       

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec())