"""
DocxReportGenerator — класс для создания аналитических отчётов в стиле ЕИС/закупок.

Формат отчёта:
- Шапка с метаданными (дата, источник, место)
- Нумерованные разделы с таблицами
- Цветовая кодировка перерасхода/экономии
- Технические боксы (с уровнем критичности)
- Основные выводы
- Футер

Требует: python-docx
pip install python-docx
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd


class DocxReportGenerator:
    """
    Генератор DOCX-отчётов в стиле аналитики по закупкам.
    
    Использование:
        gen = DocxReportGenerator()
        gen.add_header("Сравнение цены контракта с НМЦК", 
                      "2018-2025 годы | 44-ФЗ и 223-ФЗ | 529 контрактов | от 20 млн руб.")
        gen.add_metadata_table({
            "Дата формирования": "12 марта 2026 г.",
            "Источник данных": "ЕИС, реестр контрактов",
            "Место подготовки": "Санкт-Петербург, РФ"
        })
        gen.add_section("1. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ", "Анализ охватывает...")
        gen.add_kpi_table([...])
        gen.save("report.docx")
    """
    
    # ─── Цветовая схема ────────────────────────────────────────
    COLOR_CRITICAL_BG = RGBColor(255, 230, 230)      # светло-красный
    COLOR_CRITICAL_BORDER = RGBColor(192, 21, 47)    # красный
    
    COLOR_WARNING_BG = RGBColor(255, 240, 230)       # светло-оранжевый
    COLOR_WARNING_BORDER = RGBColor(168, 75, 47)     # оранжевый
    
    COLOR_INFO_BG = RGBColor(240, 245, 255)          # светло-синий
    COLOR_INFO_BORDER = RGBColor(98, 108, 113)       # серо-синий
    
    COLOR_SUCCESS_BG = RGBColor(230, 255, 240)       # светло-зелёный
    COLOR_SUCCESS_BORDER = RGBColor(33, 128, 141)    # бирюзовый
    
    # Градация перерасхода/экономии (для строк таблиц)
    COLOR_OVERSPEND_HIGH = RGBColor(255, 200, 200)   # > +100%
    COLOR_OVERSPEND_MED = RGBColor(255, 230, 220)    # +50...+100%
    COLOR_OVERSPEND_LOW = RGBColor(255, 245, 235)    # до +50%
    COLOR_ECONOMY_LOW = RGBColor(240, 255, 240)      # до -20%
    COLOR_ECONOMY_MED = RGBColor(220, 255, 230)      # -20...-50%
    COLOR_ECONOMY_HIGH = RGBColor(200, 255, 220)     # < -50%
    
    def __init__(self):
        self.doc = Document()
        self._setup_styles()
        
    def _setup_styles(self):
        """Настройка базовых стилей документа."""
        # Поля страницы
        sections = self.doc.sections
        for section in sections:
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2.5)
            section.right_margin = Cm(1.5)
            # ← Альбомная ориентация (A4: 297mm × 210mm)
            section.page_width = Cm(29.7)
            section.page_height = Cm(21.0)
    def _set_cell_border(self, cell, **kwargs):
        """Установка границ ячейки таблицы."""
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        
        tcBorders = OxmlElement('w:tcBorders')
        for edge in ('top', 'left', 'bottom', 'right'):
            edge_data = kwargs.get(edge)
            if edge_data:
                edge_el = OxmlElement(f'w:{edge}')
                edge_el.set(qn('w:val'), edge_data.get('val', 'single'))
                edge_el.set(qn('w:sz'), str(edge_data.get('sz', 4)))
                edge_el.set(qn('w:space'), '0')
                edge_el.set(qn('w:color'), edge_data.get('color', '000000'))
                tcBorders.append(edge_el)
        tcPr.append(tcBorders)
        
    def _format_number(self, value, decimals=0) -> str:
        """
        Форматирование числа с разделением разрядов пробелом.
        0 или None → '-'
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return '-'
        if value == 0:
            return '-'
        
        if decimals == 0:
            return f"{int(value):,}".replace(',', ' ')
        else:
            return f"{value:,.{decimals}f}".replace(',', ' ')
    
    # ═══════════════════════════════════════════════════════════
    # ШАПКА ОТЧЁТА
    # ═══════════════════════════════════════════════════════════
    
    def add_header(self, title: str, subtitle: str = None):
        """
        Добавляет шапку отчёта:
        - Жирный заголовок (14pt)
        - Подзаголовок (12pt)
        """
        # Заголовок
        heading = self.doc.add_paragraph()
        run = heading.add_run("АНАЛИТИЧЕСКИЙ ОТЧЁТ")
        run.bold = True
        run.font.size = Pt(11)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Основное название
        title_p = self.doc.add_paragraph()
        title_run = title_p.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(14)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Подзаголовок
        if subtitle:
            sub_p = self.doc.add_paragraph()
            sub_run = sub_p.add_run(subtitle)
            sub_run.font.size = Pt(10)
            sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        # Разделитель
        self.doc.add_paragraph("─" * 80)
        
    def add_metadata_table(self, metadata: Dict[str, str]):
        """
        Метатаблица с ключ-значение парами:
        Дата формирования: | 11 марта 2026 г.
        Источник данных:   | ЕИС, реестр...
        """
        table = self.doc.add_table(rows=len(metadata), cols=2)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.LEFT
        
        for i, (key, value) in enumerate(metadata.items()):
            row = table.rows[i]
            
            # Ключ (жирный)
            cell_key = row.cells[0]
            p_key = cell_key.paragraphs[0]
            run_key = p_key.add_run(key)
            run_key.bold = True
            run_key.font.size = Pt(10)
            
            # Значение
            cell_val = row.cells[1]
            p_val = cell_val.paragraphs[0]
            run_val = p_val.add_run(value)
            run_val.font.size = Pt(10)
            
        self.doc.add_paragraph()  # пустая строка
        
    # ═══════════════════════════════════════════════════════════
    # РАЗДЕЛЫ
    # ═══════════════════════════════════════════════════════════
    
    def add_section(self, heading: str, intro_text: str = None):
        """
        Добавляет нумерованный раздел с заголовком.
        Пример: "1. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ: ЦЕНА vs НМЦК"
        """
        h = self.doc.add_paragraph()
        run = h.add_run(heading)
        run.bold = True
        run.font.size = Pt(12)
        
        if intro_text:
            p = self.doc.add_paragraph(intro_text)
            p_format = p.paragraph_format
            p_format.space_after = Pt(6)
            for run in p.runs:
                run.font.size = Pt(10)
                
    # ═══════════════════════════════════════════════════════════
    # ТАБЛИЦЫ
    # ═══════════════════════════════════════════════════════════
    def _rgb_to_hex(self, rgb_color: RGBColor) -> str:
        """Конвертация RGBColor в hex-строку. str(RGBColor) возвращает 'RRGGBB'."""
        return str(rgb_color)
    def add_kpi_table(self, data: List[Tuple[str, str, str, str]],
                      col_headers: List[str] = None,
                      row_colors: List[Optional[RGBColor]] = None):  # ← новый параметр
        if col_headers is None:
            col_headers = ["Показатель", "Итого", "44-ФЗ", "223-ФЗ"]

        table = self.doc.add_table(rows=1 + len(data), cols=len(col_headers))
        table.style = 'Table Grid'

        # Заголовки (без изменений)
        hdr_cells = table.rows[0].cells
        for i, hdr_text in enumerate(col_headers):
            cell = hdr_cells[i]
            p = cell.paragraphs[0]
            run = p.add_run(hdr_text)
            run.bold = True
            run.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), 'E0E0E0')
            cell._element.get_or_add_tcPr().append(shading_elm)

        # Данные с цветовой кодировкой
        for row_idx, row_data in enumerate(data, start=1):
            row = table.rows[row_idx]

            # Определяем цвет для этой строки
            bg_color = None
            if row_colors and row_idx - 1 < len(row_colors):
                bg_color = row_colors[row_idx - 1]

            for col_idx, cell_text in enumerate(row_data):
                cell = row.cells[col_idx]
                p = cell.paragraphs[0]
                run = p.add_run(str(cell_text))
                run.font.size = Pt(9)
                if col_idx == 0:
                    run.bold = True

                # Применяем цвет строки
                if bg_color:
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:fill'), self._rgb_to_hex(bg_color))
                    cell._element.get_or_add_tcPr().append(shading_elm)

        self.doc.add_paragraph()
        
    def add_comparison_table(self, data: List[Tuple], 
                             col_headers: List[str],
                             color_column_idx: int = None,
                             color_thresholds: Dict = None):
        """
        Сравнительная таблица с возможностью цветовой кодировки строк.
        
        data: список кортежей (по одному на строку)
        col_headers: заголовки колонок
        color_column_idx: индекс колонки с Δ% для цветовой кодировки
        color_thresholds: {"high": 100, "med": 50, "low": 0, "neg_low": -20, ...}
        """
        table = self.doc.add_table(rows=1 + len(data), cols=len(col_headers))
        table.style = 'Table Grid'
        
        # Заголовки
        hdr_cells = table.rows[0].cells
        for i, hdr_text in enumerate(col_headers):
            cell = hdr_cells[i]
            p = cell.paragraphs[0]
            run = p.add_run(hdr_text)
            run.bold = True
            run.font.size = Pt(8)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), 'D0D0D0')
            cell._element.get_or_add_tcPr().append(shading_elm)
            
        # Данные
        for row_idx, row_data in enumerate(data, start=1):
            row = table.rows[row_idx]
            
            # Определяем цвет строки по Δ%
            bg_color = None
            if color_column_idx is not None and color_thresholds:
                delta_pct = row_data[color_column_idx]
                if isinstance(delta_pct, (int, float)):
                    bg_color = self._get_delta_color(delta_pct, color_thresholds)
                    
            for col_idx, cell_text in enumerate(row_data):
                cell = row.cells[col_idx]
                p = cell.paragraphs[0]
                run = p.add_run(str(cell_text))
                run.font.size = Pt(8)
                
                # Жирный для чисел с перерасходом
                if col_idx == color_column_idx and isinstance(cell_text, (int, float)):
                    if cell_text > 50:
                        run.bold = True
                        
                # Установка фона
                if bg_color:
                    shading_elm = OxmlElement('w:shd')
                    color_hex = str(bg_color)  # ← правильное имя переменной
                    shading_elm.set(qn('w:fill'), color_hex.upper())
                    cell._element.get_or_add_tcPr().append(shading_elm)

        self.doc.add_paragraph()
        
    def _get_delta_color(self, delta_pct: float, thresholds: Dict) -> RGBColor:
        """Возвращает цвет фона в зависимости от Δ%."""
        if delta_pct > thresholds.get('high', 100):
            return self.COLOR_OVERSPEND_HIGH
        elif delta_pct > thresholds.get('med', 50):
            return self.COLOR_OVERSPEND_MED
        elif delta_pct > 0:
            return self.COLOR_OVERSPEND_LOW
        elif delta_pct > thresholds.get('neg_low', -20):
            return self.COLOR_ECONOMY_LOW
        elif delta_pct > thresholds.get('neg_med', -50):
            return self.COLOR_ECONOMY_MED
        else:
            return self.COLOR_ECONOMY_HIGH
            
    def add_summary_table(self, data: Dict[str, List], 
                         footnote: str = None):
        """
        Сводная таблица по законам (44-ФЗ vs 223-ФЗ).
        
        data: {
            "headers": ["Показатель", "44-ФЗ", "223-ФЗ", "Примечание"],
            "rows": [
                ["Всего контрактов", "279", "250", ""],
                ["Цена > НМЦК", "14 / 5.0%", "30 / 12.0%", "По 223-ФЗ в 2.4× чаще"],
                ...
            ]
        }
        """
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        
        table = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.style = 'Table Grid'
        
        # Заголовки
        hdr_cells = table.rows[0].cells
        for i, hdr_text in enumerate(headers):
            cell = hdr_cells[i]
            p = cell.paragraphs[0]
            run = p.add_run(hdr_text)
            run.bold = True
            run.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), 'E8E8E8')
            cell._element.get_or_add_tcPr().append(shading_elm)
            
        # Данные
        for row_idx, row_data in enumerate(rows, start=1):
            row = table.rows[row_idx]
            for col_idx, cell_text in enumerate(row_data):
                cell = row.cells[col_idx]
                p = cell.paragraphs[0]
                
                # Первая колонка жирным
                if col_idx == 0:
                    run = p.add_run(str(cell_text))
                    run.bold = True
                    run.font.size = Pt(9)
                else:
                    run = p.add_run(str(cell_text))
                    run.font.size = Pt(9)
                    
                    # Примечания курсивом
                    if col_idx == len(headers) - 1 and cell_text:
                        run.italic = True
                        
        if footnote:
            p = self.doc.add_paragraph(footnote)
            p_run = p.runs[0]
            p_run.font.size = Pt(8)
            p_run.italic = True
            
        self.doc.add_paragraph()
        
    def add_distribution_table(self, data: Dict[str, List]):
        """
        Таблица распределения по диапазонам (< -50%, -50...-20%, и т.д.).
        
        data: {
            "headers": ["Диапазон Δ%", "Кол-во 44-ФЗ", "Кол-во 223-ФЗ", "Итого"],
            "rows": [
                ["< -50%", "0", "10", "10"],
                ["-50% ... -20%", "0", "32", "52"],
                ...
            ],
            "totals": ["ИТОГО", "0", "250", "529"]
        }
        """
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        totals = data.get("totals", None)
        
        table = self.doc.add_table(
            rows=1 + len(rows) + (1 if totals else 0), 
            cols=len(headers)
        )
        table.style = 'Table Grid'
        
        # Заголовки
        hdr_cells = table.rows[0].cells
        for i, hdr_text in enumerate(headers):
            cell = hdr_cells[i]
            p = cell.paragraphs[0]
            run = p.add_run(hdr_text)
            run.bold = True
            run.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), 'D8D8D8')
            cell._element.get_or_add_tcPr().append(shading_elm)
            
        # Данные
        for row_idx, row_data in enumerate(rows, start=1):
            row = table.rows[row_idx]
            for col_idx, cell_text in enumerate(row_data):
                cell = row.cells[col_idx]
                p = cell.paragraphs[0]
                run = p.add_run(str(cell_text))
                run.font.size = Pt(9)
                
                # Центрирование числовых колонок
                if col_idx > 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
        # Итоговая строка
        if totals:
            row = table.rows[1 + len(rows)]
            for col_idx, cell_text in enumerate(totals):
                cell = row.cells[col_idx]
                p = cell.paragraphs[0]
                run = p.add_run(str(cell_text))
                run.bold = True
                run.font.size = Pt(9)
                
                if col_idx > 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                # Фон итоговой строки
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:fill'), 'F0F0F0')
                cell._element.get_or_add_tcPr().append(shading_elm)
                
        self.doc.add_paragraph()
        
    # ═══════════════════════════════════════════════════════════
    # ТЕХНИЧЕСКИЕ БОКСЫ
    # ═══════════════════════════════════════════════════════════
    
    def add_technical_box(self, title: str, content: str, 
                         level: str = "info"):
        """
        Технический бокс с рамкой и фоном.
        
        level: "critical" | "warning" | "info" | "success"
        """
        level_map = {
            "critical": (self.COLOR_CRITICAL_BG, self.COLOR_CRITICAL_BORDER, "Критическая"),
            "warning": (self.COLOR_WARNING_BG, self.COLOR_WARNING_BORDER, "Требует проверки"),
            "info": (self.COLOR_INFO_BG, self.COLOR_INFO_BORDER, "Информационная"),
            "success": (self.COLOR_SUCCESS_BG, self.COLOR_SUCCESS_BORDER, "Системный паттерн"),
        }
        
        bg_color, border_color, label = level_map.get(level, level_map["info"])
        
        # Таблица 1x1 для бокса
        table = self.doc.add_table(rows=1, cols=1)
        cell = table.rows[0].cells[0]
        
        # Фон
        shading_elm = OxmlElement('w:shd')
        color_hex = str(bg_color)
        shading_elm.set(qn('w:fill'), color_hex.upper())
        cell._element.get_or_add_tcPr().append(shading_elm)
        
        # Рамка
        border_hex = str(border_color)
        self._set_cell_border(
            cell,
            top={'val': 'single', 'sz': 12, 'color': border_hex},
            left={'val': 'single', 'sz': 12, 'color': border_hex},
            bottom={'val': 'single', 'sz': 12, 'color': border_hex},
            right={'val': 'single', 'sz': 12, 'color': border_hex}
        )
        
        # Заголовок бокса
        p_title = cell.paragraphs[0]
        run_title = p_title.add_run(f"{title} | {label}")
        run_title.bold = True
        run_title.font.size = Pt(10)
        
        # Содержимое
        p_content = cell.add_paragraph(content)
        p_content.paragraph_format.space_before = Pt(4)
        for run in p_content.runs:
            run.font.size = Pt(9)
            
        self.doc.add_paragraph()
        
    # ═══════════════════════════════════════════════════════════
    # ОСНОВНЫЕ ВЫВОДЫ
    # ═══════════════════════════════════════════════════════════
    
    def add_conclusions(self, conclusions: List[Tuple[str, str]]):
        """
        Раздел "ОСНОВНЫЕ ВЫВОДЫ" с нумерованными тезисами.
        
        conclusions: [
            ("Чистый перерасход за 8 лет — 53.7 млрд руб.", 
             "Суммарный перерасход (57.1 млрд) кратно превышает экономию..."),
            ("44-ФЗ дисциплинирует цену лучше", 
             "По 44-ФЗ перерасход встречается в 2.4× реже..."),
            ...
        ]
        """
        h = self.doc.add_paragraph()
        run = h.add_run("ОСНОВНЫЕ ВЫВОДЫ")
        run.bold = True
        run.font.size = Pt(12)
        
        for idx, (heading, text) in enumerate(conclusions, start=1):
            p = self.doc.add_paragraph()
            
            # Нумерация + жирный заголовок
            run_num = p.add_run(f"{idx}. {heading}: ")
            run_num.bold = True
            run_num.font.size = Pt(10)
            
            # Текст
            run_text = p.add_run(text)
            run_text.font.size = Pt(10)
            
            p.paragraph_format.space_after = Pt(6)
            
        self.doc.add_paragraph()
        
    # ═══════════════════════════════════════════════════════════
    # ФУТЕР
    # ═══════════════════════════════════════════════════════════
    
    def add_footer(self, text: str = None):
        """
        Футер внизу страницы с датой и местом подготовки.
        По умолчанию: "Подготовлено: {текущая дата} | Санкт-Петербург, РФ"
        """
        if text is None:
            today = datetime.now().strftime("%d %B %Y г.").replace(
                "January", "января").replace("February", "февраля").replace(
                "March", "марта").replace("April", "апреля").replace(
                "May", "мая").replace("June", "июня").replace(
                "July", "июля").replace("August", "августа").replace(
                "September", "сентября").replace("October", "октября").replace(
                "November", "ноября").replace("December", "декабря")
            text = f"Подготовлено: {today} | Санкт-Петербург, Российская Федерация"
            
        self.doc.add_paragraph("─" * 80)
        
        p = self.doc.add_paragraph(text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.size = Pt(9)
            run.italic = True
            
    # ═══════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════
    
    def add_legend(self, legend_items: List[Tuple[str, RGBColor]]):
        """
        Легенда цветовой кодировки.
        
        legend_items: [
            ("Перерасход > +100%", COLOR_OVERSPEND_HIGH),
            ("Перерасход +50...+100%", COLOR_OVERSPEND_MED),
            ...
        ]
        """
        p = self.doc.add_paragraph()
        run = p.add_run("Цветовая кодировка:")
        run.bold = True
        run.font.size = Pt(9)
        
        table = self.doc.add_table(rows=len(legend_items), cols=2)
        table.style = 'Table Grid'
        
        for i, (label, color) in enumerate(legend_items):
            row = table.rows[i]
            
            # Цветной квадрат
            cell_color = row.cells[0]
            shading_elm = OxmlElement('w:shd')
            color_hex = str(color)
            shading_elm.set(qn('w:fill'), color_hex.upper())
            cell_color._element.get_or_add_tcPr().append(shading_elm)
            cell_color.width = Inches(0.3)
            
            # Текст
            cell_text = row.cells[1]
            p = cell_text.paragraphs[0]
            run = p.add_run(label)
            run.font.size = Pt(8)
            
        self.doc.add_paragraph()
        
    def add_paragraph(self, text: str, bold: bool = False, 
                     italic: bool = False, size: int = 10):
        """Добавить параграф с настройками."""
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.size = Pt(size)
        return p
        
    def add_page_break(self):
        """Разрыв страницы."""
        self.doc.add_page_break()
        
    # ═══════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ
    # ═══════════════════════════════════════════════════════════
    
    def save(self, filename: str):
        """Сохранить документ."""
        self.doc.save(filename)
        print(f"✓ Отчёт сохранён: {filename}")


# ═══════════════════════════════════════════════════════════════
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ═══════════════════════════════════════════════════════════════

def example_usage():
    """Демонстрация использования класса."""
    gen = DocxReportGenerator()
    
    # Шапка
    gen.add_header(
        "Сравнение цены контракта с НМЦК: перерасход и экономия",
        "2018-2025 годы | 44-ФЗ и 223-ФЗ | 529 контрактов | от 20 млн руб."
    )
    
    # Метаданные
    gen.add_metadata_table({
        "Дата формирования": "12 марта 2026 г.",
        "Источник данных": "ЕИС, реестр контрактов 44-ФЗ и 223-ФЗ (≥ 20 млн руб.)",
        "Место подготовки": "Санкт-Петербург, РФ"
    })
    
    # Раздел 1
    gen.add_section(
        "1. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ: ЦЕНА КОНТРАКТА vs НМЦК",
        "Анализ охватывает 529 контрактов сегмента ≥ 20 млн руб. за 2018-2025 годы. "
        "В 46.5% случаев цена контракта точно равна НМЦК — характерный признак "
        "единственного поставщика или несостоявшихся торгов."
    )
    
    # KPI-таблица
    gen.add_kpi_table([
        ("Всего контрактов загружено", "287 ед.", "-", "-"),
        ("Контрактов с указанной ценой", "257 ед.", "-", "115 (223-ФЗ)"),
        ("Цена контракта > НМЦК (↑)", "29 ед. / 11.3%", "-", "13 / 11.3%"),
        ("Цена контракта < НМЦК (↓)", "111 ед. / 43.2%", "-", "45 / 39.1%"),
        ("Цена контракта == НМЦК (=)", "117 ед. / 45.5%", "-", "57 / 49.6%"),
        ("Средняя дельта Δ%", "inf% (выбросы)", "-", "inf%"),
        ("Суммарный перерасход (> НМЦК)", "58 462 553 041 руб.", "-", "17 512 209 000 руб."),
        ("Суммарная экономия (< НМЦК)", "3 546 523 538 руб.", "-", "1 609 495 130 руб."),
    ],
        row_colors=[
            None,  # Всего загружено — без цвета
            None,  # Контрактов с ценой — без цвета
            gen.COLOR_OVERSPEND_LOW,  # Цена > НМЦК → светло-красный
            gen.COLOR_ECONOMY_LOW,  # Цена < НМЦК → светло-зелёный
            None,  # Цена == НМЦК → без цвета
            None,  # Средняя дельта → без цвета
            gen.COLOR_OVERSPEND_MED,  # Суммарный перерасход → красный
            gen.COLOR_ECONOMY_MED,  # Суммарная экономия → зелёный
        ])
    
    # Легенда
    gen.add_legend([
        ("Перерасход > +100%", gen.COLOR_OVERSPEND_HIGH),
        ("Перерасход +50...+100%", gen.COLOR_OVERSPEND_MED),
        ("Перерасход до +50%", gen.COLOR_OVERSPEND_LOW),
        ("Экономия до −20%", gen.COLOR_ECONOMY_LOW),
        ("Экономия −20...−50%", gen.COLOR_ECONOMY_MED),
        ("Экономия < −50%", gen.COLOR_ECONOMY_HIGH),
    ])
    
    # Раздел 2
    gen.add_section(
        "2. СРАВНЕНИЕ 44-ФЗ И 223-ФЗ: ЦЕНОВОЕ ОТКЛОНЕНИЕ",
        "По 44-ФЗ перерасход значительно реже (5.0% против 12.0% по 223-ФЗ) "
        "и меньше по среднему Δ (−0.75% против −2.26%)."
    )
    
    # Сводная таблица
    gen.add_summary_table({
        "headers": ["Показатель", "44-ФЗ", "223-ФЗ", "Примечание"],
        "rows": [
            ["Всего контрактов, ед.", "279", "250", ""],
            ["Цена > НМЦК (перерасход)", "14 / 5.0%", "30 / 12.0%", "По 223-ФЗ — в 2.4× чаще"],
            ["Цена < НМЦК (экономия)", "103 / 36.9%", "136 / 54.4%", "По 223-ФЗ — на 17.5 п.п. выше"],
            ["Средняя дельта Δ%", "−0.75%", "−2.26%", "По 223-ФЗ — в 3× глубже"],
        ]
    })
    
    # Технический бокс
    gen.add_technical_box(
        "1. Регистр поля law: «44-Фз» vs «44-ФЗ»",
        "В исходных данных поле law принимает два значения: «44-ФЗ» (корректное) и «44-Фз» "
        "(с строчной «з»). Рекомендуется нормализация: df['law'] = df['law'].str.upper().",
        level="critical"
    )
    
    # Выводы
    gen.add_conclusions([
        ("Чистый перерасход за 8 лет — 53.7 млрд руб.", 
         "Суммарный перерасход (57.1 млрд) кратно превышает экономию (3.4 млрд). "
         "Средняя дельта −1.46% выглядит незначительной, однако является средним по "
         "«здоровым» контрактам и нескольким контрактам с +100–+460%."),
        ("44-ФЗ дисциплинирует цену лучше, чем 223-ФЗ", 
         "По 44-ФЗ перерасход встречается в 2.4× реже (5.0% vs 12.0%), средняя дельта в 3× меньше. "
         "Это подтверждает, что конкурентные процедуры 44-ФЗ эффективнее сдерживают рост цены."),
    ])
    
    # Футер
    gen.add_footer()
    
    # Сохранение
    gen.save("example_report.docx")


if __name__ == "__main__":
    example_usage()
