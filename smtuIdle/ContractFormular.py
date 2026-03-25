from PySide6.QtWidgets import *
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, FinalDetermination
from PySide6.QtCore import *
from PySide6.QtGui import QColor
import json
from PySide6.QtGui import QFont,QDesktopServices
from insertPanel import InsertWidgetPanel
from insertPanelContract import InsertPanelContract

from InsertWidgetNMCK import InsertWidgetNMCK
from InsertWidgetCEIA import InsertWidgetCEIA
from parserV3 import delete_records_by_id
from PySide6.QtWidgets import QSizePolicy
import os
import subprocess
from openpyxl import Workbook
from  locale import format_string,setlocale,LC_ALL
setlocale(LC_ALL, 'ru_RU.UTF-8')
# Код вашей модели остается таким же, как вы предоставили в предыдущем сообщении.



# Создаем соединение с базой данных
db = SqliteDatabase('database.db')
cursor = db.cursor()



class ContractFormularWidget(QWidget):
    def __init__(self,main_window,role, user, changer):
        super().__init__()
        self.main_win = main_window
        self.selected_text = None
        self.role = role
        self.symbol = ' ₽'
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
        # self.BackButton = QPushButton("Назад", self)
        # self.BackButton.clicked.connect(self.go_back)
        # self.deleteButton = QPushButton("Удалить запись", self)
        # self.deleteButton.setFixedWidth(200)
        # self.deleteButton.clicked.connect(self.remove_button_clicked)
        # self.addButtonContract = QPushButton("Добавить обоснование НМЦК", self)
        # self.BackButton.hide()
        # self.addButtonContract.setMaximumWidth(400)
        
        # self.addButtonTKP = QPushButton("Добавить результаты закупки", self)
        # self.addButtonTKP.setMaximumWidth(400)
        # self.addButtonCIA = QPushButton("Добавить ЦКЕИ", self)
        self.addButtonCurrency= QPushButton("Экспорт в Еxcel Формуляра Контрактов", self)
        self.addButtonCurrency.setMaximumWidth(300)
        self.label_form = QLabel() 
        self.label_form.setText("Редактирование Формуляра")

         # Устанавливаем обработчики событий для кнопок
        # self.addButtonContract.clicked.connect(self.add_button_nmck_clicked)
        # self.addButtonTKP.clicked.connect(self.add_button_contract_clicked)
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
        # self.butlayout.addWidget(self.addButtonContract )
        # self.butlayout.addWidget(self.addButtonTKP )
        self.butlayout.setAlignment(Qt.AlignLeft)
        button_layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignHCenter)
        # Создаем горизонтальный макет и добавляем элементы
        button_layout2 = QHBoxLayout()

        
        # button_layout2.addWidget(self.addButtonTKP)
        # button_layout2.addWidget(self.addButtonContract, alignment=Qt.AlignLeft)
        # button_layout2.addWidget(self.addButtonTKP,alignment=Qt.AlignLeft)
        # button_layout2.addWidget(self.addButtonCIA)
        # Создаем слой для центрирования
       # Создаем слой для центрирования
                
        # Добавляем первую кнопку
        button_layout2.addWidget(self.addButtonCurrency,alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addStretch()
        # button_layout2.addWidget(self.deleteButton)
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
            self.label_form.hide()
        else:
            self.addButtonCurrency.show()
            self.label_form.show()
        # if self.role == "Гость" or self.role == "Пользователь":
        #     self.addButtonContract.hide()
        #     self.deleteButton.hide()
        # else:
        #     self.addButtonCurrency.show()
        #     self.deleteButton.show()
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
                    
                    QMessageBox.information(self, "Успех", "Вы успешно удалили запись!")
                    self.reload_data()
                else:
                    QMessageBox.information(self,"Ошибка", "Ошибка при удалении записей")
                    
                  
        else:
            pass

    def _render_json_section(self, data, prefix: str = ""):
        """
        Рекурсивно рендерит dict/list из JSON-поля в строки таблицы.
        Останавливается на глубине 3 уровня чтобы не перегружать таблицу.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                label = f"{prefix}{key}" if not prefix else f"  {prefix}{key}"
                if isinstance(value, (dict, list)):
                    self.add_section_to_table(label)
                    self._render_json_section(value)
                else:
                    self.add_row_to_table(label, str(value) if value is not None else "—")
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    self._render_json_section(item, prefix=f"{prefix}")
                else:
                    self.add_row_to_table(f"{prefix}[{idx}]", str(item) if item is not None else "—")
    def show_current_purchase(self):
        self.table.setRowCount(0)

        if not self.purchases_list:
            self.label.setText("Нет записей")
            return

        current_purchase = self.purchases_list[self.current_position]
        self.current_purchase = current_purchase

        # ── Описание закупки ──────────────────────────────────
        self.add_section_to_table("Описание закупки")
        self.add_row_to_table("№ПП", str(current_purchase.Id))
        self.add_row_to_table("Реестровый номер", current_purchase.RegistryNumber or "Нет данных")
        self.add_row_to_table("Наименование закупки", current_purchase.PurchaseName or "Нет данных")

        self.contracts = Contract.select().where(Contract.purchase == current_purchase)

        for contract in self.contracts:

            # ── Определение победителя ────────────────────────
            self.add_section_to_table("Определение победителя")
            self.add_row_to_table("Общее количество заявок", str(contract.TotalApplications or "—"))
            self.add_row_to_table("Допущено заявок", str(contract.AdmittedApplications or "—"))
            self.add_row_to_table("Отклонено заявок", str(contract.RejectedApplications or "—"))

            # PriceProposal
            price_proposal = self._parse_json_field(contract.PriceProposal)
            if isinstance(price_proposal, dict):
                for key, value in price_proposal.items():
                    try:
                        self.add_row_to_table(key, format_string("%.0f", float(value), grouping=True) + self.symbol)
                    except (ValueError, TypeError):
                        self.add_row_to_table(key, str(value))
            elif isinstance(price_proposal, list):
                for idx, item in enumerate(price_proposal):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            try:
                                self.add_row_to_table(key,
                                                      format_string("%.0f", float(value), grouping=True) + self.symbol)
                            except (ValueError, TypeError):
                                self.add_row_to_table(key, str(value))
                    else:
                        self.add_row_to_table(f"Ценовое предложение {idx + 1}", str(item))

            # Applicant
            applicant = self._parse_json_field(contract.Applicant)
            if isinstance(applicant, dict):
                for key, value in applicant.items():
                    self.add_row_to_table(key, str(value))
            elif isinstance(applicant, list):
                for idx, item in enumerate(applicant):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            self.add_row_to_table(key, str(value))
                    else:
                        self.add_row_to_table(f"Заявитель {idx + 1}", str(item))

            # Applicant_satatus
            applicant_status = self._parse_json_field(contract.Applicant_satatus)
            if isinstance(applicant_status, dict):
                for key, value in applicant_status.items():
                    self.add_row_to_table(key, str(value))
            elif isinstance(applicant_status, list):
                for idx, item in enumerate(applicant_status):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            self.add_row_to_table(key, str(value))
                    else:
                        self.add_row_to_table(f"Статус заявителя {idx + 1}", str(item))

            # ── Заключение контракта ──────────────────────────
            self.add_section_to_table("Заключение контракта")
            self.add_row_to_table("Победитель-исполнитель", contract.WinnerExecutor or "—")
            self.add_row_to_table("Заказчик по контракту", contract.ContractingAuthority or "—")
            self.add_row_to_table("Идентификатор договора", contract.ContractIdentifier or "—")
            self.add_row_to_table("Реестровый номер договора", contract.RegistryNumber or "—")
            self.add_row_to_table("№ договора", contract.ContractNumber or "—")
            self.add_row_to_table("Дата начала/подписания", str(contract.StartDate) if contract.StartDate else "—")
            self.add_row_to_table("Дата окончания/исполнения", str(contract.EndDate) if contract.EndDate else "—")
            self.add_row_to_table("Цена договора, руб.",
                                  format_string("%.0f", contract.ContractPrice,
                                                grouping=True) + self.symbol if contract.ContractPrice else "—")
            self.add_row_to_table("Размер авансирования, руб.",
                                  format_string("%.0f", contract.AdvancePayment,
                                                grouping=True) + self.symbol if contract.AdvancePayment else "—")
            self.add_row_to_table("Снижение НМЦК, руб.",
                                  format_string("%.0f", contract.ReductionNMC,
                                                grouping=True) + self.symbol if contract.ReductionNMC else "—")
            self.add_row_to_table("Снижение НМЦК, %",
                                  format_string("%.2f",
                                                contract.ReductionNMCPercent) + " %" if contract.ReductionNMCPercent else "—")
            self.add_row_to_table("Протоколы поставщика (выписка)", contract.SupplierProtocol or "—")
            self.add_row_to_table("Договор", contract.ContractFile or "—")

            # ── Общая информация (JSON) ───────────────────────
            common_info = self._parse_json_field(contract.common_info_json)
            if common_info:
                self.add_section_to_table("Общая информация")
                self._render_json_section(common_info)

            # ── Платежи и объекты закупки (JSON) ─────────────
            payment = self._parse_json_field(contract.payment_targets_json)
            if payment:
                self.add_section_to_table("Платежи и объекты закупки")
                self._render_json_section(payment)

            # ── Исполнение контракта (JSON) ───────────────────
            process = self._parse_json_field(contract.process_info_json)
            if process:
                self.add_section_to_table("Исполнение (расторжение) контракта")
                self._render_json_section(process)

            # ── Вложения (JSON) ───────────────────────────────
            documents = self._parse_json_field(contract.documents_json)
            if documents:
                self.add_section_to_table("Вложения")
                self._render_json_section(documents)

            # ── Журнал версий (JSON) ──────────────────────────
            journal = self._parse_json_field(contract.journal_versions_json)
            if journal:
                self.add_section_to_table("Журнал версий")
                self._render_json_section(journal)

            # ── Журнал событий (JSON) ─────────────────────────
            event_log = self._parse_json_field(contract.event_log_json)
            if event_log:
                self.add_section_to_table("Журнал событий")
                self._render_json_section(event_log)

        # ── Итоговое определение НМЦК ─────────────────────────
        self.finalDetermination = FinalDetermination.select().where(
            FinalDetermination.purchase == current_purchase
        )
        for det in self.finalDetermination:
            self.add_section_to_table("Итоговое определение НМЦК с использованием нескольких методов")
            self.add_row_to_table("Способ направления запросов", str(det.RequestMethod or "—"))
            self.add_row_to_table("Способ использования общедоступной информации",
                                  str(det.PublicInformationMethod or "—"))
            self.add_row_to_table("НМЦК, полученная различными способами", str(det.NMCObtainedMethods or "—"))
            self.add_row_to_table("НМЦК на основе затратного метода, руб.", str(det.CostMethodNMC or "—"))
            self.add_row_to_table("Цена сравнимой продукции", str(det.ComparablePrice or "—"))
            self.add_row_to_table("НМЦК с применением двух методов", str(det.NMCMethodsTwo or "—"))
            self.add_section_to_table("Итоговое определение ЦКЕИ")
            self.add_row_to_table("ЦКЕИ на основе метода сопоставимых рыночных цен",
                                  str(det.CEIComparablePrices or "—"))
            self.add_row_to_table("ЦКЕИ на основе затратного метода", str(det.CEICostMethod or "—"))
            self.add_row_to_table("ЦКЕИ с применением двух методов", str(det.CEIMethodsTwo or "—"))

    def _parse_json_field(self, raw, fallback=None):
        """
        Безопасный парсинг JSON-поля.
        Возвращает dict, list или fallback если поле пустое/None/невалидное.
        """
        if not raw or raw in ("[]", "{}", "Нет данных", "None"):
            return fallback if fallback is not None else {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return fallback if fallback is not None else {}
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
        if label_text == "файл НМЦК" or label_text == "файл протокола" or label_text == "Извещение о закупке" or label_text == "Файл расчета" or label_text == "Файл итогового определения НМЦК с использованием нескольких методов" or label_text == "Договор":
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


    def add_button_nmck_clicked(self):
        
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
     
            self.insert_cont = InsertWidgetPanel(purchase_id,self,self.role,self.user,self.changer)
            # self.insert_cont.setParent(self)
            self.insert_cont.show()

    def add_button_contract_clicked(self):
        
        if len(self.purchases_list) != 0:
            self.current_purchase = self.purchases_list[self.current_position]
            purchase_id = self.current_purchase.Id
     
            self.insert_cont = InsertPanelContract(purchase_id,self,self.role,self.user,self.changer)
            # self.insert_cont.setParent(self)
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
                wb.save(f'{selected_file}\формуляр контракта {self.current_purchase.RegistryNumber}.xlsx')
                QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
       

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     csv_loader_widget = PurchasesWidget()
#     csv_loader_widget.show()
#     sys.exit(app.exec())