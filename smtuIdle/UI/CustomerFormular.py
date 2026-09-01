import json
import os
import subprocess
from openpyxl import Workbook

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices

# ВАЖНО: Убедитесь, что вы импортировали модель Customer из вашего файла моделей
from smtuIdle.BD.models import Customer


class CustomerWidget(QWidget):
    closingSignal = Signal()

    def __init__(self, mainwindow, role, user, changer):
        super().__init__()
        self.main_win = mainwindow
        self.role = role
        self.user = user
        self.changer = changer

        self.current_position = 0
        self.customers_list = []

        # --- Создание дерева (вместо таблицы) ---
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
        self.customers = Customer.select()
        self.customers_list = list(self.customers)
        self.show_current_customer()

    def reload_data_id(self, customer_id):
        self.customers = Customer.select().where(Customer.id == customer_id)
        self.customers_list = list(self.customers)
        self.show_current_customer()

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

        # Делаем URL кликабельными
        link_fields = [
            'Сайт организации', 'Ссылка на закупки',
            'Ссылка на контракты', 'Формуляр аккаунта', 'Доп. информация (url)'
        ]

        if label_text in link_fields and value_text != "Нет данных":
            item.setForeground(1, Qt.blue)
            font_link = QFont()
            font_link.setPointSize(10)
            font_link.setUnderline(True)
            item.setFont(1, font_link)
            item.setData(1, Qt.UserRole, value_text)

    def add_json_to_tree(self, parent_item, json_data, parent_key=""):
        """
        Упрощённое отображение JSON в дереве.

        kind == "kv":
            {
                "kind": "kv",
                "title": "...",
                "text": "...",
                "hrefs": [...]
            }
        отображается одной строкой:
            title | text
        """

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
            "table standalone": "Отдельная таблица",
            "url": "Ссылка",
            "parsed_table": "Табличные данные",
            "rows": "Строки таблицы",
            "headers": "Заголовки колонок",
            "doc_name": "Название документа",
            "files": "Файлы",
            "links": "Связанные ссылки",
            "text": "Текст",
                    "Table": "Таблица"
        }

        if json_data in (None, "", [], {}):
            return

        # Обработка записей kind == "kv"
        if isinstance(json_data, dict) and json_data.get("kind") == "kv":
            title = json_data.get("title") or "Параметр"
            text = json_data.get("text")

            item = QTreeWidgetItem(parent_item)
            item.setText(0, str(title))
            item.setText(1, str(text) if text not in (None, "") else "Нет данных")

            font = QFont()
            font.setPointSize(10)
            item.setFont(0, font)
            item.setFont(1, font)

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

        # Обработка словаря
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key in ("kind", "hrefs", "all_hrefs"):
                    continue

                if key == "items":
                    if isinstance(value, list):
                        for item_value in value:
                            self.add_json_to_tree(parent_item, item_value, "items")
                    elif isinstance(value, dict):
                        self.add_json_to_tree(parent_item, value, "items")
                    continue

                if key == "header" and parent_key:
                    continue

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

                    self.add_json_to_tree(child, value, key)
                else:
                    child = QTreeWidgetItem(parent_item)
                    child.setText(0, display_key)
                    child.setText(1, str(value))

            return

        # Обработка списка
        if isinstance(json_data, list):
            for index, value in enumerate(json_data):
                if isinstance(value, dict) and value.get("kind") == "kv":
                    self.add_json_to_tree(parent_item, value, parent_key)
                    continue

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

                    self.add_json_to_tree(child, value, parent_key)
                else:
                    child = QTreeWidgetItem(parent_item)

                    if parent_key == "headers":
                        child.setText(0, f"Колонка {index + 1}")
                    else:
                        child.setText(0, f"Элемент {index + 1}")

                    child.setText(
                        1,
                        str(value) if value is not None else "Нет данных"
                    )

            return

        parent_item.setText(1, str(json_data))

    def show_current_customer(self):
        self.tree.clear()
        self.current_parent = None

        if len(self.customers_list) != 0:
            current_customer = self.customers_list[self.current_position]
            self.current_customer = current_customer

            # Заголовок
            if current_customer.name:
                self.label_form.setText(f"Формуляр заказчика: {current_customer.name}")
            else:
                self.label_form.setText("Формуляр заказчика")
            self.label_form.show()

            # --- 1. Основные реквизиты (развёрнуто) ---
            self.add_section_to_table('Общие сведения', expanded=True)
            self.add_row_to_table('Идентификатор БД', current_customer.id)
            self.add_row_to_table('Наименование', current_customer.name)
            self.add_row_to_table('Закон', current_customer.law)
            self.add_row_to_table('ОГРН', current_customer.ogrn)
            self.add_row_to_table('ИНН', current_customer.inn)
            self.add_row_to_table('КПП', current_customer.kpp)
            self.add_row_to_table('Код заказчика', current_customer.customer_code)
            self.add_row_to_table('ID организации', current_customer.organization_id)

            # --- 2. Контактная информация (свёрнуто) ---
            self.add_section_to_table('Контактная информация', expanded=False)
            self.add_row_to_table('Страна', current_customer.country)
            self.add_row_to_table('Регион', current_customer.region)
            self.add_row_to_table('Город', current_customer.city)
            self.add_row_to_table('Полный адрес', current_customer.address_full)

            # --- 3. Ссылки ЕИС (свёрнуто) ---
            self.add_section_to_table('Ссылки и ресурсы', expanded=False)
            self.add_row_to_table('Сайт организации', current_customer.organization_url)
            self.add_row_to_table('Ссылка на закупки', current_customer.purchases_url)
            self.add_row_to_table('Ссылка на контракты', current_customer.contracts_url)
            self.add_row_to_table('Формуляр аккаунта', current_customer.account_card_url)
            self.add_row_to_table('Доп. информация (url)', current_customer.additional_info_url)

            # --- 4. JSON Данные (свёрнуто) ---
            json_fields = [
                ("Вложения", current_customer.documents_card_json),
                ("Дополнительная информация", current_customer.additional_info_json),
                ("Журнал версий", current_customer.journal_versions_json)
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
                if url and ('http' in url or 'zakupki' in url):
                    QDesktopServices.openUrl(QUrl(url))
                elif 'http' in filepath or 'zakupki' in filepath:
                    QDesktopServices.openUrl(QUrl(filepath))
                elif 'download' in filepath:
                    url_for = item.text(1)
                    QDesktopServices.openUrl(QUrl(url_for))

    def export_to_excel(self):
        wb = Workbook()
        ws = wb.active

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent_item = root.child(i)
            ws.append([parent_item.text(0)])

            for j in range(parent_item.childCount()):
                child_item = parent_item.child(j)
                ws.append([child_item.text(0), child_item.text(1)])

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            if selected_file and hasattr(self, 'current_customer'):
                safe_name = (
                    str(self.current_customer.inn)
                    if self.current_customer.inn
                    else "Customer"
                )
                save_path = f"{selected_file}/Customer_{safe_name}.xlsx"
                wb.save(save_path)
                QMessageBox.information(
                    self, "Успех",
                    f"Данные успешно выгружены в {save_path}"
                )