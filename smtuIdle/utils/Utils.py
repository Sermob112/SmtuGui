"""
Операционная карта сборки ЛА-12 (ГОСТ 3.1407-86)
Зависимости: pip install python-docx
"""

from docx import Document
from docx.shared import Pt, Mm, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

# ─────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────────

def set_cell_border(cell, **kwargs):
    """Устанавливает границы ячейки. kwargs: top, bottom, left, right."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        val = kwargs.get(side, 'single')
        el = OxmlElement(f'w:{side}')
        el.set(qn('w:val'), val)
        el.set(qn('w:sz'), '4')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), '000000')
        tcBorders.append(el)
    tcPr.append(tcBorders)

def set_cell_bg(cell, hex_color):
    """Закрашивает ячейку (заливка)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def cell_text(cell, text, bold=False, size=8, align=WD_ALIGN_PARAGRAPH.LEFT,
              valign=WD_ALIGN_VERTICAL.CENTER, color=None, italic=False):
    """Устанавливает текст и форматирование ячейки."""
    cell.vertical_alignment = valign
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = 'Times New Roman'
    if color:
        run.font.color.rgb = RGBColor(*bytes.fromhex(color))

def merge_row(table, row_idx, col_start, col_end):
    """Объединяет ячейки в строке."""
    row = table.rows[row_idx]
    row.cells[col_start].merge(row.cells[col_end])

def set_col_widths(table, widths_mm):
    """Задаёт ширину колонок в мм."""
    for i, col in enumerate(table.columns):
        col.width = Mm(widths_mm[i])

