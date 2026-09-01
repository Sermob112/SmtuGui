import sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import json as json_lib
from pathlib import Path
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

from smtuIdle.parserV3 import delete_records_by_id
from PySide6.QtWidgets import QSizePolicy
import os
import subprocess
from PySide6.QtCore import Signal
from smtuIdle.BD.models import Purchase, Contract, FinalDetermination, Customer, Vessel
from  locale import format_string,setlocale,LC_ALL
setlocale(LC_ALL, 'ru_RU.UTF-8')

db = SqliteDatabase('database.db')
cursor = db.cursor()


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent.parent


BASE_DIR = get_base_dir()
FILES_DIR = BASE_DIR / "db_files"
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
        font_title.setPointSize(10)
        font_title.setBold(True)
        self.label_form.setFont(font_title)

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
        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.addButtonCurrency,alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addStretch()
        button_layout2.addWidget(self.deleteButton)

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
                self.label_form.setText(f"Формуляр закупки № {current_purchase.RegistryNumber}")
            else:
                self.label_form.setText("Формуляр закупки")
            self.label_form.show()

            # =========================
            # 0. ОБЩИЕ СВЕДЕНИЯ
            # =========================
            self.add_section_to_table('Общие сведения', expanded=True)

            self.add_row_to_table("№ПП", str(current_purchase.Id))
            self.add_row_to_table(
                "Закон",
                current_purchase.PurchaseOrder if current_purchase.PurchaseOrder else "Нет данных"
            )
            self.add_row_to_table(
                "Реестровый номер",
                current_purchase.RegistryNumber if current_purchase.RegistryNumber else "Нет данных"
            )
            self.add_row_to_table(
                "Метод закупки",
                current_purchase.ProcurementMethod if current_purchase.ProcurementMethod else "Нет данных"
            )
            self.add_row_to_table(
                "Наименование закупки",
                current_purchase.PurchaseName if current_purchase.PurchaseName else "Нет данных"
            )
            self.add_row_to_table(
                "Предмет аукциона",
                current_purchase.AuctionSubject if current_purchase.AuctionSubject else "Нет данных"
            )
            self.add_row_to_table(
                "Код идентификации закупки",
                current_purchase.PurchaseIdentificationCode
                if current_purchase.PurchaseIdentificationCode else "Нет данных"
            )
            self.add_row_to_table(
                "Номер лота",
                str(current_purchase.LotNumber) if current_purchase.LotNumber is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Наименование лота",
                current_purchase.LotName if current_purchase.LotName else "Нет данных"
            )
            self.add_row_to_table(
                "Начальная максимальная цена контракта",
                format_string(
                    "%.0f",
                    current_purchase.InitialMaxContractPrice,
                    grouping=True
                ) + self.symbol
                if current_purchase.InitialMaxContractPrice is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Валюта",
                current_purchase.Currency if current_purchase.Currency else "Нет данных"
            )
            self.add_row_to_table(
                "Начальная максимальная цена контракта в валюте",
                str(current_purchase.InitialMaxContractPriceInCurrency)
                if current_purchase.InitialMaxContractPriceInCurrency is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Количество единиц",
                str(current_purchase.quantity_units)
                if current_purchase.quantity_units is not None else "Нет данных"
            )
            self.add_row_to_table(
                "НМЦК за единицу",
                format_string(
                    "%.0f",
                    current_purchase.nmck_per_unit,
                    grouping=True
                ) + self.symbol
                if current_purchase.nmck_per_unit is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Валюта контракта",
                current_purchase.ContractCurrency
                if current_purchase.ContractCurrency else "Нет данных"
            )
            self.add_row_to_table(
                "Классификация ОКДП",
                current_purchase.OKDPClassification
                if current_purchase.OKDPClassification else "Нет данных"
            )
            self.add_row_to_table(
                "Классификация ОКПД",
                current_purchase.OKPDClassification
                if current_purchase.OKPDClassification else "Нет данных"
            )
            self.add_row_to_table(
                "Классификация ОКПД2",
                current_purchase.OKPD2Classification
                if current_purchase.OKPD2Classification else "Нет данных"
            )
            self.add_row_to_table(
                "Код позиции",
                current_purchase.PositionCode
                if current_purchase.PositionCode else "Нет данных"
            )
            self.add_row_to_table(
                "Наименование заказчика",
                current_purchase.CustomerName
                if current_purchase.CustomerName else "Нет данных"
            )
            self.add_row_to_table(
                "Организация закупки",
                current_purchase.ProcurementOrganization
                if current_purchase.ProcurementOrganization else "Нет данных"
            )
            self.add_row_to_table(
                "Дата размещения",
                str(current_purchase.PlacementDate)
                if current_purchase.PlacementDate else "Нет данных"
            )
            self.add_row_to_table(
                "Дата обновления",
                str(current_purchase.UpdateDate)
                if current_purchase.UpdateDate else "Нет данных"
            )
            self.add_row_to_table(
                "Этап закупки",
                current_purchase.ProcurementStage
                if current_purchase.ProcurementStage else "Нет данных"
            )
            self.add_row_to_table(
                "Особенности закупки",
                current_purchase.ProcurementFeatures
                if current_purchase.ProcurementFeatures else "Нет данных"
            )
            self.add_row_to_table(
                "Дата начала заявки",
                str(current_purchase.ApplicationStartDate)
                if current_purchase.ApplicationStartDate else "Нет данных"
            )
            self.add_row_to_table(
                "Дата окончания заявки",
                str(current_purchase.ApplicationEndDate)
                if current_purchase.ApplicationEndDate else "Нет данных"
            )
            self.add_row_to_table(
                "Дата аукциона",
                str(current_purchase.AuctionDate)
                if current_purchase.AuctionDate else "Нет данных"
            )
            self.add_row_to_table(
                "Извещение о закупке",
                str(current_purchase.notification_link)
                if current_purchase.notification_link else "Нет данных"
            )
            self.add_row_to_table(
                "Файл НМЦК",
                str(current_purchase.nmck_file)
                if current_purchase.nmck_file else "Нет данных"
            )
            self.add_row_to_table(
                "Файл протокола",
                str(current_purchase.protocol_file)
                if current_purchase.protocol_file else "Нет данных"
            )

            # =========================
            # 1. ОПРЕДЕЛЕНИЕ НМЦК И ЦКЕИ (заголовок группы)
            # =========================
            self.add_section_to_table("Определение НМЦК и ЦКЕИ", expanded=True)

            # =========================
            # 1.1 Метод сопоставимых рыночных цен
            # =========================
            self.add_section_to_table(
                "1.Определение НМЦК методом сопоставимых рыночных цен",
                expanded=False
            )

            # ТКП
            if current_purchase.TKPData and str(current_purchase.TKPData).strip() not in (
                    "", "None", "-", "[]", "{}"
            ):
                try:
                    tkp_parsed = json.loads(current_purchase.TKPData)
                    self.add_json_to_tree(self.current_parent, tkp_parsed)
                except json.JSONDecodeError:
                    self.add_row_to_table("ТКП", str(current_purchase.TKPData))
            else:
                self.add_row_to_table("ТКП", "Нет данных")

            self.add_row_to_table(
                "Количество запросов",
                str(current_purchase.QueryCount)
                if current_purchase.QueryCount is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Количество ответов",
                str(current_purchase.ResponseCount)
                if current_purchase.ResponseCount is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Среднее значение цены",
                format_string(
                    "%.0f",
                    current_purchase.AveragePrice,
                    grouping=True
                ) + self.symbol
                if current_purchase.AveragePrice is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Минимальная цена",
                format_string(
                    "%.0f",
                    current_purchase.MinPrice,
                    grouping=True
                ) + self.symbol
                if current_purchase.MinPrice is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Максимальная цена",
                format_string(
                    "%.0f",
                    current_purchase.MaxPrice,
                    grouping=True
                ) + self.symbol
                if current_purchase.MaxPrice is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Среднее квадратичное отклонение",
                format_string(
                    "%.0f",
                    current_purchase.StandardDeviation,
                    grouping=True
                ) + self.symbol
                if current_purchase.StandardDeviation is not None else "Нет данных"
            )

            # Коэффициент вариации (%)
            coef_var = (
                current_purchase.CoefficientOfVariation * 100
                if current_purchase.CoefficientOfVariation is not None
                else None
            )
            self.add_row_to_table(
                "Коэффициент вариации %",
                f"{coef_var:.2f} %"
                if coef_var is not None else "Нет данных"
            )

            self.add_row_to_table(
                "НМЦК рыночная",
                format_string(
                    "%.0f",
                    current_purchase.NMCKMarket,
                    grouping=True
                ) + self.symbol
                if current_purchase.NMCKMarket is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Лимит финансирования",
                format_string(
                    "%.0f",
                    current_purchase.FinancingLimit,
                    grouping=True
                ) + self.symbol
                if current_purchase.FinancingLimit is not None else "Нет данных"
            )

            # --- NMCK_1, NMCK_2, NMCK_3 ---
            def add_nmck_field(field_value, label):
                if field_value and str(field_value).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed = json.loads(field_value)

                        sub_header = QTreeWidgetItem(self.current_parent)
                        sub_header.setText(0, label)
                        sub_header.setFirstColumnSpanned(True)

                        font = QFont()
                        font.setBold(True)
                        sub_header.setFont(0, font)

                        self.add_json_to_tree(sub_header, parsed)
                    except json.JSONDecodeError:
                        self.add_row_to_table(label, str(field_value))
                else:
                    self.add_row_to_table(label, "Нет данных")

            add_nmck_field(
                current_purchase.NMCK_1,
                "Цена судна (приведённая к уровню цен года поставки)"
            )
            add_nmck_field(
                current_purchase.NMCK_2,
                "Цена судна (приведённая к уровню цен первого года строительства)"
            )
            add_nmck_field(
                current_purchase.NMCK_3,
                "Цена судна (приведённая к уровню цен текущих лет строительства)"
            )

            self.add_row_to_table(
                "Количество контрактов",
                str(current_purchase.ContractCount)
                if current_purchase.ContractCount is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Определение НМЦК",
                str(current_purchase.NMC_determ)
                if current_purchase.NMC_determ is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Определение коэффициента НМЦК",
                str(current_purchase.NMC_coef_determ)
                if current_purchase.NMC_coef_determ is not None else "Нет данных"
            )

            # =========================
            # 1.2 Метод с общедоступной информацией
            # =========================
            self.add_section_to_table(
                "2.Определение НМЦК методом сопоставимых рыночных цен при использовании общедоступной информации",
                expanded=False
            )

            def parse_nmck(field_data, label):
                if field_data and str(field_data).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed = json.loads(field_data)

                        sub_header = QTreeWidgetItem(self.current_parent)
                        sub_header.setText(0, label)
                        sub_header.setFirstColumnSpanned(True)

                        font = QFont()
                        font.setBold(True)
                        sub_header.setFont(0, font)

                        self.add_json_to_tree(sub_header, parsed)
                    except json.JSONDecodeError:
                        self.add_row_to_table(label, str(field_data))
                else:
                    self.add_row_to_table(label, "Нет данных")

            parse_nmck(
                current_purchase.NMCK_1,
                "Цена судна (год поставки)"
            )
            parse_nmck(
                current_purchase.NMCK_2,
                "Цена судна (первый год строительства)"
            )
            parse_nmck(
                current_purchase.NMCK_3,
                "Цена судна (текущие годы)"
            )

            # =========================
            # 1.3 Затратный метод
            # =========================
            self.add_section_to_table(
                "3.Определение НМЦК затратным методом",
                expanded=False
            )

            self.add_row_to_table(
                "Наименование организации",
                str(current_purchase.organization_name)
                if current_purchase.organization_name else "Нет данных"
            )
            self.add_row_to_table(
                "Дата расчета",
                str(current_purchase.organization_name_date)
                if current_purchase.organization_name_date else "Нет данных"
            )

            org_price_val = None
            if current_purchase.organization_price:
                try:
                    org_price_val = float(current_purchase.organization_price)
                except (ValueError, TypeError):
                    pass

            self.add_row_to_table(
                "Цена",
                format_string(
                    "%.0f",
                    org_price_val,
                    grouping=True
                ) + self.symbol
                if org_price_val is not None else "Нет данных"
            )
            self.add_row_to_table(
                "Файл расчета",
                str(current_purchase.organization_name_file)
                if current_purchase.organization_name_file else "Нет данных"
            )

            # =========================
            # 1.4 Итоговое определение (несколько методов)
            # =========================
            self.add_section_to_table(
                "4.Итоговое определение НМЦК с использованием нескольких методов",
                expanded=False
            )

            self.add_row_to_table(
                "Способ направления запросов",
                str(current_purchase.method_direction_requests)
                if current_purchase.method_direction_requests else "Нет данных"
            )
            self.add_row_to_table(
                "Способ использования общедоступной информации",
                str(current_purchase.method_usage_information)
                if current_purchase.method_usage_information else "Нет данных"
            )
            self.add_row_to_table(
                "НМЦК различными способами",
                str(current_purchase.nmc_various_methods)
                if current_purchase.nmc_various_methods else "Нет данных"
            )
            self.add_row_to_table(
                "НМЦК затратным методом",
                str(current_purchase.nmc_cost_method)
                if current_purchase.nmc_cost_method else "Нет данных"
            )
            self.add_row_to_table(
                "Цена сравнимой продукции",
                str(current_purchase.comparable_product_price)
                if current_purchase.comparable_product_price else "Нет данных"
            )
            self.add_row_to_table(
                "НМЦК двумя методами",
                str(current_purchase.nmc_two_methods)
                if current_purchase.nmc_two_methods else "Нет данных"
            )
            self.add_file_row_to_table(
                "Файл итогового определения",
                current_purchase.file_4 if current_purchase.file_4 else None
            )

            # =========================
            # FINAL DETERMINATION
            # =========================
            self.finalDetermination = FinalDetermination.select().where(
                FinalDetermination.purchase == current_purchase
            )

            if self.finalDetermination.exists():
                self.add_section_to_table(
                    "Итоговое определение НМЦК с использованием нескольких методов (FinalDetermination)",
                    expanded=True
                )

                for det in self.finalDetermination:
                    self.add_row_to_table(
                        "Способ направления запросов о предоставлении ценовой информации",
                        str(det.RequestMethod) if det.RequestMethod else "Нет данных"
                    )
                    self.add_row_to_table(
                        "Способ использования общедоступной информации",
                        str(det.PublicInformationMethod)
                        if det.PublicInformationMethod else "Нет данных"
                    )
                    self.add_row_to_table(
                        "НМЦК, полученная различными способами",
                        str(det.NMCObtainedMethods)
                        if det.NMCObtainedMethods else "Нет данных"
                    )
                    self.add_row_to_table(
                        "НМЦК на основе затратного метода",
                        str(det.CostMethodNMC)
                        if det.CostMethodNMC else "Нет данных"
                    )
                    self.add_row_to_table(
                        "Цена сравнимой продукции",
                        str(det.ComparablePrice)
                        if det.ComparablePrice else "Нет данных"
                    )
                    self.add_row_to_table(
                        "НМЦК, полученная с применением двух методов",
                        str(det.NMCMethodsTwo)
                        if det.NMCMethodsTwo else "Нет данных"
                    )
                    self.add_row_to_table(
                        "ЦКЕИ на основе метода",
                        str(det.CEICostMethod)
                        if det.CEICostMethod else "Нет данных"
                    )
                    self.add_row_to_table(
                        "ЦКЕИ, полученная с применением двух методов",
                        str(det.CEIMethodsTwo)
                        if det.CEIMethodsTwo else "Нет данных"
                    )

            # =========================
            # JSON ПОЛЯ ЗАКУПКИ
            # =========================
            json_fields = [
                ("Общая информация по закупке", current_purchase.common_info_json),
                ("Документы закупки", current_purchase.documents_json),
                ("Журнал событий закупки", current_purchase.event_log_json),
                ("Результаты поставщика закупки", current_purchase.supplier_result_json),
                ("Список лотов закупки", current_purchase.lots_json),
                ("Протоколы закупки", current_purchase.protocols_json),
                ("Сведения о договорах закупки", current_purchase.contracts_info_json),
                ("Изменения закупки", current_purchase.changes_json),
            ]

            for section_name, json_string in json_fields:
                self.add_section_to_table(section_name, expanded=False)

                if json_string and str(json_string).strip() not in (
                        "", "None", "-", "[]", "{}"
                ):
                    try:
                        parsed_json = json.loads(json_string)
                        self.add_json_to_tree(self.current_parent, parsed_json)
                    except json.JSONDecodeError:
                        self.add_row_to_table(
                            "Содержимое JSON",
                            str(json_string)
                        )
                else:
                    self.add_row_to_table(
                        "Содержимое JSON",
                        "Нет данных"
                    )

            # =========================
            # СВЯЗАННЫЕ ДАННЫЕ
            # =========================
            self.add_section_to_table('Связанные документы', expanded=True)
            links_parent = self.current_parent

            # 1. ЗАКАЗЧИК
            if current_purchase.CustomerName:
                customer = Customer.select().where(
                    Customer.name == current_purchase.CustomerName
                ).first()

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
                    link_item.setData(
                        1, Qt.UserRole,
                        f"GOTO_CUSTOMER:{customer.id}"
                    )
                    link_item.setForeground(1, Qt.blue)

                    font_link = QFont()
                    font_link.setUnderline(True)
                    link_item.setFont(1, font_link)

                    QTreeWidgetItem(customer_node, ['ИНН', str(customer.inn)])
                    QTreeWidgetItem(customer_node, ['КПП', str(customer.kpp)])

            # 2. КОНТРАКТЫ И СУДА
            contracts = None

            fk_contracts = Contract.select().where(
                Contract.purchase == current_purchase.Id
            )

            if fk_contracts.exists():
                contracts = fk_contracts
            elif current_purchase.RegistryNumber:
                rn_contracts = Contract.select().where(
                    Contract.RegistryNumber == current_purchase.RegistryNumber
                )
                if rn_contracts.exists():
                    contracts = rn_contracts

            if contracts is not None:
                for contract in contracts:
                    c_title = (
                        f'Контракт № {contract.ContractNumber}'
                        if contract.ContractNumber
                        else f'Контракт ID {contract.Id}'
                    )

                    contract_node = QTreeWidgetItem(links_parent)
                    contract_node.setText(0, c_title)
                    contract_node.setFirstColumnSpanned(True)

                    font_c = QFont()
                    font_c.setBold(True)
                    contract_node.setFont(0, font_c)
                    contract_node.setBackground(0, QColor(240, 240, 240))

                    link_item = QTreeWidgetItem(contract_node)
                    link_item.setText(0, 'Перейти в карточку контракта')
                    link_item.setText(1, c_title)
                    link_item.setData(
                        1, Qt.UserRole,
                        f"GOTO_CONTRACT:{contract.Id}"
                    )
                    link_item.setForeground(1, Qt.blue)
                    link_item.setFont(1, font_link)

                    QTreeWidgetItem(contract_node, ['Победитель', str(contract.WinnerExecutor)])
                    QTreeWidgetItem(contract_node, ['Заказчик', str(contract.ContractingAuthority)])

                    if contract.ContractPrice is not None:
                        QTreeWidgetItem(
                            contract_node,
                            [
                                'Цена',
                                f"{format_string('%.2f', float(contract.ContractPrice), grouping=True)} {self.symbol}"
                            ]
                        )

                    for label, field_data in [
                        ("Ценовое предложение", contract.PriceProposal),
                        ("Заявитель", contract.Applicant),
                        ("Статус заявителя", contract.Applicant_satatus)
                    ]:
                        if field_data and str(field_data).strip() not in (
                                "", "None", "-", "[]", "{}"
                        ):
                            try:
                                parsed_data = json.loads(field_data)
                                json_node = QTreeWidgetItem(contract_node)
                                json_node.setText(0, label)
                                self.add_json_to_tree(json_node, parsed_data)
                            except json.JSONDecodeError:
                                QTreeWidgetItem(contract_node, [label, str(field_data)])

                    try:
                        vessels = Vessel.select().where(Vessel.contract == contract)
                        for vessel in vessels:
                            v_title = (
                                f'Судно (Проект {vessel.ship_project})'
                                if vessel.ship_project
                                else f'Судно ID {vessel.id}'
                            )

                            vessel_node = QTreeWidgetItem(contract_node)
                            vessel_node.setText(0, v_title)
                            vessel_node.setFirstColumnSpanned(True)
                            vessel_node.setFont(0, font_c)
                            vessel_node.setBackground(0, QColor(250, 250, 250))

                            v_link = QTreeWidgetItem(vessel_node)
                            v_link.setText(0, 'Перейти в карточку судна')
                            v_link.setText(1, v_title)
                            v_link.setData(
                                1, Qt.UserRole,
                                f"GOTO_VESSEL:{vessel.id}"
                            )
                            v_link.setForeground(1, Qt.blue)
                            v_link.setFont(1, font_link)

                            QTreeWidgetItem(vessel_node, ['ИМО', str(vessel.imo_number)])
                            QTreeWidgetItem(vessel_node, ['Тип', str(vessel.ship_type)])
                    except Exception:
                        pass
        else:
            self.label.setText("Нет записи")
            self.label_form.setText("Карточка закупки")
            self.label_form.show()
    def add_file_row_to_table(self, label, file_path):
        item = QTreeWidgetItem(self.current_parent)
        item.setText(0, label)

        if file_path:
            item.setText(1, file_path)
            item.setData(1, Qt.UserRole, file_path)
            item.setForeground(1, QColor("blue"))
            font = item.font(1)
            font.setUnderline(True)
            item.setFont(1, font)
        else:
            item.setText(1, "Нет данных")
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
        """
        Упрощённое отображение JSON в дереве.

        Объект kind == "kv":

            {
                "kind": "kv",
                "text": "23.03.2026",
                "hrefs": [],
                "title": "Дата заключения контракта"
            }

        отображается одной строкой:

            Дата заключения контракта | 23.03.2026

        Поля kind, hrefs и items в дерево не выводятся.
        """

        key_translations = {
            "общие_данные": "Общие данные",
            "общая_информация": "Общая информация",
            "информация_о_заказчике": "Информация о заказчике",
            "информация_о_поставщиках": "Информация о поставщиках",
            "информация_об_изменении_контракта": (
                "Информация об изменении контракта"
            ),
            "table": "Таблица",
            "rows": "Строки таблицы",
            "headers": "Заголовки колонок",
            "rows_by_index": "Строки таблицы",
            "totals_row": "Итоговая строка",
            "totals_summary": "Итоговая сводка",
            "nested": "Вложенные данные",
            "section_title": "Заголовок раздела",
            "header": "Название группы",
            "name": "Название",
            "price": "Цена",
            "sum": "Сумма",
            "quantity": "Количество",
            "quantitu": "Количество",
            "ktru": "КТРУ",
            "raw_sum_text": "Текстовая сумма",
            "url": "Ссылка",
            "sign_url": "Ссылка на подпись",
            "sign_link": "Ссылка на подпись",
            "text": "Текст",
            "table standalone": "Отдельная таблица",
            "table_standalone": "Отдельная таблица",
            "Parsed_table": "Отдельная таблица",

        }

        if json_data in (None, "", [], {}):
            return

        # ---------------------------------------------------------
        # Обработка одной записи вида kind == "kv"
        # ---------------------------------------------------------
        if isinstance(json_data, dict) and json_data.get("kind") == "kv":
            title = json_data.get("title") or "Параметр"
            text = json_data.get("text")

            item = QTreeWidgetItem(parent_item)
            item.setText(0, str(title))
            item.setText(
                1,
                str(text) if text not in (None, "") else "Нет данных"
            )

            font = QFont()
            font.setPointSize(10)
            item.setFont(0, font)
            item.setFont(1, font)

            # Сохраняем первую ссылку из hrefs, но сам hrefs не отображаем
            hrefs = json_data.get("hrefs") or []

            if hrefs:
                url = hrefs[0]

                item.setForeground(1, Qt.blue)

                link_font = QFont()
                link_font.setPointSize(10)
                link_font.setUnderline(True)
                item.setFont(1, link_font)

                item.setData(1, Qt.UserRole, str(url))

            return

        # ---------------------------------------------------------
        # Обработка словаря
        # ---------------------------------------------------------
        if isinstance(json_data, dict):
            for key, value in json_data.items():

                # Служебные поля не выводим
                if key in ("kind", "hrefs", "all_hrefs"):
                    continue

                # Узел items пропускаем, а его содержимое выводим
                # непосредственно в родительский узел
                if key == "items":
                    if isinstance(value, list):
                        for item_value in value:
                            self.add_json_to_tree(
                                parent_item,
                                item_value,
                                "items"
                            )
                    elif isinstance(value, dict):
                        self.add_json_to_tree(
                            parent_item,
                            value,
                            "items"
                        )
                    continue

                # Заголовок группы не дублируем внутри JSON
                if key == "header" and parent_key:
                    continue

                # Пустые значения не создают лишние строки
                if value in (None, "", [], {}):
                    continue

                display_key = key_translations.get(
                    key,
                    str(key).replace("_", " ").capitalize()
                )

                if isinstance(value, (dict, list)):
                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, display_key)

                    font = QFont()
                    font.setBold(True)
                    child.setFont(0, font)

                    self.add_json_to_tree(
                        child,
                        value,
                        key
                    )
                else:
                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, display_key)
                    child.setText(1, str(value))

            return

        # ---------------------------------------------------------
        # Обработка списков
        # ---------------------------------------------------------
        if isinstance(json_data, list):
            for index, value in enumerate(json_data):

                # Элементы kind == "kv" сразу становятся строками
                if (
                        isinstance(value, dict)
                        and value.get("kind") == "kv"
                ):
                    self.add_json_to_tree(
                        parent_item,
                        value,
                        parent_key
                    )
                    continue

                # Вложенные словари и списки
                if isinstance(value, (dict, list)):

                    if parent_key in ("rows", "rows_by_index"):
                        item_name = f"Строка {index + 1}"
                    elif parent_key == "headers":
                        item_name = f"Колонка {index + 1}"
                    else:
                        item_name = f"Запись {index + 1}"

                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, item_name)

                    font = QFont()
                    font.setBold(True)
                    child.setFont(0, font)

                    self.add_json_to_tree(
                        child,
                        value,
                        parent_key
                    )

                # Простые значения списка
                else:
                    child = QTreeWidgetItem(parent_item)

                    if parent_key == "headers":
                        child.setText(
                            0,
                            f"Колонка {index + 1}"
                        )
                    else:
                        child.setText(
                            0,
                            f"Элемент {index + 1}"
                        )

                    child.setText(
                        1,
                        str(value) if value is not None else "Нет данных"
                    )

            return

        # ---------------------------------------------------------
        # Простое скалярное значение
        # ---------------------------------------------------------
        parent_item.setText(1, str(json_data))

    def add_section_to_table(self, section_text, expanded=False):
        # Создаем родительскую ветку (Группу)
        self.current_parent = QTreeWidgetItem(self.tree)
        self.current_parent.setText(0, section_text)
        self.current_parent.setFirstColumnSpanned(True)  # Растягиваем на всю ширину

        self.current_parent.setExpanded(expanded)

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.current_parent.setFont(0, font)

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

            url_or_cmd = item.data(1, Qt.UserRole)

            # ── ВНУТРЕННИЕ ПЕРЕХОДЫ (GOTO_*) ─────────────────────────────────
            if url_or_cmd and isinstance(url_or_cmd, str) and url_or_cmd.startswith("GOTO_"):
                command, record_id = url_or_cmd.split(":")
                record_id = int(record_id)

                if hasattr(self.main_win, 'history'):
                    self.main_win.history.append(self.main_win.stackedWidget.currentIndex())

                if command == "GOTO_CUSTOMER":
                    self.main_win.customerFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(11)
                elif command == "GOTO_CONTRACT":
                    self.main_win.contractFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(8)
                elif command == "GOTO_VESSEL":
                    self.main_win.vesselFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(13)
                return

            # ── ОТКРЫТИЕ ФАЙЛА ПО ОТНОСИТЕЛЬНОМУ ПУТИ (из db_files) ─────────
            if url_or_cmd and isinstance(url_or_cmd, str) and not url_or_cmd.startswith(
                    ("http", "zakupki", "download")):

                # url_or_cmd может быть вида "db_files\№ 0129....docx"
                # Нормализуем слеши
                rel_path = url_or_cmd.replace("/", "\\")

                # Если путь уже начинается с db_files, убираем дублирование
                if rel_path.lower().startswith("db_files"):
                    rel_path = rel_path[len("db_files"):].lstrip("\\/")

                full_path = FILES_DIR / rel_path

                if not (full_path.exists() and full_path.is_file()):
                    QMessageBox.warning(self, "Файл не найден", f"Не найден файл:\n{full_path}")
                    return

                filepath = str(full_path)

            # ── ОТКРЫТИЕ ФАЙЛА / ССЫЛКИ ──────────────────────────────────────
            if filepath and os.path.isfile(filepath):
                if filepath.lower().endswith(('.docx', '.doc')):
                    subprocess.Popen(['start', 'winword', filepath], shell=True)
                elif filepath.lower().endswith('.pdf'):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
                elif filepath.lower().endswith(('.xlsx', '.xls', '.csv')):
                    subprocess.Popen(['start', 'excel', filepath], shell=True)
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
            else:
                if url_or_cmd and ('http' in url_or_cmd or 'zakupki' in url_or_cmd):
                    QDesktopServices.openUrl(QUrl(url_or_cmd))
                elif filepath and ('http' in filepath or 'zakupki' in filepath):
                    QDesktopServices.openUrl(QUrl(filepath))
                elif filepath and 'download' in filepath:
                    QDesktopServices.openUrl(QUrl(filepath))

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
        if not hasattr(self, 'current_purchase') or self.current_purchase is None:
            QMessageBox.warning(self, "Ошибка", "Нет текущей закупки для экспорта")
            return

        p = self.current_purchase

        wb = Workbook()
        ws = wb.active
        ws.title = "Общие сведения"

        ws.append(["Параметр", "Значение"])

        def add_row(label, value):
            if value is None or str(value).strip() in ("", "None", "-"):
                ws.append([label, "Нет данных"])
            else:
                ws.append([label, value])

        fields = [
            ("ID в БД", p.Id),
            ("Закон", p.PurchaseOrder),
            ("Реестровый номер", p.RegistryNumber),
            ("Метод закупки", p.ProcurementMethod),
            ("Наименование закупки", p.PurchaseName),
            ("Предмет аукциона", p.AuctionSubject),
            ("Код закупки", p.PurchaseIdentificationCode),
            ("Номер лота", p.LotNumber),
            ("Наименование лота", p.LotName),
            ("НМЦК", p.InitialMaxContractPrice),
            ("Валюта", p.Currency),
            ("НМЦК в валюте", p.InitialMaxContractPriceInCurrency),
            ("Кол-во единиц", p.quantity_units),
            ("НМЦК на единицу", p.nmck_per_unit ),
            ("Валюта контракта", p.ContractCurrency),
            ("ОКДП", p.OKDPClassification),
            ("ОКПД", p.OKPDClassification),
            ("ОКПД2", p.OKPD2Classification),
            ("Код позиции", p.PositionCode),
            ("Наименование заказчика", p.CustomerName),
            ("Организация закупки", p.ProcurementOrganization),
            ("Дата размещения", p.PlacementDate),
            ("Дата обновления", p.UpdateDate),
            ("Этап закупки", p.ProcurementStage),
            ("Особенности закупки", p.ProcurementFeatures),
            ("Дата начала подачи заявок", p.ApplicationStartDate),
            ("Дата окончания подачи заявок", p.ApplicationEndDate),
            ("Дата аукциона", p.AuctionDate),
            ("Ссылка на извещение", p.notification_link),
            ("Файл НМЦК", p.nmck_file),
            ("Протокол", p.protocol_file),
            ("Число заявок", p.QueryCount),
            ("Число ответов", p.ResponseCount),
            ("Средняя цена", p.AveragePrice),
            ("Минимальная цена", p.MinPrice),
            ("Максимальная цена", p.MaxPrice),
            ("Стандартное отклонение", p.StandardDeviation),
            ("Коэффициент вариации", p.CoefficientOfVariation),
            ("НМЦК market", p.NMCKMarket),
            ("Лимит финансирования", p.FinancingLimit),
        ]

        for label, value in fields:
            add_row(label, value)

        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 90

        # --- 2. JSON-поля ---
        json_fields = [
            ("TKPData", "ТКП данные"),
            ("common_info_json", "Общая информация"),
            ("documents_json", "Документы"),
            ("event_log_json", "Журнал событий"),
            ("supplier_result_json", "Результат поставщика"),
            ("lots_json", "Лоты"),
            ("protocols_json", "Протоколы"),
            ("contracts_info_json", "Информация по контрактам"),
            ("changes_json", "Изменения"),
        ]

        existing_json = [x for x in json_fields if hasattr(p, x[0])]
        if existing_json:
            ws_json = wb.create_sheet("JSON данные")
            ws_json.append(["Поле", "Значение (JSON)"])

            for fname, label in existing_json:
                raw = getattr(p, fname, None)
                if raw and str(raw).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed = json_lib.loads(raw)
                        value_str = json_lib.dumps(parsed, ensure_ascii=False, indent=2)
                    except Exception:
                        value_str = str(raw)
                else:
                    value_str = "Нет данных"
                ws_json.append([label, value_str])

            ws_json.column_dimensions["A"].width = 35
            ws_json.column_dimensions["B"].width = 100

        # --- 3. Контракт ---
        contract = (
            Contract.select()
            .where(Contract.purchase == p.Id)
            .first()
        )
        if contract is None and p.RegistryNumber:
            contract = (
                Contract.select()
                .where(Contract.RegistryNumber == p.RegistryNumber)
                .first()
            )

        if contract:
            ws_cont = wb.create_sheet("Контракт")
            ws_cont.append(["Параметр", "Значение"])

            contract_fields = [
                ("ID в БД", contract.Id),
                ("№ договора", contract.ContractNumber),
                ("Реестровый номер", contract.RegistryNumber),
                ("Идентификатор договора", contract.ContractIdentifier),
                ("Заказчик по контракту", contract.ContractingAuthority),
                ("Победитель-исполнитель", contract.WinnerExecutor),
                ("Дата начала", contract.StartDate),
                ("Дата окончания", contract.EndDate),
                ("Цена договора", contract.ContractPrice),
                ("Авансирование", contract.AdvancePayment),
                ("Снижение НМЦК", contract.ReductionNMC),
                ("Снижение НМЦК %", contract.ReductionNMCPercent),
                ("Всего заявок", contract.TotalApplications),
                ("Допущено", contract.AdmittedApplications),
                ("Отклонено", contract.RejectedApplications),
                ("Ценовое предложение", contract.PriceProposal),
                ("Заявитель", contract.Applicant),
                ("Статус заявителя", contract.Applicant_satatus),
                ("Протокол поставщика", contract.SupplierProtocol),
                ("Файл договора", contract.ContractFile),
            ]

            for label, value in contract_fields:
                if value is None or str(value).strip() in ("", "None", "-"):
                    ws_cont.append([label, "Нет данных"])
                else:
                    ws_cont.append([label, value])

            ws_cont.column_dimensions["A"].width = 40
            ws_cont.column_dimensions["B"].width = 90

        # --- 4. Сохранение ---
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            if selected_file:
                if p.RegistryNumber:
                    safe_name = str(p.RegistryNumber)
                else:
                    safe_name = str(p.Id)

                safe_name = "".join(ch for ch in safe_name if ch.isalnum() or ch in "._- ")
                save_path = f"{selected_file}/Формуляр закупки № {safe_name}.xlsx"

                wb.save(save_path)
                QMessageBox.information(self, "Успех", f"Файл успешно сохранен: {save_path}")
