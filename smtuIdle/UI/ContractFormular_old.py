import json
import os
import subprocess
from locale import format_string, setlocale, LC_ALL
from openpyxl import Workbook

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices
from openpyxl.utils import get_column_letter
import json as json_lib

# ВАЖНО: Убедитесь, что вы импортировали модель Contract из вашего файла моделей
from smtuIdle.BD.models import Contract, SupplierContract
from smtuIdle.BD.models import Contract, Supplier, Vessel, ContractVersion
# Установка локали для форматирования чисел (если нужна)
try:
    setlocale(LC_ALL, 'ru_RU.UTF-8')
except:
    pass


class ContractWidget(QWidget):
    closingSignal = Signal()

    def __init__(self, mainwindow, role, user, changer):
        super().__init__()
        self.main_win = mainwindow
        self.role = role
        self.user = user
        self.changer = changer
        self.symbol = "₽"

        self.current_position = 0
        self.contracts_list = []

        # --- Создание дерева ---
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setWordWrap(True)
        self.tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tree.setColumnWidth(0, 400)

        # Настройка сетки и стилей

        self.tree.setStyleSheet("""
          
            QTreeWidget::item {
                border-bottom: 1px solid #e0e0e0;
                border-right: 1px solid #e0e0e0;
                padding: 4px;
            }
        """)
        self.tree.setStyle(QStyleFactory.create('windows'))
        self.tree.itemClicked.connect(self.open_file)

        # --- Заголовок ---
        self.label_form = QLabel("")
        font_title = QFont()
        font_title.setPointSize(10)
        font_title.setBold(True)
        self.label_form.setFont(font_title)


        # --- Кнопки управления ---
        self.BackButton = QPushButton("Назад", self)
        self.BackButton.clicked.connect(self.go_back)
        self.BackButton.hide()

        self.exportButton = QPushButton("Экспорт в Excel", self)
        self.exportButton.setMaximumWidth(300)
        self.exportButton.clicked.connect(self.export_to_excel)

        # --- Сборка макетов ---
        vertical_labels = QVBoxLayout()
        vertical_labels.addWidget(self.label_form)

        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.exportButton, alignment=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addLayout(vertical_labels)
        layout.addWidget(self.tree)
        layout.addLayout(button_layout2)

        self.reload_data()

    def go_back(self):
        if hasattr(self.main_win, 'navigate_back'):
            self.main_win.navigate_back()
        else:
            self.main_win.stackedWidget.setCurrentIndex(0)

    def reload_data(self):
        self.contracts = Contract.select()
        self.contracts_list = list(self.contracts)
        self.show_current_contract()

    def reload_data_id(self, contract_id):
        self.contracts = Contract.select().where(Contract.Id == contract_id)
        self.contracts_list = list(self.contracts)
        self.show_current_contract()

    def add_section_to_table(self, section_text, expanded=False):
        self.current_parent = QTreeWidgetItem(self.tree)
        self.current_parent.setText(0, section_text)
        self.current_parent.setFirstColumnSpanned(True)
        self.current_parent.setExpanded(expanded)

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.current_parent.setFont(0, font)
        self.current_parent.setBackground(0, QColor(230, 230, 230))

    def add_row_to_table(self, label_text, value_text):
        if value_text is None or str(value_text).strip() in ("", "None", "-"):
            value_text = "Нет данных"
        else:
            value_text = str(value_text)

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

        # Подсветка файлов/ссылок
        link_fields = ['Протоколы (выписка)', 'Договор', 'Реестровый номер договора']
        if label_text in link_fields and value_text != "Нет данных":
            item.setForeground(1, Qt.blue)
            font_link = QFont()
            font_link.setPointSize(10)
            font_link.setUnderline(True)
            item.setFont(1, font_link)

            # Если это реестровый номер, вшиваем ссылку на ЕИС
            # (если контракт 223/44 ФЗ, можно адаптировать ссылку под нужный формат)
            if label_text == 'Реестровый номер договора':
                link = f"https://zakupki.gov.ru/epz/contract/search/results.html?searchString={value_text}"
                item.setData(1, Qt.UserRole, link)

    def add_json_to_tree(self, parent_item, json_data, parent_key=""):
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
            "text": "Текст",

            # Новые ключи из вашего запроса
            "totals summary": "Итоговая сводка",
            "section title": "Заголовок раздела",
            "Table": "Таблица",
            "Nested": "Вложенные данные",
            "Meta": "Метаданные",
            "Actions": "Действия",
            "Href": "Ссылка",
            "Print link": "Ссылка на печать",
            "Rows by index": "Строки по порядку",
            "table": "Таблица",
            "name": "Название",
            "quantitu": "Количество",
            # Исправлено с quantitu -> quantity (или оставлено как есть, если в JSON именно так)
            "price": "Цена",
            "sum": "Сумма",
            "ktru": "КТРУ",
            "raw_sum_text": "Текстовая сумма"
        }

        if not json_data:
            return

        if isinstance(json_data, dict):
            for key, value in json_data.items():
                # Если ключ пустой или null, используем заглушку
                if key == "null" or key is None:
                    display_key = "Параметр"
                else:
                    # Проверка на наличие перевода
                    if key in key_translations:
                        display_key = key_translations[key]
                    else:
                        # Если нет перевода, форматируем как есть (snake_case -> Title Case)
                        display_key = str(key).replace("_", " ").capitalize()

                if isinstance(value, (dict, list)):
                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, display_key)
                    font = QFont()
                    font.setBold(True)
                    child.setFont(0, font)
                    self.add_json_to_tree(child, value, key)
                else:
                    # Логика отображения значений (скаляров)
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
                        pass  # Обработка списков ссылок ниже в else if isinstance(json_data, list)
                    else:
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, display_key)
                        child.setText(1, str(value) if value is not None else "Нет данных")

        elif isinstance(json_data, list):
            for idx, item in enumerate(json_data):
                if isinstance(item, (dict, list)):
                    # Определение имени для вложенных объектов
                    child_name = f"Запись {idx + 1}"

                    # Специфичные имена для контекста (например, заголовки или ссылки)
                    if parent_key == "headers":
                        child_name = f"Колонка {idx + 1}"
                    elif parent_key in ("all_hrefs", "hrefs"):
                        child_name = f"Ссылка {idx + 1}"

                    # Если родительский ключ совпадает с новыми полями, можно дать более точное имя
                    if parent_key == "totals summary":
                        child_name = f"Пункт сводки {idx + 1}"
                    elif parent_key in ("rows", "Rows by index"):
                        child_name = f"Строка {idx + 1}"

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
                    # Если в списке простые значения (например, массив строк или чисел)
                    if parent_key == "headers":
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, f"Колонка {idx + 1}")
                        child.setText(1, str(item) if item is not None else "Нет данных")
                    elif parent_key in ("all_hrefs", "hrefs"):
                        # Обработка списка ссылок вложенных объектов (если вдруг это не dict внутри list)
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, f"Ссылка {idx + 1}")
                        child.setText(1, str(item))
                        child.setForeground(1, Qt.blue)
                        font_link = QFont()
                        font_link.setUnderline(True)
                        child.setFont(1, font_link)
                        child.setData(1, Qt.UserRole, str(item))
                    else:
                        child = QTreeWidgetItem(parent_item)
                        child.setText(0, f"Элемент {idx + 1}")
                        child.setText(1, str(item) if item is not None else "Нет данных")
        else:
            parent_item.setText(1, str(json_data))

    def show_current_contract(self):
        self.tree.clear()
        self.current_parent = None

        if len(self.contracts_list) != 0:
            c = self.contracts_list[self.current_position]
            self.current_contract = c

            # Заголовок
            title_text = f"№ {c.ContractNumber}" if c.ContractNumber else f"ID {c.Id}"
            self.label_form.setText(f"Формуляр контракта {title_text}")
            self.label_form.show()

            # --- 1. Основные реквизиты (развернуто) ---
            self.add_section_to_table('Общие сведения', expanded=True)
            self.add_row_to_table('ID в БД', c.Id)
            self.add_row_to_table('№ договора', c.ContractNumber)
            self.add_row_to_table('Реестровый номер договора', c.RegistryNumber)
            self.add_row_to_table('Идентификатор договора', c.ContractIdentifier)
            self.add_row_to_table('Заказчик по контракту', c.ContractingAuthority)
            self.add_row_to_table('Победитель-исполнитель', c.WinnerExecutor)
            self.add_row_to_table('Дата начала', c.StartDate)
            self.add_row_to_table('Дата окончания', c.EndDate)

            # --- 2. Финансы (развернуто) ---
            self.add_section_to_table('Финансовая информация', expanded=True)

            price = f"{format_string('%.2f', c.ContractPrice, grouping=True)} {self.symbol}" if c.ContractPrice is not None else None
            advance = f"{format_string('%.2f', c.AdvancePayment, grouping=True)} {self.symbol}" if c.AdvancePayment is not None else None
            reduction = f"{format_string('%.2f', c.ReductionNMC, grouping=True)} {self.symbol}" if c.ReductionNMC is not None else None
            reduction_pct = f"{format_string('%.2f', c.ReductionNMCPercent)} %" if c.ReductionNMCPercent is not None else None

            self.add_row_to_table('Цена договора', price)
            self.add_row_to_table('Размер авансирования', advance)
            self.add_row_to_table('Снижение НМЦК (руб.)', reduction)
            self.add_row_to_table('Снижение НМЦК (%)', reduction_pct)

            # --- 3. Данные по заявкам (свернуто) ---
            self.add_section_to_table('Данные по заявкам', expanded=False)
            self.add_row_to_table('Всего заявок', c.TotalApplications)
            self.add_row_to_table('Допущено', c.AdmittedApplications)
            self.add_row_to_table('Отклонено', c.RejectedApplications)

            # Парсинг простых массивов/списков из текстовых полей, если они есть
            for label, field_data in [
                ("Ценовое предложение", c.PriceProposal),
                ("Заявитель", c.Applicant),
                ("Статус заявителя", c.Applicant_satatus)
            ]:
                if field_data and field_data != "[]":
                    try:
                        parsed = json.loads(field_data)
                        self.add_json_to_tree(self.current_parent, parsed, label)
                    except json.JSONDecodeError:
                        self.add_row_to_table(label, field_data)

            # --- 4. Документы (свернуто) ---
            self.add_section_to_table('Прикрепленные документы', expanded=False)
            self.add_row_to_table('Протоколы (выписка)', c.SupplierProtocol)
            self.add_row_to_table('Договор', c.ContractFile)

            # --- 5. JSON Данные ---
            json_fields = [
                ("Общая информация контракта", c.common_info_json),
                ("Платежи и объекты закупки контракта", c.payment_targets_json),
                ("Исполнение (расторжение) контракта", c.process_info_json),
                ("Вложения контракта", c.documents_json),
                ("Журнал версий контракта", c.journal_versions_json),
                ("Журнал событий контракта", c.event_log_json),
            ]

            for section_name, json_string in json_fields:
                self.add_section_to_table(section_name, expanded=False)

                if json_string and str(json_string).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed_json = json.loads(json_string)
                        self.add_json_to_tree(self.current_parent, parsed_json)
                    except json.JSONDecodeError:
                        self.add_row_to_table("Данные", str(json_string))
                else:
                    self.add_row_to_table("Данные", "Нет данных")
                # =========================================================
                # СВЯЗАННЫЕ ДАННЫЕ (ПОСТАВЩИКИ, СУДА, ВЕРСИИ)
                # =========================================================
            self.add_section_to_table('Связанные документы', expanded=True)
            links_parent = self.current_parent

            # 1. ПОСТАВЩИКИ (Исполнители)
            suppliers = (
                Supplier
                .select()
                .join(SupplierContract)
                .where(SupplierContract.contract == c)
            )
            if suppliers.exists():
                for sup in suppliers:
                    sup_name = sup.organization if sup.organization else f"ID {sup.id}"
                    sup_node = QTreeWidgetItem(links_parent)
                    sup_node.setText(0, f"Поставщик: {sup_name}")
                    sup_node.setFirstColumnSpanned(True)
                    font_c = QFont()
                    font_c.setBold(True)
                    sup_node.setFont(0, font_c)
                    sup_node.setBackground(0, QColor(240, 240, 240))

                    link_item = QTreeWidgetItem(sup_node)
                    link_item.setText(0, 'Перейти в карточку поставщика')
                    link_item.setText(1, f"ID: {sup.id}")
                    link_item.setData(1, Qt.UserRole, f"GOTO_SUPPLIER:{sup.id}")
                    link_item.setForeground(1, Qt.blue)
                    font_link = QFont()
                    font_link.setUnderline(True)
                    link_item.setFont(1, font_link)

                    QTreeWidgetItem(sup_node, ['ИНН', str(sup.inn)])
                    QTreeWidgetItem(sup_node, ['КПП', str(sup.kpp)])

            # 2. ОБЪЕКТ ЗАКУПКИ (СУДА)
            vessels = Vessel.select().where(Vessel.contract == c)
            if vessels.exists():
                for ves in vessels:
                    v_name = f"Проект {ves.ship_project}" if ves.ship_project else f"ID {ves.id}"
                    ves_node = QTreeWidgetItem(links_parent)
                    ves_node.setText(0, f"Судно: {v_name}")
                    ves_node.setFirstColumnSpanned(True)
                    ves_node.setFont(0, font_c)
                    ves_node.setBackground(0, QColor(240, 240, 240))

                    link_item = QTreeWidgetItem(ves_node)
                    link_item.setText(0, 'Перейти в карточку судна')
                    link_item.setText(1, f"ID: {ves.id}")
                    link_item.setData(1, Qt.UserRole, f"GOTO_VESSEL:{ves.id}")
                    link_item.setForeground(1, Qt.blue)
                    link_item.setFont(1, font_link)

                    QTreeWidgetItem(ves_node, ['ИМО', str(ves.imo_number)])
                    QTreeWidgetItem(ves_node, ['Тип', str(ves.ship_type)])

            # 3. ВЕРСИИ КОНТРАКТА (Список)
            versions = ContractVersion.select().where(ContractVersion.contract == c).order_by(
                ContractVersion.version.desc())
            if versions.exists():
                font_c = QFont()
                font_c.setBold(True)

                font_link = QFont()
                font_link.setUnderline(True)

                ver_node = QTreeWidgetItem(links_parent)
                ver_node.setText(0, f"Версии контракта (Всего: {versions.count()})")
                ver_node.setFirstColumnSpanned(True)
                ver_node.setFont(0, font_c)
                ver_node.setBackground(0, QColor(240, 240, 240))
                ver_node.setExpanded(False)

                for ver in versions:
                    ver_title = f"Версия {ver.version}" if ver.version else f"Версия ID {ver.id}"
                    date_info = f" (обновлено {ver.date_updated_in_registry})" if ver.date_updated_in_registry else ""

                    link_item = QTreeWidgetItem(ver_node)
                    link_item.setText(0, f"{ver_title}{date_info}")
                    link_item.setText(1, "Перейти в версию")
                    link_item.setData(1, Qt.UserRole, f"GOTO_VERSION:{ver.id}")
                    link_item.setForeground(1, Qt.blue)
                    link_item.setFont(1, font_link)
            else:
                self.label_form.setText("Нет данных")
                self.label_form.show()

    def open_file(self, item, column):
        if column == 1:
            filepath = item.text(1)

            if filepath == "Нет данных":
                return

            if os.path.isfile(filepath):
                if filepath.lower().endswith(('.docx', '.doc')):
                    subprocess.Popen(['start', 'winword', filepath], shell=True)
                elif filepath.lower().endswith('.pdf'):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
                elif filepath.lower().endswith(('.xlsx', '.xls', '.csv')):
                    subprocess.Popen(['start', 'excel', filepath], shell=True)
            else:
                url = item.data(1, Qt.UserRole)
                if url:
                    QDesktopServices.openUrl(QUrl(url))
                elif 'http' in filepath or 'zakupki' in filepath:
                    QDesktopServices.openUrl(QUrl(filepath))
                elif 'download' in filepath:
                    url_for = item.text(1)
                    QDesktopServices.openUrl(QUrl(url_for))

    def open_file(self, item, column):
        if column == 1:
            filepath = item.text(1)
            if not filepath:
                return

            url_or_cmd = item.data(1, Qt.UserRole)

            # --- 1. ПРОВЕРКА НА ВНУТРЕННИЕ ПЕРЕХОДЫ ---
            if url_or_cmd and isinstance(url_or_cmd, str) and url_or_cmd.startswith("GOTO_"):
                command, record_id = url_or_cmd.split(":")
                record_id = int(record_id)

                # Сохраняем историю для кнопки Назад
                if hasattr(self.main_win, 'history'):
                    self.main_win.history.append(self.main_win.stackedWidget.currentIndex())

                # Переходы
                if command == "GOTO_SUPPLIER":
                    self.main_win.supplierFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(12)  # Замените на реальный индекс поставщика в MainWindow

                elif command == "GOTO_VESSEL":
                    self.main_win.vesselFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(13)  # Замените на реальный индекс судна

                elif command == "GOTO_VERSION":
                    self.main_win.contractVersionFormular.reload_data_id(record_id)
                    self.main_win.navigate_to_page(14)  # Замените на реальный индекс версии контракта

                return  # Прерываем, так как это не файл и не http ссылка
            # ----------------------------------------

            # --- 2. СТАНДАРТНОЕ ОТКРЫТИЕ ФАЙЛОВ И ССЫЛОК ---
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
                    url_for = item.text(1)
                    QDesktopServices.openUrl(QUrl(url_for))

    def export_to_excel(self):
        if not hasattr(self, 'current_contract') or self.current_contract is None:
            QMessageBox.warning(self, "Ошибка", "Нет текущего контракта для экспорта")
            return

        c = self.current_contract

        wb = Workbook()
        ws = wb.active
        ws.title = "Общие сведения"

        # Заголовки для транспонированной таблицы
        ws.append(["Параметр", "Значение"])

        # --- 1. Все скалярные поля модели Contract (транспонировано) ---
        for field in Contract._meta.fields.values():
            name = field.name
            verbose = field.verbose_name or name
            value = getattr(c, name, None)

            # JSON‑поля откладываем на отдельный лист
            if name.endswith('_json'):
                continue

            if value is None:
                value_str = "Нет данных"
            elif isinstance(value, (int, float)):
                value_str = value
            else:
                value_str = str(value)

            ws.append([verbose, value_str])

        # Автоширина колонок
        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 80

        # --- 2. JSON‑поля (отдельный лист) ---
        json_fields = [
            ("common_info_json", "Общая информация"),
            ("payment_targets_json", "Платежи и объекты закупки"),
            ("process_info_json", "Исполнение (расторжение)"),
            ("documents_json", "Вложения"),
            ("journal_versions_json", "Журнал версий"),
            ("event_log_json", "Журнал событий"),
        ]

        if any(getattr(c, fname, None) for fname, _ in json_fields):
            ws_json = wb.create_sheet("JSON данные")
            ws_json.append(["Поле", "Значение (JSON)"])

            for fname, label in json_fields:
                raw = getattr(c, fname, None)
                if raw and str(raw).strip() not in ("", "None", "-", "[]", "{}"):
                    try:
                        parsed = json_lib.loads(raw)
                        value_str = json_lib.dumps(parsed, ensure_ascii=False, indent=2)
                    except json_lib.JSONDecodeError:
                        value_str = str(raw)
                else:
                    value_str = "Нет данных"

                ws_json.append([label, value_str])

            ws_json.column_dimensions["A"].width = 35
            ws_json.column_dimensions["B"].width = 80

        # --- 3. Поставщики (Supplier через SupplierContract) ---
        suppliers = (
            Supplier
            .select()
            .join(SupplierContract)
            .where(SupplierContract.contract == c)
        )
        if suppliers.exists():
            ws_sup = wb.create_sheet("Поставщики")
            ws_sup.append(["ID", "Организация", "ИНН", "КПП", "Страна", "Адрес", "Телефон", "Email", "Статус"])

            for sup in suppliers:
                ws_sup.append([
                    sup.id,
                    sup.organization or "",
                    sup.inn or "",
                    sup.kpp or "",
                    sup.country or "",
                    sup.address or "",
                    sup.phone or "",
                    sup.mail or "",
                    sup.status or "",
                ])

            for col_idx in range(1, 10):
                ws_sup.column_dimensions[get_column_letter(col_idx)].width = 20

        # --- 4. Суда (Vessel) ---
        vessels = Vessel.select().where(Vessel.contract == c)
        if vessels.exists():
            ws_ves = wb.create_sheet("Суда")
            ws_ves.append([
                "ID", "Проект судна", "Тип (РМРС)", "Класс", "Год постройки",
                "Страна постройки", "Верфь", "Дедвейт", "Реестр. номер закупки"
            ])

            for ves in vessels:
                ws_ves.append([
                    ves.id,
                    ves.ship_project or "",
                    ves.ship_type_rmrs or "",
                    ves.ship_class or "",
                    ves.year_built or "",
                    ves.country_built or "",
                    ves.shipyard_name or "",
                    ves.deadweight or "",
                    ves.registry_number or "",
                ])

            for col_idx in range(1, 10):
                ws_ves.column_dimensions[get_column_letter(col_idx)].width = 20

        # --- 5. Версии контракта (ContractVersion) ---
        versions = (
            ContractVersion
            .select()
            .where(ContractVersion.contract == c)
            .order_by(ContractVersion.version.desc())
        )
        if versions.exists():
            ws_ver = wb.create_sheet("Версии контракта")
            ws_ver.append(["ID", "Версия", "Дата обновления в реестре"])

            for ver in versions:
                ws_ver.append([
                    ver.id,
                    ver.version or "",
                    ver.date_updated_in_registry or "",
                ])

            for col_idx in range(1, 4):
                ws_ver.column_dimensions[get_column_letter(col_idx)].width = 25

        # --- 6. Сохранение файла ---
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            if selected_file:
                # Формируем имя файла: "Контракт № ....xlsx"
                if c.ContractNumber:
                    safe_name = str(c.ContractNumber)
                else:
                    safe_name = str(c.Id)

                # Очищаем спецсимволы, чтобы ОС не ругалась на имя файла
                safe_name = "".join(ch for ch in safe_name if ch.isalnum() or ch in "._- ")

                save_path = f"{selected_file}/Контракт № {safe_name}.xlsx"
                wb.save(save_path)
                QMessageBox.information(self, "Успех", f"Данные успешно выгружены в {save_path}")