def add_thin_row(table, left_label, text, col_span_end=None):
    """Добавляет строку-переход (О/Т/Р)."""
    row = table.add_row()
    for cell in row.cells:
        set_cell_border(cell)
    row.height = Mm(7)
    cell_text(row.cells[0], left_label, bold=True, size=8,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    if col_span_end:
        row.cells[1].merge(row.cells[col_span_end])
    cell_text(row.cells[1], text, size=8)
    return row

# ─────────────────────────────────────────────
# ДАННЫЕ
# ─────────────────────────────────────────────

ORGANIZATION = 'ООО «Привод-Системс»'
PRODUCT      = 'Актуатор линейный ЛА-12'
DRAWING_NO   = 'ЛА-12-00.00.000СБ'
MATERIAL     = 'Смазка Литол-24 (ГОСТ 21150-87)'

# Структура операций: (номер, название, оборудование/место, разряд, Тпз, Тшт, [переходы])
# Переход: (тип='О'|'Т'|'Р', текст, время_мин)
OPERATIONS = [
    {
        'num': '005',
        'name': 'Монтаж и проверка печатной платы',
        'equip': 'Рабочее место монтажника РЭА',
        'tool': 'Паяльная станция 48 Вт, флюс ФТС, припой ПОС-61, тестер',
        'rank': 3,
        'tpz': 10.0,
        'tshtk': 72.6,
        'transitions': [
            ('О', 'Получить плату ЛА-12-00.00.0011 и комплект SMD-компонентов согласно схеме ЭЗ', 2.0),
            ('Т', 'Паяльная станция; пинцет антистатический; флюс ФТС; припой ПОС-61 Ø0,8', None),
            ('О', 'Нанести флюс на контактные площадки платы', 3.0),
            ('О', 'Установить и запаять SMD-резисторы R1–R8 (типоразмер 0805)', 8.0),
            ('О', 'Установить и запаять SMD-конденсаторы C1–C6', 6.0),
            ('О', 'Установить и запаять микросхему драйвера двигателя (SO-8)', 5.0),
            ('О', 'Установить и запаять разъём питания JST-2 и разъём управления JST-4', 4.0),
            ('О', 'Отмыть флюс изопропиловым спиртом, просушить 5 мин', 5.0),
            ('Р', 'Проверить тестером отсутствие короткого замыкания по цепям питания', 3.0),
            ('Р', 'Подать питание 12 В; измерить напряжение на выходах ±5%', 4.0),
            ('Р', 'Проверить ток холостого хода: не более 50 мА', 3.0),
            ('О', 'Промаркировать плату серийным номером; уложить в антистатический пакет', 2.0),
        ]
    },
    {
        'num': '010',
        'name': 'Входной контроль покупных изделий',
        'equip': 'Рабочее место контролёра ОТК',
        'tool': 'Штангенциркуль ШЦ-I-150-0,05, микрометр МК 25-2, динамометр ДПУ-0,01',
        'rank': 2,
        'tpz': 5.0,
        'tshtk': 13.2,
        'transitions': [
            ('О', 'Получить партию по маршрутному листу; проверить комплектность по спецификации ЛА-12-00.00.000', 2.0),
            ('Р', 'Подшипник ISK 6300ZZ: проверить маркировку, лёгкость вращения, отсутствие люфта', 1.0),
            ('Р', 'Двигатель DM4030: проверить маркировку, напряжение питания, сопротивление обмоток', 2.0),
            ('Р', 'Корпус редуктора (отливка): осмотр поверхности, контроль посадочных диаметров штангенциркулем', 2.0),
            ('Р', 'Ходовой винт ЛА-12-00.00.004: контроль резьбы калибром, прямолинейность < 0,1/100 мм', 1.5),
            ('Р', 'Гайка ходовая ПТФЭ ЛА-12-00.00.002: контроль резьбы, размеров; Ra ≤ 1,6 мкм', 1.5),
            ('О', 'Составить акт входного контроля; маркировать партию «ВК ПРИНЯТ»', 1.5),
            ('О', 'Передать принятые комплектующие на склад промежуточного хранения', 1.7),
        ]
    },
    {
        'num': '015',
        'name': 'Общая сборка актуатора',
        'equip': 'Сборочный стенд СС-01, верстак слесарный',
        'tool': 'Ключ динамометрический 2–25 Н·м; отвёртка Torx T10; пресс ручной настольный ПН-1; смазка Литол-24',
        'rank': 4,
        'tpz': 15.0,
        'tshtk': 153.6,
        'transitions': [
            ('О', 'Запрессовать подшипник ISK 6300ZZ в посадочное гнездо корпуса редуктора; усилие запрессовки 0,5–1,0 кН', 5.0),
            ('О', 'Установить ходовой винт ЛА-12-00.00.004 в подшипник; зафиксировать стопорным кольцом', 4.0),
            ('О', 'Навернуть гайку ходовую ПТФЭ ЛА-12-00.00.002 на винт; момент затяжки 0,8 Н·м', 3.0),
            ('Т', 'Ключ динамометрический 0,5–5 Н·м; отвёртка шлицевая 5 мм', None),
            ('О', 'Смазать резьбу ходового винта смазкой Литол-24 (слой 0,2–0,3 мм)', 2.0),
            ('О', 'Установить шайбу ЛА-12-00.00.003 и накладки ЛА-12-00.00.005/006 на корпус; закрепить 4 винтами М2,5×30 (ГОСТ 10621-80). Момент 0,4 Н·м', 8.0),
            ('О', 'Установить редуктор ЛА-12-00.00.007 на вал двигателя; зафиксировать осью Ø6×40 (ГОСТ 10621-80)', 6.0),
            ('О', 'Установить двигатель DM4030 в корпус редуктора; закрепить 2 винтами М6×50 (ГОСТ 17473). Момент 4,0 Н·м', 7.0),
            ('О', 'Установить втулку ЛА-12-00.00.008 и алюминиевый профиль L=120 мм (ЛА-12-00.00.0012); закрепить', 6.0),
            ('О', 'Установить наконечник ЛА-12-01.00.000 на шток; закрепить гайкой М6 самоконтрящейся (ГОСТ 50273). Момент 6,0 Н·м', 5.0),
            ('О', 'Установить хвостовик ЛА-12-00.00.0010; зашплинтовать (шплинт 2,5×25, ГОСТ 397-79)', 5.0),
            ('О', 'Установить кольцо уплотнительное; собрать наружный корпус 180924-0 со штекерами 42460-2', 7.0),
            ('О', 'Подключить плату ЛА-12-00.00.0011 к двигателю и разъёму наружного корпуса; уложить провод ПВС 2×0,75 L=0,35 м', 5.0),
            ('О', 'Установить шайбы 8.01.08кп.019 (2 шт.) под крепёжные узлы; проверить отсутствие перекосов', 4.0),
            ('Р', 'Проверить плавность хода штока по всей длине рабочего хода; усилие от руки не более 5 Н', 3.0),
            ('Р', 'Проверить момент затяжки резьбовых соединений согласно таблице моментов', 4.0),
            ('О', 'Нанести финальную смазку; закрыть корпус; затянуть крышку', 4.0),
            ('Р', 'Визуальный контроль: отсутствие зазоров, люфтов, механических повреждений; комплектность', 3.0),
            ('О', 'Сделать отметку в маршрутном листе «Сборка завершена»', 1.0),
        ]
    },
    {
        'num': '020',
        'name': 'Испытания и обкатка',
        'equip': 'Испытательный стенд ИС-ЛА-12',
        'tool': 'Блок питания лабораторный 0–100 В / 5 А; мультиметр Fluke 87; динамометр ДПУ-0,01-2',
        'rank': 3,
        'tpz': 10.0,
        'tshtk': 81.0,
        'transitions': [
            ('О', 'Установить актуатор на стенд; подключить к блоку питания соответствующего исполнения (12/48/96 В)', 3.0),
            ('О', 'Обкатка: 10 полных циклов выдвижения/втягивания без нагрузки; контроль плавности', 15.0),
            ('Р', 'Измерить ток потребления на холостом ходу: ≤ 0,8 А (12 В) / ≤ 0,3 А (48 В) / ≤ 0,15 А (96 В)', 3.0),
            ('О', 'Испытание под нагрузкой 500 Н: 5 полных циклов; контроль хода, скорости, нагрева', 15.0),
            ('О', 'Испытание под максимальной нагрузкой 2000 Н: 3 цикла; контроль целостности', 10.0),
            ('Р', 'Измерить скорость штока при номинальной нагрузке 500 Н: не менее указанной в ТУ ±10%', 5.0),
            ('Р', 'Проверить концевые выключатели / защиту по току в крайних положениях', 5.0),
            ('Р', 'Проверить нагрев двигателя и редуктора после 5 циклов под нагрузкой: ΔT ≤ 40°C', 5.0),
            ('Р', 'Измерить напряжение питания на разъёме под нагрузкой: просадка ≤ 5%', 3.0),
            ('О', 'Охладить изделие до комнатной температуры (≥ 15 мин)', 15.0),
            ('О', 'Занести результаты испытаний в паспорт изделия; поставить штамп ОТК', 2.0),
        ]
    },
    {
        'num': '025',
        'name': 'Маркировка и упаковка',
        'equip': 'Рабочее место упаковщика',
        'tool': 'Принтер этикеток; термоусадочная плёнка; антистатический пакет; картонный короб',
        'rank': 2,
        'tpz': 5.0,
        'tshtk': 32.4,
        'transitions': [
            ('О', 'Нанести этикетку с обозначением ЛА-12-00.00.000-0Х, серийным номером, датой изготовления', 3.0),
            ('О', 'Нанести этикетку с электрическими параметрами (Uном, Imax, усилие, ход)', 2.0),
            ('О', 'Обернуть актуатор защитной плёнкой VCI; запаять антистатический пакет', 4.0),
            ('О', 'Вложить в короб: актуатор в пакете, паспорт/инструкция, монтажный комплект (при наличии)', 3.0),
            ('О', 'Нанести на короб транспортную маркировку: «Хрупкое», «Беречь от влаги», ориентация', 2.0),
            ('Р', 'Контроль комплектности: актуатор + паспорт + этикетка; соответствие исполнения заказу', 2.0),
            ('О', 'Взвесить упакованное изделие; указать вес на коробе', 1.5),
            ('О', 'Передать на склад готовой продукции с сопроводительной документацией', 2.0),
            ('О', 'Закрыть маршрутный лист; передать в архив производства', 1.5),
        ]
    },
]

# Нормо-часовые ставки
RATES = {2: 380, 3: 450, 4: 550}  # руб/час

# ─────────────────────────────────────────────
# ПОСТРОЕНИЕ ДОКУМЕНТА
# ─────────────────────────────────────────────

doc = Document()

# Поля страницы
section = doc.sections[0]
section.page_width  = Mm(297)
section.page_height = Mm(210)
section.orientation = 1          # альбомная
section.left_margin   = Mm(20)
section.right_margin  = Mm(5)
section.top_margin    = Mm(10)
section.bottom_margin = Mm(10)

# Стиль по умолчанию
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(8)

# ────── ТИТУЛЬНЫЙ БЛОК ──────
def add_title_block(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('ОПЕРАЦИОННАЯ КАРТА СБОРКИ')
    r.bold = True
    r.font.size = Pt(12)
    r.font.name = 'Times New Roman'

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run('ГОСТ 3.1407-86  |  Форма 1')
    r2.font.size = Pt(9)
    r2.font.name = 'Times New Roman'
    r2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    doc.add_paragraph()

    # Шапка с реквизитами (таблица 6 столбцов)
    hdr = doc.add_table(rows=2, cols=6)
    hdr.style = 'Table Grid'
    widths = [50, 60, 40, 40, 40, 30]
    for i, col in enumerate(hdr.columns):
        col.width = Mm(widths[i])

    labels = ['Организация', 'Изделие', 'Обозначение', 'Материал / Смазка', 'Дата', 'Лист']
    values = [ORGANIZATION, PRODUCT, DRAWING_NO, MATERIAL, '23.04.2026', '1 / 1']

    for i, (lbl, val) in enumerate(zip(labels, values)):
        cell_text(hdr.cell(0, i), lbl, bold=True, size=7,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_bg(hdr.cell(0, i), 'D9E1F2')
        cell_text(hdr.cell(1, i), val, size=8,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
    for row in hdr.rows:
        row.height = Mm(7)
    doc.add_paragraph()

add_title_block(doc)

# ────── ФУНКЦИЯ ОДНОЙ ОПЕРАЦИИ ──────

def add_operation(doc, op):
    num     = op['num']
    name    = op['name']
    equip   = op['equip']
    tool    = op['tool']
    rank    = op['rank']
    tpz     = op['tpz']
    tshtk   = op['tshtk']
    trans   = op['transitions']

    rate    = RATES[rank]
    t_work  = sum(t for _, _, t in trans if t)
    salary  = round(tshtk / 60 * rate, 2)

    # ── Заголовок операции ──
    # Таблица: [Сл.сим+№оп] [Код+Наименование] [Оборуд.] [Разряд] [Тпз] [Тшт-к]
    COL_W = [15, 95, 75, 15, 18, 18]   # мм, итого ~236 мм

    tbl = doc.add_table(rows=1, cols=6)
    tbl.style = 'Table Grid'
    for i, w in enumerate(COL_W):
        tbl.columns[i].width = Mm(w)

    hdr_row = tbl.rows[0]
    hdr_row.height = Mm(7)
    for cell in hdr_row.cells:
        set_cell_bg(cell, 'BDD7EE')

    heads = ['—', f'Операция {num}  {name}', equip, 'Разр.', 'Тпз, мин', 'Тшт-к, мин']
    aligns = [WD_ALIGN_PARAGRAPH.CENTER] * 6
    bolds = [True, True, False, True, True, True]
    for i, (h, al, bo) in enumerate(zip(heads, aligns, bolds)):
        cell_text(hdr_row.cells[i], h, bold=bo, size=8, align=al)

    # Строка значений шапки
    val_row = tbl.add_row()
    val_row.height = Mm(7)
    vals = ['А', f'Оборудование: {equip}', f'Инструмент/приспособления: {tool}',
            str(rank), str(tpz), str(tshtk)]
    val_aligns = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT,
                  WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER,
                  WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER]
    for i, (v, al) in enumerate(zip(vals, val_aligns)):
        cell_text(val_row.cells[i], v, size=8, align=al)

    # ── Переходы ──
    for idx, (sym, text, t_val) in enumerate(trans, start=1):
        row = tbl.add_row()
        row.height = Mm(6)

        # Кол.1 — служебный символ + номер перехода
        label = f'{sym}{idx:02d}'
        cell_text(row.cells[0], label, bold=True, size=8,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

        # Кол.2–3 — текст перехода (объединяем под описание)
        row.cells[1].merge(row.cells[2])
        cell_text(row.cells[1], text, size=8)

        # Кол.4 — для Т-строк пишем «Т», иначе номер
        if sym == 'Т':
            cell_text(row.cells[3], 'Т', bold=True, size=8,
                      align=WD_ALIGN_PARAGRAPH.CENTER,
                      color='0070C0')
        else:
            cell_text(row.cells[3], str(idx), size=8,
                      align=WD_ALIGN_PARAGRAPH.CENTER)

        # Кол.5 — время перехода
        cell_text(row.cells[4], f'{t_val:.1f}' if t_val else '—', size=8,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

        # Кол.6 — нарастающее суммарное время (только для О/Р)
        if sym in ('О', 'Р') and t_val:
            running = sum(tt for _, _, tt in trans[:idx] if tt)
            cell_text(row.cells[5], f'{running:.1f}', size=8,
                      align=WD_ALIGN_PARAGRAPH.CENTER)
        else:
            cell_text(row.cells[5], '', size=8)

    # ── Итоговая строка ──
    sum_row = tbl.add_row()
    sum_row.height = Mm(7)
    for cell in sum_row.cells:
        set_cell_bg(cell, 'E2EFDA')
    sum_row.cells[0].merge(sum_row.cells[2])
    cell_text(sum_row.cells[0],
              f'Итого по операции {num}:  Тшт-к = {tshtk} мин  |  '
              f'ЗП = {salary:.2f} руб  |  Разряд {rank}',
              bold=True, size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
    cell_text(sum_row.cells[3], str(rank), bold=True, size=8,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_text(sum_row.cells[4], str(tpz), bold=True, size=8,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_text(sum_row.cells[5], str(tshtk), bold=True, size=8,
              align=WD_ALIGN_PARAGRAPH.CENTER)

    # Разрыв между операциями
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)

# Добавляем все операции
for op in OPERATIONS:
    add_operation(doc, op)

# ─────────────────────────────────────────────
# СВОДНАЯ ЭКОНОМИЧЕСКАЯ ТАБЛИЦА
# ─────────────────────────────────────────────

def add_economics(doc):
    p = doc.add_paragraph()
    r = p.add_run('СВОДНАЯ ТАБЛИЦА ТРУДОЗАТРАТ И ЭКОНОМИКИ')
    r.bold = True
    r.font.size = Pt(10)
    r.font.name = 'Times New Roman'
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    tbl = doc.add_table(rows=1, cols=7)
    tbl.style = 'Table Grid'
    col_ws = [12, 60, 20, 15, 18, 20, 25]
    for i, w in enumerate(col_ws):
        tbl.columns[i].width = Mm(w)

    # Шапка
    hdr = tbl.rows[0]
    hdr.height = Mm(8)
    for cell in hdr.cells:
        set_cell_bg(cell, 'D9E1F2')
    heads = ['№ оп.', 'Наименование операции', 'Разряд', 'Тпз, мин',
             'Тшт-к, мин', 'н/ч', 'ЗП, руб']
    for i, h in enumerate(heads):
        cell_text(hdr.cells[i], h, bold=True, size=8,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

    total_tpz = total_tshtk = total_zp = 0.0

    for op in OPERATIONS:
        rate  = RATES[op['rank']]
        zp    = round(op['tshtk'] / 60 * rate, 2)
        nh    = round(op['tshtk'] / 60, 2)
        total_tpz   += op['tpz']
        total_tshtk += op['tshtk']
        total_zp    += zp

        row = tbl.add_row()
        row.height = Mm(7)
        vals = [op['num'], op['name'], str(op['rank']),
                str(op['tpz']), str(op['tshtk']), str(nh), f'{zp:.2f}']
        aligns = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT,
                  WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER,
                  WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.CENTER,
                  WD_ALIGN_PARAGRAPH.CENTER]
        for i, (v, al) in enumerate(zip(vals, aligns)):
            cell_text(row.cells[i], v, size=8, align=al)

    # Итоговая строка
    tot_row = tbl.add_row()
    tot_row.height = Mm(8)
    for cell in tot_row.cells:
        set_cell_bg(cell, 'E2EFDA')
    tot_row.cells[0].merge(tot_row.cells[1])
    cell_text(tot_row.cells[0], 'ИТОГО на 1 изделие', bold=True, size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    tot_vals = ['', '', str(total_tpz), str(total_tshtk),
                str(round(total_tshtk / 60, 2)), f'{total_zp:.2f}']
    for i, v in enumerate(tot_vals):
        if i == 0:
            continue
        cell_text(tot_row.cells[i + 1], v, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

    # Примечание
    doc.add_paragraph()
    note = doc.add_paragraph()
    note.add_run(
        f'Примечание: ЗП рассчитана по тарифным ставкам: '
        f'2 разряд — {RATES[2]} руб/ч; '
        f'3 разряд — {RATES[3]} руб/ч; '
        f'4 разряд — {RATES[4]} руб/ч. '
        f'Тпз — подготовительно-заключительное время. '
        f'Тшт-к — штучно-калькуляционное время. '
        f'н/ч — нормо-часы.'
    ).font.size = Pt(7)

add_economics(doc)

# ─────────────────────────────────────────────
# СОХРАНЕНИЕ
# ─────────────────────────────────────────────

OUTPUT = 'ОК_ЛА-12_сборка.docx'
doc.save(OUTPUT)
print(f'✅  Файл сохранён: {OUTPUT}')