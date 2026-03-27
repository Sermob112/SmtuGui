import os
import subprocess
from locale import format_string, setlocale, LC_ALL
from openpyxl import Workbook
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices

# ВАЖНО: Убедитесь, что вы импортировали модель Vessel из вашего файла моделей
from smtuIdle.BD.models import Vessel


class VesselWidget(QWidget):
    closingSignal = Signal()

    def __init__(self, mainwindow, role, user, changer):
        super().__init__()
        self.main_win = mainwindow
        self.role = role
        self.user = user
        self.changer = changer

        self.current_position = 0
        self.vessels_list = []

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
        self.vessels = Vessel.select()
        self.vessels_list = list(self.vessels)
        self.show_current_vessel()

    def reload_data_id(self, vessel_id):
        self.vessels = Vessel.select().where(Vessel.id == vessel_id)
        self.vessels_list = list(self.vessels)
        self.show_current_vessel()

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
            # Если передали дату, форматируем в строку
            if isinstance(value_text, date):
                value_text = value_text.strftime('%d.%m.%Y')
            # Если передали boolean (True/False)
            elif isinstance(value_text, bool):
                value_text = "Да" if value_text else "Нет"
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

    def show_current_vessel(self):
        self.tree.clear()
        self.current_parent = None

        if len(self.vessels_list) != 0:
            v = self.vessels_list[self.current_position]
            self.current_vessel = v

            # Заголовок
            title_text = f"Проект {v.ship_project}" if v.ship_project else f"ID {v.id}"
            if v.imo_number:
                title_text += f" (ИМО: {v.imo_number})"

            self.label_form.setText(f"Карточка судна: {title_text}")
            self.label_form.show()

            # --- 1. Идентификация ---
            self.add_section_to_table('Идентификация', expanded=True)
            self.add_row_to_table('Идентификатор БД', v.id)
            self.add_row_to_table('Номер ИМО', v.imo_number)
            self.add_row_to_table('Проект судна', v.ship_project)
            self.add_row_to_table('Реестровый номер', v.registry_number)
            self.add_row_to_table('Строительный номер', v.build_number)
            if v.purchase_id:
                self.add_row_to_table('ID Закупки', v.purchase_id)

            # --- 2. Классификация ---
            self.add_section_to_table('Классификация РМРС / РКО', expanded=True)
            self.add_row_to_table('Тип судна (РМРС)', v.ship_type_rmrs)
            self.add_row_to_table('Тип и назначение (РКО)', v.ship_type_rko)
            self.add_row_to_table('Класс', v.ship_class)
            self.add_row_to_table('Подкласс', v.subclass)
            self.add_row_to_table('Тип', v.ship_type)
            self.add_row_to_table('Подтип', v.subtype)
            self.add_row_to_table('Группа', v.group)
            self.add_row_to_table('Подгруппа', v.subgroup)

            # --- 3. Даты постройки ---
            self.add_section_to_table('Даты постройки', expanded=False)
            self.add_row_to_table('Год постройки', v.year_built)
            self.add_row_to_table('Дата закладки киля', v.date_keel_laid)
            self.add_row_to_table('Дата спуска на воду', v.date_launched)
            self.add_row_to_table('Дата постройки', v.date_built)
            self.add_row_to_table('Страна постройки', v.country_built)

            # --- 4. Размерения и вместимость ---
            self.add_section_to_table('Размерения и вместимость', expanded=False)
            self.add_row_to_table('Валовая вместимость', v.gross_tonnage)
            self.add_row_to_table('Чистая вместимость', v.net_tonnage)
            self.add_row_to_table('Дедвейт', v.deadweight)
            self.add_row_to_table('Водоизмещение наибольшее', v.displacement_max)
            self.add_row_to_table('Длина наибольшая', v.length_max)
            self.add_row_to_table('Ширина наибольшая', v.width_max)
            self.add_row_to_table('Высота борта наибольшая', v.height_max)
            self.add_row_to_table('Осадка наибольшая', v.draft_max)
            self.add_row_to_table('Кубический модуль', v.cubic_module)
            self.add_row_to_table('Отношение Длина/Ширина', v.length_width_ratio)
            self.add_row_to_table('Скорость наибольшая', v.speed_max)

            # --- 5. Грузовые характеристики и оборудование ---
            self.add_section_to_table('Грузовые характеристики и оборудование', expanded=False)
            self.add_row_to_table('Количество грузовых трюмов', v.cargo_holds_count)
            self.add_row_to_table('Наливные танки (кол-во)', v.liquid_tanks_count)
            self.add_row_to_table('Количество контейнеров TEU', v.teu_count)
            self.add_row_to_table('Количество палуб', v.decks_count)
            self.add_row_to_table('Количество переборок', v.bulkheads_count)
            self.add_row_to_table('Грузовые люки (кол-во)', v.hatches_count)
            self.add_row_to_table('Стрелы (кол-во)', v.booms_count)
            self.add_row_to_table('Краны (кол-во)', v.cranes_count)

            # --- 6. Пассажиры ---
            self.add_section_to_table('Пассажиры', expanded=False)
            self.add_row_to_table('Число пассажиров коечных', v.passengers_berth)
            self.add_row_to_table('Число пассажиров бескоечных', v.passengers_no_berth)

            # --- 7. Материалы и конструкция ---
            self.add_section_to_table('Материалы и конструкция', expanded=False)
            self.add_row_to_table('Материал корпуса', v.hull_material)
            self.add_row_to_table('Материал надстройки', v.superstructure_material)
            self.add_row_to_table('Наличие подводных крыльев', v.has_hydrofoil)

            # --- 8. Верфь постройки ---
            self.add_section_to_table('Верфь постройки', expanded=False)
            self.add_row_to_table('Верфь постройки судна', v.shipyard_name)
            self.add_row_to_table('Город постройки судна', v.city_built)
            self.add_row_to_table('Регион РФ', v.region_built)
            self.add_row_to_table('Федеральный округ', v.federal_district)
            self.add_row_to_table('ИНН верфи', v.shipyard_inn)
            self.add_row_to_table('КПП верфи', v.shipyard_kpp)
            self.add_row_to_table('ОГРН верфи', v.shipyard_ogrn)

        else:
            self.label_form.setText("Нет данных")
            self.label_form.show()

    def open_file(self, item, column):
        # Если в будущем добавятся ссылки, они будут обрабатываться здесь
        if column == 1:
            filepath = item.text(1)
            if filepath == "Нет данных":
                return

            url = item.data(1, Qt.UserRole)
            if url:
                QDesktopServices.openUrl(QUrl(url))

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
            if selected_file and hasattr(self, 'current_vessel'):
                safe_name = str(self.current_vessel.ship_project) if self.current_vessel.ship_project else str(
                    self.current_vessel.id)
                safe_name = "".join(x for x in safe_name if x.isalnum() or x in "._- ")

                save_path = f"{selected_file}/Vessel_{safe_name}.xlsx"
                wb.save(save_path)
                QMessageBox.information(self, "Успех", f"Данные успешно выгружены в {save_path}")