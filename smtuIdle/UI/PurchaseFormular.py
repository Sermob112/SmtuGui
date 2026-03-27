from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, FinalDetermination
from PySide6.QtCore import *
from PySide6.QtGui import QColor
import json
from PySide6.QtGui import QFont,QDesktopServices
from smtuIdle.insertPanel import InsertWidgetPanel
from smtuIdle.insertPanelContract import InsertPanelContract
from PySide6.QtWidgets import QTreeWidgetItem
# from InsertWidgetNMCK import InsertWidgetNMCK
# from InsertWidgetCEIA import InsertWidgetCEIA
from smtuIdle.parserV3 import delete_records_by_id
from PySide6.QtWidgets import QSizePolicy
import os
import subprocess
from openpyxl import Workbook
from PySide6.QtCore import Signal
from smtuIdle.BD.models import Purchase, Contract, FinalDetermination, Customer, Vessel
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
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tree.setColumnWidth(0, 500)
        self.tree.setStyleSheet("""
                              /* Стилизуем только ячейки, не трогая branch (стрелочки) */
                    QTreeWidget::item {
                        border-bottom: 1px solid #e0e0e0;
                        border-right: 1px solid #e0e0e0;
                        padding: 4px;
                    }
                """)

        # Рисуем линии дерева (соединяющие ветви) - это системная настройка, а не QSS
        self.tree.setStyle(QStyleFactory.create('windows'))  # Часто помогает вернуть строгие линии и плюсики

        self.tree.itemClicked.connect(self.open_file) # Подключаем клик по ссылке

        # Настраиваем заголовок формы (Номер закупки)
        self.label_form = QLabel("")
        font_title = QFont()
        font_title.setPointSize(16)
        font_title.setBold(True)
        self.label_form.setFont(font_title)
        self.label_form.setAlignment(Qt.AlignHCenter)
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
        self.tree.itemClicked.connect(self.open_file)
        # Добавляем таблицу и остальные элементы в макет
        layout.addLayout( vertical_labels)
        layout.addWidget(self.tree)
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
        self.tree.clear()
        self.current_parent = None
        if not self.purchases:
            return
        if len(self.purchases_list) != 0:
            current_purchase = self.purchases_list[self.current_position]
            self.current_purchase = current_purchase

            if current_purchase.RegistryNumber:
                self.label_form.setText(f"Карточка закупки № {current_purchase.RegistryNumber}")
            else:
                self.label_form.setText("Карточка закупки")
            self.label_form.show()

            self.add_section_to_table('Общие сведения', expanded=True)
            self.add_row_to_table("№ПП", str(current_purchase.Id))
            self.add_row_to_table("Закон",
                                  current_purchase.PurchaseOrder if current_purchase.PurchaseOrder else "Нет данных")
            self.add_row_to_table("Реестровый номер",
                                  current_purchase.RegistryNumber if current_purchase.RegistryNumber else "Нет данных")
            self.add_row_to_table("Метод закупки",
                                  current_purchase.ProcurementMethod if current_purchase.ProcurementMethod else "Нет данных")
            self.add_row_to_table("Наименование закупки",
                                  current_purchase.PurchaseName if current_purchase.PurchaseName else "Нет данных")
            self.add_row_to_table("Предмет аукциона",
                                  current_purchase.AuctionSubject if current_purchase.AuctionSubject else "Нет данных")
            self.add_row_to_table("Код идентификации закупки",
                                  current_purchase.PurchaseIdentificationCode if current_purchase.PurchaseIdentificationCode else "Нет данных")
            self.add_row_to_table("Номер лота",
                                  str(current_purchase.LotNumber) if current_purchase.LotNumber is not None else "Нет данных")
            self.add_row_to_table("Наименование лота",
                                  current_purchase.LotName if current_purchase.LotName else "Нет данных")
            self.add_row_to_table("Начальная максимальная цена контракта",
                                  format_string("%.0f", current_purchase.InitialMaxContractPrice,
                                                grouping=True) + self.symbol if current_purchase.InitialMaxContractPrice is not None else "Нет данных")
            self.add_row_to_table("Валюта", current_purchase.Currency if current_purchase.Currency else "Нет данных")
            self.add_row_to_table("Начальная максимальная цена контракта в валюте",
                                  str(current_purchase.InitialMaxContractPriceInCurrency) if current_purchase.InitialMaxContractPriceInCurrency is not None else "Нет данных")
            self.add_row_to_table("Количество единиц",
                                  str(current_purchase.quantity_units) if current_purchase.quantity_units is not None else "Нет данных")
            self.add_row_to_table("НМЦК за единицу", format_string("%.0f", current_purchase.nmck_per_unit,
                                                                   grouping=True) + self.symbol if current_purchase.nmck_per_unit is not None else "Нет данных")
            self.add_row_to_table("Валюта контракта",
                                  current_purchase.ContractCurrency if current_purchase.ContractCurrency else "Нет данных")
            self.add_row_to_table("Классификация ОКДП",
                                  current_purchase.OKDPClassification if current_purchase.OKDPClassification else "Нет данных")
            self.add_row_to_table("Классификация ОКПД",
                                  current_purchase.OKPDClassification if current_purchase.OKPDClassification else "Нет данных")
            self.add_row_to_table("Классификация ОКПД2",
                                  current_purchase.OKPD2Classification if current_purchase.OKPD2Classification else "Нет данных")
            self.add_row_to_table("Код позиции",
                                  current_purchase.PositionCode if current_purchase.PositionCode else "Нет данных")
            self.add_row_to_table("Наименование заказчика",
                                  current_purchase.CustomerName if current_purchase.CustomerName else "Нет данных")
            self.add_row_to_table("Организация закупки",
                                  current_purchase.ProcurementOrganization if current_purchase.ProcurementOrganization else "Нет данных")
            self.add_row_to_table("Дата размещения",
                                  str(current_purchase.PlacementDate) if current_purchase.PlacementDate else "Нет данных")
            self.add_row_to_table("Дата обновления",
                                  str(current_purchase.UpdateDate) if current_purchase.UpdateDate else "Нет данных")
            self.add_row_to_table("Этап закупки",
                                  current_purchase.ProcurementStage if current_purchase.ProcurementStage else "Нет данных")
            self.add_row_to_table("Особенности закупки",
                                  current_purchase.ProcurementFeatures if current_purchase.ProcurementFeatures else "Нет данных")
            self.add_row_to_table("Дата начала заявки",
                                  str(current_purchase.ApplicationStartDate) if current_purchase.ApplicationStartDate else "Нет данных")
            self.add_row_to_table("Дата окончания заявки",
                                  str(current_purchase.ApplicationEndDate) if current_purchase.ApplicationEndDate else "Нет данных")
            self.add_row_to_table("Дата аукциона",
                                  str(current_purchase.AuctionDate) if current_purchase.AuctionDate else "Нет данных")
            self.add_row_to_table("Извещение о закупке",
                                  str(current_purchase.notification_link) if current_purchase.notification_link else "Нет данных")
            self.add_row_to_table("Файл НМЦК",
                                  str(current_purchase.nmck_file) if current_purchase.nmck_file else "Нет данных")
            self.add_row_to_table("Файл протокола",
                                  str(current_purchase.protocol_file) if current_purchase.protocol_file else "Нет данных")

            self.add_section_to_table("Определение НМЦК и ЦКЕИ")
            self.add_section_to_table("1.Определение НМЦК методом сопоставимых рыночных цен")
            if current_purchase.TKPData and str(current_purchase.TKPData).strip() not in ("", "None", "-", "[]", "{}"):
                try:
                    tkp_parsed = json.loads(current_purchase.TKPData)
                    node = QTreeWidgetItem(self.current_parent)
                    node.setText(0, "ТКП")
                    self.add_json_to_tree(node, tkp_parsed)
                except json.JSONDecodeError:
                    self.add_row_to_table("ТКП", str(current_purchase.TKPData))
            else:
                self.add_row_to_table("ТКП", "Нет данных")
            self.add_row_to_table("Количество запросов",
                                  str(current_purchase.QueryCount) if current_purchase.QueryCount is not None else "Нет данных")
            self.add_row_to_table("Количество ответов",
                                  str(current_purchase.ResponseCount) if current_purchase.ResponseCount is not None else "Нет данных")
            self.add_row_to_table("Среднее значение цены", format_string("%.0f", current_purchase.AveragePrice,
                                                                         grouping=True) + self.symbol if current_purchase.AveragePrice is not None else "Нет данных")
            self.add_row_to_table("Минимальная цена", format_string("%.0f", current_purchase.MinPrice,
                                                                    grouping=True) + self.symbol if current_purchase.MinPrice is not None else "Нет данных")
            self.add_row_to_table("Максимальная цена", format_string("%.0f", current_purchase.MaxPrice,
                                                                     grouping=True) + self.symbol if current_purchase.MaxPrice is not None else "Нет данных")
            self.add_row_to_table("Среднее квадратичное отклонение",
                                  format_string("%.0f", current_purchase.StandardDeviation,
                                                grouping=True) + self.symbol if current_purchase.StandardDeviation is not None else "Нет данных")
            self.add_row_to_table("Коэффициент вариации %",
                                  format_string("%.0f", current_purchase.CoefficientOfVariation * 100,
                                                grouping=True) + ' %' if current_purchase.CoefficientOfVariation is not None else "Нет данных")
            self.add_row_to_table("НМЦК рыночная", format_string("%.0f", current_purchase.NMCKMarket,
                                                                 grouping=True) + self.symbol if current_purchase.NMCKMarket is not None else "Нет данных")
            self.add_row_to_table("Лимит финансирования", format_string("%.0f", current_purchase.FinancingLimit,
                                                                        grouping=True) + self.symbol if current_purchase.FinancingLimit is not None else "Нет данных")

            self.add_section_to_table(
                "2.Определение НМЦК методом сопоставимых рыночных цен при использовании общедоступной информации")

            # Вспомогательная функция для безопасного парсинга полей НМЦК
            def parse_nmck(field_data, label):
                if field_data and str(field_data).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed = json.loads(field_data)
                        # Создаем узел с заголовком и передаем в рекурсивную функцию
                        node = QTreeWidgetItem(self.current_parent)
                        node.setText(0, label)
                        self.add_json_to_tree(node, parsed)
                    except json.JSONDecodeError:
                        self.add_row_to_table(label, str(field_data))

            parse_nmck(current_purchase.NMCK_1, "Цена судна (год поставки)")
            parse_nmck(current_purchase.NMCK_2, "Цена судна (первый год строительства)")
            parse_nmck(current_purchase.NMCK_3, "Цена судна (текущие годы)")

            self.add_section_to_table("3.Определение НМЦК затратным методом")
            self.add_row_to_table("Наименование организации",
                                  str(current_purchase.organization_name) if current_purchase.organization_name else "Нет данных")
            self.add_row_to_table("Дата расчета",
                                  str(current_purchase.organization_name_date) if current_purchase.organization_name_date else "Нет данных")
            self.add_row_to_table("Цена", format_string("%.0f", float(current_purchase.organization_price),
                                                        grouping=True) + self.symbol if current_purchase.organization_price else "Нет данных")
            self.add_row_to_table("Файл расчета",
                                  str(current_purchase.organization_name_file) if current_purchase.organization_name_file else "Нет данных")

            self.add_section_to_table("4.Итоговое определение НМЦК с использованием нескольких методов")
            self.add_row_to_table("Способ направления запросов",
                                  str(current_purchase.method_direction_requests) if current_purchase.method_direction_requests else "Нет данных")
            self.add_row_to_table("Способ использования общедоступной информации",
                                  str(current_purchase.method_usage_information) if current_purchase.method_usage_information else "Нет данных")
            self.add_row_to_table("НМЦК различными способами",
                                  str(current_purchase.nmc_various_methods) if current_purchase.nmc_various_methods else "Нет данных")
            self.add_row_to_table("НМЦК затратным методом",
                                  str(current_purchase.nmc_cost_method) if current_purchase.nmc_cost_method else "Нет данных")
            self.add_row_to_table("Цена сравнимой продукции",
                                  str(current_purchase.comparable_product_price) if current_purchase.comparable_product_price else "Нет данных")
            self.add_row_to_table("НМЦК двумя методами",
                                  str(current_purchase.nmc_two_methods) if current_purchase.nmc_two_methods else "Нет данных")
            self.add_row_to_table("Файл итогового определения",
                                  str(current_purchase.file_4) if current_purchase.file_4 else "Нет данных")

            # FINAL DETERMINATION
            self.finalDetermination = FinalDetermination.select().where(FinalDetermination.purchase == current_purchase)
            for det in self.finalDetermination:
                self.add_section_to_table("Итоговое определение НМЦК с использованием нескольких методов.")
                self.add_row_to_table("Способ направления запросов о предоставлении ценовой информации",
                                      str(det.RequestMethod))
                self.add_row_to_table("Способ использования общедоступной информации", str(det.PublicInformationMethod))
                self.add_row_to_table("НМЦК, полученная различными способами", str(det.NMCObtainedMethods))
                self.add_row_to_table("НМЦК на основе затратного метода", str(det.CostMethodNMC))
                self.add_row_to_table("Цена сравнимой продукции", str(det.ComparablePrice))
                self.add_row_to_table("НМЦК, полученная с применением двух методов", str(det.NMCMethodsTwo))
                self.add_row_to_table("ЦКЕИ на основе метода", str(det.CEICostMethod))
                self.add_row_to_table("ЦКЕИ, полученная с применением двух методов", str(det.CEIMethodsTwo))

            # JSON ПОЛЯ ЗАКУПКИ
            json_fields = [
                ("Общая информация", current_purchase.common_info_json),
                ("Документы", current_purchase.documents_json),
                ("Журнал событий", current_purchase.event_log_json),
                ("Результаты поставщика", current_purchase.supplier_result_json),
                ("Список лотов", current_purchase.lots_json),
                ("Протоколы", current_purchase.protocols_json),
                ("Сведения о договорах", current_purchase.contracts_info_json),
                ("Изменения", current_purchase.changes_json)
            ]
            for section_name, json_string in json_fields:
                self.add_section_to_table(section_name, expanded=False)
                if json_string and str(json_string).strip() not in ("", "None", "-"):
                    try:
                        self.add_json_to_tree(self.current_parent, json.loads(json_string))
                    except json.JSONDecodeError:
                        self.add_row_to_table("Данные", str(json_string))
                else:
                    self.add_row_to_table("Данные", "Нет данных")

            # =========================================================
            # СВЯЗАННЫЕ ДАННЫЕ (ЗАКАЗЧИК, КОНТРАКТЫ, СУДА) - ИСПРАВЛЕННЫЙ БЛОК
            # =========================================================
            self.add_section_to_table('Связанные документы', expanded=True)
            links_parent = self.current_parent  # Сохраняем родительский узел

            # 1. ЗАКАЗЧИК
            if current_purchase.CustomerName:
                customer = Customer.select().where(Customer.name == current_purchase.CustomerName).first()
                if customer:
                    customer_node = QTreeWidgetItem(links_parent)
                    customer_node.setText(0, f"Заказчик: {customer.name}")
                    customer_node.setFirstColumnSpanned(True)
                    font_c = QFont()
                    font_c.setBold(True)
                    customer_node.setFont(0, font_c)
                    customer_node.setBackground(0, QColor(240, 240, 240))

                    link_item = QTreeWidgetItem(customer_node)
                    link_item.setText(0, 'Перейти в карточку заказчика')
                    link_item.setText(1, f"ID: {customer.id}")
                    link_item.setData(1, Qt.UserRole, f"GOTO_CUSTOMER:{customer.id}")
                    link_item.setForeground(1, Qt.blue)
                    font_link = QFont()
                    font_link.setUnderline(True)
                    link_item.setFont(1, font_link)

                    QTreeWidgetItem(customer_node, ['ИНН', str(customer.inn)])
                    QTreeWidgetItem(customer_node, ['КПП', str(customer.kpp)])

            # 2. КОНТРАКТЫ И ИХ СУДА (по RegistryNumber)
            if current_purchase.RegistryNumber:
                contracts = Contract.select().where(Contract.RegistryNumber == current_purchase.RegistryNumber)
                if contracts.exists():
                    for contract in contracts:
                        # Ветка для контракта
                        c_title = f'Контракт № {contract.ContractNumber}' if contract.ContractNumber else f'Контракт ID {contract.Id}'
                        contract_node = QTreeWidgetItem(links_parent)
                        contract_node.setText(0, c_title)
                        contract_node.setFirstColumnSpanned(True)
                        font_c = QFont()
                        font_c.setBold(True)
                        contract_node.setFont(0, font_c)
                        contract_node.setBackground(0, QColor(240, 240, 240))

                        # Ссылка на контракт
                        link_item = QTreeWidgetItem(contract_node)
                        link_item.setText(0, 'Перейти в карточку контракта')
                        link_item.setText(1, c_title)
                        link_item.setData(1, Qt.UserRole, f"GOTO_CONTRACT:{contract.Id}")
                        link_item.setForeground(1, Qt.blue)
                        font_link = QFont()
                        font_link.setUnderline(True)
                        link_item.setFont(1, font_link)

                        # Превью контракта
                        QTreeWidgetItem(contract_node, ['Победитель', str(contract.WinnerExecutor)])
                        QTreeWidgetItem(contract_node, ['Заказчик', str(contract.ContractingAuthority)])
                        if contract.ContractPrice is not None:
                            QTreeWidgetItem(contract_node, ['Цена',
                                                            f"{format_string('%.2f', float(contract.ContractPrice), grouping=True)} {self.symbol}"])

                        # БЕЗОПАСНЫЙ парсинг JSON-полей контракта прямо внутрь этой ветки
                        for label, field_data in [
                            ("Ценовое предложение", contract.PriceProposal),
                            ("Заявитель", contract.Applicant),
                            ("Статус заявителя", contract.Applicant_satatus)
                        ]:
                            if field_data and str(field_data).strip() not in ("", "None", "-", "[]", "{}"):
                                try:
                                    parsed_data = json.loads(field_data)
                                    # Создаем временную секцию для add_json_to_tree
                                    json_node = QTreeWidgetItem(contract_node)
                                    json_node.setText(0, label)
                                    self.add_json_to_tree(json_node, parsed_data)
                                except json.JSONDecodeError:
                                    QTreeWidgetItem(contract_node, [label, str(field_data)])

                        # 3. СУДА ПО КОНТРАКТУ
                        try:
                            # Ищем судно по связи с контрактом
                            vessels = Vessel.select().where(Vessel.contract == contract)
                            for vessel in vessels:
                                v_title = f'Судно (Проект {vessel.ship_project})' if vessel.ship_project else f'Судно ID {vessel.id}'
                                vessel_node = QTreeWidgetItem(contract_node)  # Вкладываем в контракт
                                vessel_node.setText(0, v_title)
                                vessel_node.setFirstColumnSpanned(True)
                                vessel_node.setFont(0, font_c)
                                vessel_node.setBackground(0, QColor(250, 250, 250))

                                v_link = QTreeWidgetItem(vessel_node)
                                v_link.setText(0, 'Перейти в карточку судна')
                                v_link.setText(1, v_title)
                                v_link.setData(1, Qt.UserRole, f"GOTO_VESSEL:{vessel.id}")
                                v_link.setForeground(1, Qt.blue)
                                v_link.setFont(1, font_link)

                                QTreeWidgetItem(vessel_node, ['ИМО', str(vessel.imo_number)])
                                QTreeWidgetItem(vessel_node, ['Тип', str(vessel.ship_type)])
                        except Exception as e:
                            pass
        else:
            self.label.setText("Нет записи")
            self.label_form.setText("Карточка закупки")
            self.label_form.show()

    def add_row_to_table(self, label_text, value_text):
        # Если данных нет - пишем "Нет данных"
        if value_text is None or str(value_text).strip() in ("", "None", "-"):
            value_text = "Нет данных"
        else:
            value_text = str(value_text)

        # Кладем строку в текущую группу (если она создана), иначе в корень
        if hasattr(self, 'current_parent') and self.current_parent:
            item = QTreeWidgetItem(self.current_parent)
        else:
            item = QTreeWidgetItem(self.tree)

        item.setText(0, str(label_text))
        item.setText(1, value_text)

        font = QFont()
        font.setPointSize(10)
        item.setFont(0, font)
        item.setFont(1, font)

        # Подсветка ссылок синим цветом
        link_fields = ['Реестровый номер', 'Файл обоснования НМЦК', 'Файл протокола',
                       'Ссылка на закупку', 'Файл контракта', 'Файл ответа']

        if label_text in link_fields and value_text != "Нет данных":
            item.setForeground(1, Qt.blue)
            font_link = QFont()
            font_link.setPointSize(10)
            font_link.setUnderline(True)
            item.setFont(1, font_link)

            # Для реестрового номера вшиваем ссылку
            if label_text == 'Реестровый номер':
                link = f"https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={value_text}&morphology=on"
                item.setData(1, Qt.UserRole, link)

    def add_json_to_tree(self, parent_item, json_data, parent_key=""):
        # Словарь для перевода ключей парсера на человеческий язык
        key_translations = {
            "title": "Заголовок",
            "items": "Элементы",
            "hrefs": "Ссылки",
            "all_hrefs": "Все ссылки",
            "header": "Название группы",
            "kind": "Тип",
            "kv": "Значение",
            "type": "Тип документа",
            "sign_link": "Ссылка на подпись",
            "sign_url": "Ссылка на подпись",
            "table_standalone": "Отдельная таблица",
            "url": "Ссылка",
            "parsed_table": "Табличные данные",
            "rows": "Строки таблицы",
            "headers": "Заголовки колонок",
            "doc_name": "Название документа",
            "files": "Файлы",
            "links": "Связанные ссылки",
            "text": "Текст"
        }

        if not json_data:
            return

        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key == "null" or key is None:
                    key = "Параметр"

                # ПЕРЕВОДИМ ИЛИ ФОРМАТИРУЕМ КЛЮЧ
                if key in key_translations:
                    display_key = key_translations[key]
                else:
                    # Если ключа нет в словаре: заменяем "_" на пробел и делаем первую букву заглавной
                    # Например: "some_field_name" -> "Some field name"
                    display_key = str(key).replace("_", " ").capitalize()

                if isinstance(value, (dict, list)):
                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, display_key)
                    font = QFont()
                    font.setBold(True)
                    child.setFont(0, font)
                    self.add_json_to_tree(child, value, key)
                else:
                    if key == "text":
                        parent_item.setText(1, str(value))
                    elif key in ("url", "sign_url", "sign_link"):
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, display_key)
                        child.setText(1, str(value))
                        child.setForeground(1, Qt.blue)
                        font_link = QFont()
                        font_link.setUnderline(True)
                        child.setFont(1, font_link)
                        child.setData(1, Qt.UserRole, str(value))
                    elif key in ("all_hrefs", "hrefs"):
                        pass
                    else:
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, display_key)
                        child.setText(1, str(value) if value is not None else "Нет данных")


        elif isinstance(json_data, list):
            for idx, item in enumerate(json_data):
                if isinstance(item, (dict, list)):
                    child_name = f"Запись {idx + 1}"
                    if parent_key == "headers":
                        child_name = f"Колонка {idx + 1}"
                    elif parent_key in ("all_hrefs", "hrefs"):
                        child_name = f"Ссылка {idx + 1}"

                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, child_name)

                    if parent_key in ("all_hrefs", "hrefs"):
                        child.setText(1, str(item))
                        child.setForeground(1, Qt.blue)
                        font_link = QFont()
                        font_link.setUnderline(True)
                        child.setFont(1, font_link)
                        child.setData(1, Qt.UserRole, str(item))
                    else:
                        self.add_json_to_tree(child, item, parent_key)
                else:
                    if parent_key == "headers":
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, f"Колонка {idx + 1}")
                        child.setText(1, str(item) if item is not None else "Нет данных")
                    else:
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, f"Элемент {idx + 1}")
                        child.setText(1, str(item) if item is not None else "Нет данных")
        else:
            parent_item.setText(1, str(json_data))

    def add_section_to_table(self, section_text, expanded=False):
        # Создаем родительскую ветку (Группу)
        self.current_parent = QTreeWidgetItem(self.tree)
        self.current_parent.setText(0, section_text)
        self.current_parent.setFirstColumnSpanned(True)  # Растягиваем на всю ширину

        # Устанавливаем, развернута группа или нет (в зависимости от переданного параметра)
        self.current_parent.setExpanded(expanded)

        # Стилизация заголовка группы
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.current_parent.setFont(0, font)
        # self.current_parent.setBackground(0, QColor(230, 230, 230))


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

    def open_file(self, item, column):
        if column == 1:
            filepath = item.text(1)
            if not filepath:
                return

            # Получаем скрытые данные (метку перехода или ссылку), которые мы зашили в Qt.UserRole
            url_or_cmd = item.data(1, Qt.UserRole)

            # 1. ПРОВЕРКА НА ВНУТРЕННИЕ ПЕРЕХОДЫ МЕЖДУ ФОРМУЛЯРАМИ
            if url_or_cmd and isinstance(url_or_cmd, str) and url_or_cmd.startswith("GOTO_"):
                command, record_id = url_or_cmd.split(":")
                record_id = int(record_id)

                # Сохраняем текущую страницу в историю, чтобы кнопка "Назад" корректно работала
                if hasattr(self.main_win, 'history'):
                    self.main_win.history.append(self.main_win.stackedWidget.currentIndex())

                # Переход в зависимости от команды
                if command == "GOTO_CUSTOMER":
                    # Передаем id в формуляр и переключаем страницу
                    self.main_win.customerFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(
                        11)  # Замените 11 на реальный индекс страницы заказчиков в MainWindow

                elif command == "GOTO_CONTRACT":
                    self.main_win.contractFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(8)  # Замените 8 на реальный индекс страницы контрактов

                elif command == "GOTO_VESSEL":
                    self.main_win.vesselFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(13)  # Замените 13 на реальный индекс страницы судов

                return  # Прерываем функцию, так как это был внутренний переход

            # 2. ПРОВЕРКА НА ОТКРЫТИЕ ФАЙЛОВ И ВНЕШНИХ ССЫЛОК (Оригинальная логика)
            if os.path.isfile(filepath):
                if filepath.lower().endswith(('.docx', '.doc')):
                    subprocess.Popen(['start', 'winword', filepath], shell=True)
                elif filepath.lower().endswith('.pdf'):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
                elif filepath.lower().endswith(('.xlsx', '.xls', '.csv')):
                    subprocess.Popen(['start', 'excel', filepath], shell=True)
            else:
                if url_or_cmd and ('http' in url_or_cmd or 'zakupki' in url_or_cmd):
                    QDesktopServices.openUrl(QUrl(url_or_cmd))
                elif 'http' in filepath or 'zakupki' in filepath:
                    QDesktopServices.openUrl(QUrl(filepath))
                elif 'download' in filepath:
                    # Предполагаем, что для загрузки используется текст элемента
                    url_for = item.text(1)
                    QDesktopServices.openUrl(QUrl(url_for))



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

        root = self.tree.invisibleRootItem()
        # Проходим по всем группам
        for i in range(root.childCount()):
            parent_item = root.child(i)
            ws.append([parent_item.text(0)])  # Имя группы

            # Проходим по строкам внутри группы
            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                ws.append([child_item.text(0), child_item.text(1)])

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