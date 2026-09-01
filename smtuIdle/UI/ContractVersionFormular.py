import json
import os
import subprocess
from locale import format_string, setlocale, LC_ALL
from openpyxl import Workbook
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices

# ВАЖНО: Убедитесь, что вы импортировали модель ContractVersion из вашего файла моделей
from smtuIdle.BD.models import ContractVersion


class ContractVersionWidget(QWidget):
    closingSignal = Signal()

    def __init__(self, mainwindow, role, user, changer):
        super().__init__()
        self.main_win = mainwindow
        self.role = role
        self.user = user
        self.changer = changer

        self.current_position = 0
        self.versions_list = []

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
        font_title.setPointSize(16)
        font_title.setBold(True)
        self.label_form.setFont(font_title)
        self.label_form.setAlignment(Qt.AlignHCenter)

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
        self.versions = ContractVersion.select()
        self.versions_list = list(self.versions)
        self.show_current_version()

    def reload_data_id(self, version_id):
        self.versions = ContractVersion.select().where(ContractVersion.id == version_id)
        self.versions_list = list(self.versions)
        self.show_current_version()

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

        # Подсветка ссылок
        link_fields = ['Ссылка на контракт', 'Ссылка на заказчика']
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

        Запись вида:

            {
                "kind": "kv",
                "title": "Дата заключения контракта",
                "text": "23.03.2026",
                "hrefs": []
            }

        отображается как:

            Дата заключения контракта | 23.03.2026
        """

        key_translations = {
            "title": "Название",
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
            "table": "Таблица",
            "nested": "Вложенные данные",
            "rows_by_index": "Строки таблицы",
            "totals_row": "Итоговая строка",
            "totals_summary": "Итоговая сводка",
        }

        if json_data in (None, "", [], {}):
            return

        # ---------------------------------------------------------
        # Запись вида kind == "kv"
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

            # Ссылки используются, но отдельно в дерево не выводятся
            hrefs = json_data.get("hrefs") or []

            if hrefs:
                item.setForeground(1, Qt.blue)

                link_font = QFont()
                link_font.setPointSize(10)
                link_font.setUnderline(True)
                item.setFont(1, link_font)

                item.setData(
                    1,
                    Qt.UserRole,
                    str(hrefs[0])
                )

            return

        # ---------------------------------------------------------
        # Словарь
        # ---------------------------------------------------------
        if isinstance(json_data, dict):
            for key, value in json_data.items():

                # Технические поля скрываем
                if key in ("kind", "hrefs", "all_hrefs"):
                    continue

                # Узел items пропускаем и сразу выводим его содержимое
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

                # Не дублируем служебный header внутри раздела
                if key == "header" and parent_key:
                    continue

                # Пустые поля не показываем
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
        # Список
        # ---------------------------------------------------------
        if isinstance(json_data, list):
            for index, value in enumerate(json_data):

                # kind == kv сразу становится строкой title | text
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

        # Простое скалярное значение
        parent_item.setText(1, str(json_data))

    def show_current_version(self):
        self.tree.clear()
        self.current_parent = None

        if len(self.versions_list) != 0:
            cv = self.versions_list[self.current_position]
            self.current_version = cv

            # Заголовок
            title_text = cv.version if cv.version else "Неизвестна"
            reg_text = cv.reg_number if cv.reg_number else "б/н"
            self.label_form.setText(f"Версия контракта №{reg_text} (Версия: {title_text})")
            self.label_form.show()

            # --- 1. Основные реквизиты версии (развернуто) ---
            self.add_section_to_table('Сведения о версии', expanded=True)
            self.add_row_to_table('Идентификатор БД', cv.id)
            self.add_row_to_table('ID Оригинального контракта', cv.contract_id)
            self.add_row_to_table('Реестровый номер', cv.reg_number)
            self.add_row_to_table('Версия из реестра', cv.version)
            self.add_row_to_table('Статус', cv.status)
            self.add_row_to_table('Закон', cv.law)

            if isinstance(cv.captured_at, datetime):
                captured_str = cv.captured_at.strftime('%d.%m.%Y %H:%M:%S')
            else:
                captured_str = cv.captured_at
            self.add_row_to_table('Дата и время снимка', captured_str)

            # --- 2. Содержимое контракта в этой версии (развернуто) ---
            self.add_section_to_table('Данные контракта', expanded=True)
            self.add_row_to_table('Номер контракта', cv.number)
            self.add_row_to_table('Наименование объекта', cv.object_name)
            self.add_row_to_table('Заказчик', cv.customer_name)
            self.add_row_to_table('Цена контракта', cv.contract_price)

            # --- 3. Даты и ссылки (свернуто) ---
            self.add_section_to_table('Даты и ссылки', expanded=False)
            self.add_row_to_table('Дата подписания', cv.date_contract_signed)
            self.add_row_to_table('Дата исполнения', cv.date_execution_due)
            self.add_row_to_table('Дата регистрации', cv.date_registered)
            self.add_row_to_table('Дата обновления в реестре', cv.date_updated_in_registry)
            self.add_row_to_table('Ссылка на контракт', cv.contract_url)
            self.add_row_to_table('Ссылка на заказчика', cv.customer_url)

            # --- 4. JSON Слепки данных ---
            json_fields = [
                ("Общая информация (детали)", cv.common_info_json),
                ("Платежи и объекты закупки", cv.payment_targets_json),
                ("Исполнение (расторжение)", cv.process_info_json),
                ("Вложения", cv.documents_json),
                ("Журнал версий", cv.journal_versions_json),
                ("Журнал событий", cv.event_log_json)
            ]

            for section_name, json_string in json_fields:
                self.add_section_to_table(
                    section_name,
                    expanded=False
                )

                if json_string and str(json_string).strip() not in (
                        "",
                        "None",
                        "-",
                        "[]",
                        "{}"
                ):
                    try:
                        parsed_json = json.loads(json_string)

                        # items пропускается внутри add_json_to_tree
                        self.add_json_to_tree(
                            self.current_parent,
                            parsed_json
                        )

                    except json.JSONDecodeError:
                        self.add_row_to_table(
                            "Содержимое JSON",
                            str(json_string)
                        )
                else:
                    self.add_row_to_table("Данные", "Нет данных")

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
            if selected_file and hasattr(self, 'current_version'):
                safe_reg = str(self.current_version.reg_number) if self.current_version.reg_number else str(
                    self.current_version.id)
                safe_ver = str(self.current_version.version) if self.current_version.version else "latest"

                safe_reg = "".join(x for x in safe_reg if x.isalnum() or x in "._- ")
                safe_ver = "".join(x for x in safe_ver if x.isalnum() or x in "._- ")

                save_path = f"{selected_file}/ContractVersion_{safe_reg}_v{safe_ver}.xlsx"
                wb.save(save_path)
                QMessageBox.information(self, "Успех", f"Данные успешно выгружены в {save_path}")