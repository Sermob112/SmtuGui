import os
import subprocess
from openpyxl import Workbook

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices

# ВАЖНО: Убедитесь, что вы импортировали модель Supplier из вашего файла моделей
from smtuIdle.BD.models import Supplier


class SupplierWidget(QWidget):
    closingSignal = Signal()

    def __init__(self, mainwindow, role, user, changer):
        super().__init__()
        self.main_win = mainwindow
        self.role = role
        self.user = user
        self.changer = changer

        self.current_position = 0
        self.suppliers_list = []

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
        self.suppliers = Supplier.select()
        self.suppliers_list = list(self.suppliers)
        self.show_current_supplier()

    def reload_data_id(self, supplier_id):
        self.suppliers = Supplier.select().where(Supplier.id == supplier_id)
        self.suppliers_list = list(self.suppliers)
        self.show_current_supplier()

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

        # Делаем Email или телефон кликабельным (опционально)
        if label_text == 'Email' and value_text != "Нет данных":
            item.setForeground(1, Qt.blue)
            font_link = QFont()
            font_link.setPointSize(10)
            font_link.setUnderline(True)
            item.setFont(1, font_link)
            item.setData(1, Qt.UserRole, f"mailto:{value_text}")

    def show_current_supplier(self):
        self.tree.clear()
        self.current_parent = None

        if len(self.suppliers_list) != 0:
            current_supplier = self.suppliers_list[self.current_position]
            self.current_supplier = current_supplier

            # Заголовок
            if current_supplier.organization:
                self.label_form.setText(f"Исполнитель: {current_supplier.organization}")
            else:
                self.label_form.setText("Формуляр исполнителя")
            self.label_form.show()

            # --- 1. Основные реквизиты (развернуто) ---
            self.add_section_to_table('Общие сведения', expanded=True)
            self.add_row_to_table('Идентификатор БД', current_supplier.id)
            self.add_row_to_table('Организация', current_supplier.organization)
            self.add_row_to_table('ИНН', current_supplier.inn)
            self.add_row_to_table('КПП', current_supplier.kpp)
            self.add_row_to_table('Статус', current_supplier.status)

            # Если нужно отобразить ID контракта, к которому привязан поставщик:
            if current_supplier.contract_id:
                self.add_row_to_table('ID Контракта', current_supplier.contract_id)

            # --- 2. Контактная информация (развернуто) ---
            self.add_section_to_table('Контактная информация', expanded=True)
            self.add_row_to_table('Страна', current_supplier.country)
            self.add_row_to_table('Адрес', current_supplier.address)
            self.add_row_to_table('Почтовый индекс', current_supplier.index_address)
            self.add_row_to_table('Телефон', current_supplier.phone)
            self.add_row_to_table('Email', current_supplier.mail)

        else:
            self.label_form.setText("Нет данных")
            self.label_form.show()

    def open_file(self, item, column):
        if column == 1:
            filepath = item.text(1)

            if filepath == "Нет данных":
                return

            # Если это Email-ссылка (mailto:)
            url = item.data(1, Qt.UserRole)
            if url and 'mailto:' in url:
                QDesktopServices.openUrl(QUrl(url))
                return

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
            if selected_file and hasattr(self, 'current_supplier'):
                safe_name = str(self.current_supplier.inn) if self.current_supplier.inn else "Supplier"
                save_path = f"{selected_file}/Supplier_{safe_name}.xlsx"
                wb.save(save_path)
                QMessageBox.information(self, "Успех", f"Данные успешно выгружены в {save_path}")