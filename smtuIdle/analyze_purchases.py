import pandas as pd
import sqlite3
from sqlalchemy import create_engine, text
import re
from datetime import datetime
import json

# ── МЕНЯЕМ DSN ──────────────────────────────────────────────────────────────
DB_PATH = "database.db"            # путь к вашей базе
DB_DSN  = f"sqlite:///{DB_PATH}"
_DATE_EXPR = (
    "date("
    "substr(published,7,4)||'-'||substr(published,4,2)||'-'||substr(published,1,2)"
    ")"
)
def _parse_json_cols(df, *cols):
    """Десериализует JSON-строки в dict/list для указанных колонок."""
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.strip().startswith(('{', '[')) else x
            )
    return df
def get_engine():
    return create_engine(DB_DSN)

def clean_price_value(value):
    """Преобразует строковую цену (например '499 678,00') в float"""
    if pd.isna(value):
        return None
    try:
        # Убираем пробелы и меняем запятую на точку
        clean_str = str(value).replace(' ', '').replace(',', '.')
        # Убираем символ рубля если он есть
        clean_str = clean_str.replace('₽', '')
        return float(clean_str)
    except (ValueError, TypeError):
        return None


def categorize_price(price):
    """Категоризация цены"""
    if pd.isna(price):
        return 'Нет цены'

    p = price

    if p < 400_000:
        return 'до 400 тыс.'
    elif 400_000 <= p < 1_000_000:
        return '400 тыс. — 1 млн'
    elif 1_000_000 <= p < 5_000_000:
        return '1 — 5 млн'
    elif 5_000_000 <= p < 20_000_000:
        return '5 — 20 млн'
    elif 20_000_000 <= p < 100_000_000:
        return '20 — 100 млн'
    elif 100_000_000 <= p < 1_000_000_000:
        return '100 млн — 1 млрд'
    else:
        return 'более 1 млрд'


def print_summary(df, column_name, title, limit=None):
    """Вывод сводной таблицы"""
    print(f"\n{'=' * 60}")
    print(f"СВОДНАЯ ТАБЛИЦА: {title}")
    print(f"{'=' * 60}")

    if df is None or df.empty:
        print("Нет данных для анализа")
        return

    counts = df[column_name].value_counts()
    items_to_show = counts.head(limit) if limit else counts

    for category, count in items_to_show.items():
        clean_name = str(category).strip()
        short_name = (clean_name[:50] + '...') if len(clean_name) > 50 else clean_name
        print(f"{short_name:<50} {count:>8}")

    print(f"{'-' * 60}")
    if limit and len(counts) > limit:
        print(f"{f'... и еще {len(counts) - limit} строк ...':<50}")
    print(f"{'ИТОГО записей':<50} {len(df):>8}")


def extract_purchase_items(json_data):
    """
    Извлекает code, cost и quantity из common_info_json
    """
    if not isinstance(json_data, dict):
        return []

    extracted_items = []

    try:
        info_section = json_data.get('информация_об_объекте_закупки', {})
        items = info_section.get('items', [])

        for item in items:
            if item.get('kind') == 'table':
                table = item.get('table', {})
                rows = table.get('rows', [])

                for row in rows:
                    code = row.get('КОД ПОЗИЦИИ')
                    cost = row.get('СТОИМОСТЬ, ₽')
                    qty = row.get('КОЛИЧЕСТВО (ОБЪЕМ РАБОТЫ, УСЛУГИ)')

                    # Пропускаем пустые или технические строки (где нет кода или он "1" и нет цены)
                    # В примере есть строки {"КОД ПОЗИЦИИ": "1", "СТОИМОСТЬ, ₽": null} - их игнорируем
                    if code and cost:
                        extracted_items.append({
                            'code': code,
                            'cost_raw': cost,
                            'qty_raw': qty
                        })
    except Exception:
        pass

    return extracted_items


def clean_quantity_value(value):
    """Преобразует строку количества '1,00' или '10' в float"""
    if pd.isna(value):
        return None
    try:
        # Убираем пробелы и меняем запятую на точку
        clean_str = str(value).replace(' ', '').replace(',', '.')
        return float(clean_str)
    except (ValueError, TypeError):
        return None
# --- Блок анализа закупок ---



def print_law_table(df, law_name, table_number):
    """Вспомогательная функция для печати таблицы по конкретному закону"""
    print(f"\n{'=' * 90}")
    print(f"Таблица {table_number}. Данные о значениях НМЦК закупок по {law_name} в 2025 году")
    print(f"{'=' * 90}")

    # Фильтруем данные по закону
    law_df = df[df['law'] == law_name].copy()

    if law_df.empty:
        print(f"Нет данных по {law_name}")
        return

    # Группировка
    grouped = law_df.groupby('category')['price'].agg(['count', 'sum', 'mean'])

    # Формируем итоговый DataFrame
    # Колонки: ед. | сумма НМЦК | средняя НМЦК
    result = pd.DataFrame()
    result['ед.'] = grouped['count'].astype(int)
    result['сумма НМЦК, руб.'] = grouped['sum']
    result['средняя НМЦК, руб.'] = grouped['mean']

    # Считаем "Итого"
    total_row = pd.Series({
        'ед.': int(law_df['price'].count()),
        'сумма НМЦК, руб.': law_df['price'].sum(),
        'средняя НМЦК, руб.': law_df['price'].mean()
    }, name='Итого')

    result = pd.concat([result, total_row.to_frame().T])

    # Форматирование
    def format_val(x):
        if pd.isna(x): return "-"
        if isinstance(x, (int, float)):
            if x == 0: return "0"
            if x % 1 == 0:  # Целые числа
                return "{:,.0f}".format(x).replace(',', ' ')
            return "{:,.2f}".format(x).replace(',', ' ')  # Деньги
        return x

    # Применяем форматирование ко всем ячейкам
    for col in result.columns:
        result[col] = result[col].apply(format_val)

    # Убираем префикс "1. ", "2. " из названий категорий для красоты
    result.index = [idx[3:] if idx[0].isdigit() else idx for idx in result.index]

    print(result.to_string(justify='right'))
    print(f"{'-' * 90}")


def analyze_purchase(engine):
    query = f"""
    SELECT 
        reg_number, object_name, law, status, placing_way,
        customer_name, initial_price_amount,
        common_info_json, lots_json, published
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND {_DATE_EXPR} <= '2025-12-31'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    """
    try:
        print("\n>>> Загрузка данных закупок (с 2018 по 2025, от 100 млн)...")
        df = pd.read_sql_query(query, engine)
        df = _parse_json_cols(df, 'common_info_json', 'lots_json')
        print(f"✓ Загружено {len(df)} закупок")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    if df.empty:
        print("Нет данных.")
        return


    # ПОДГОТОВКА ДАННЫХ
    df['price'] = pd.to_numeric(df['initial_price_amount'], errors='coerce').fillna(0)
    df['category'] = df['price'].apply(categorize_price)

    # Обработка даты для получения года
    df['published_dt'] = pd.to_datetime(df['published'], format='%d.%m.%Y', errors='coerce')
    df['year'] = df['published_dt'].dt.year

    df['price_category_simple'] = df['price'].apply(categorize_price)

    # Функция для приведения названий способов к единому виду
    def map_placing_way(way):
        if pd.isna(way):
            return 'Прочие'
        w = str(way).strip().lower()
        if 'электронный аукцион' in w:
            return 'Электронный аукцион'
        elif 'открытый конкурс' in w:
            return 'Открытый конкурс в электронной форме'
        elif 'единственного поставщика' in w or 'единственным поставщиком' in w:
            return 'Закупка у единственного поставщика'
        else:
            return 'Прочие'

    # ← ВОТ ЭТИ ДВЕ СТРОКИ НУЖНО ДОБАВИТЬ СРАЗУ ЗДЕСЬ, ДО ВСЕХ ТАБЛИЦ
    df['placing_way_cat'] = df['placing_way'].apply(map_placing_way)
    df_period = df[(df['year'] >= 2018) & (df['year'] <= 2025)]

    # -------------------------------------------------------------------------
    # 1. СТАНДАРТНЫЕ СВОДНЫЕ
    # -------------------------------------------------------------------------
    print_summary(df, 'law', 'ЗАКУПКИ: ЗАКОНЫ')
    print_summary(df, 'status', 'ЗАКУПКИ: СТАТУС таблица 8')
    print_summary(df, 'customer_name', 'ЗАКУПКИ: ЗАКАЗЧИКИ (ТОП ПО БЮДЖЕТУ)', limit=20)

    price_order_simple = ['до 400 тыс.', '400 тыс. — 1 млн', '1 — 5 млн', '5 — 20 млн',
                          '20 — 100 млн', '100 млн — 1 млрд', 'более 1 млрд', 'Нет цены']
    df['price_category_simple'] = pd.Categorical(df['price_category_simple'], categories=price_order_simple,
                                                 ordered=True)
    print_summary(df.sort_values('price_category_simple'), 'price_category_simple', 'ЗАКУПКИ: БЮДЖЕТ (НМЦК)')

    # -------------------------------------------------------------------------
    # 2. ТАБЛИЦА 2: ДИАПАЗОНЫ ЦЕН (НМЦК × ЗАКОН)
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 80}")
    print("Таблица 2. Распределение по диапазонам НМЦК (кол-во)")
    print(f"{'=' * 80}")

    price_order_custom = [
        'до 400 тыс.', '400 тыс. — 1 млн', '1 — 5 млн',
        '5 — 20 млн', '20 — 100 млн', '100 млн — 1 млрд',
        'более 1 млрд'
    ]
    df['price_category_tab2'] = df['price'].apply(categorize_price)
    df['price_category_tab2'] = pd.Categorical(df['price_category_tab2'], categories=price_order_custom, ordered=True)

    pivot_ranges = pd.crosstab(df['price_category_tab2'], df['law']).reindex(price_order_custom)
    pivot_ranges['Общий итог'] = pivot_ranges.sum(axis=1)
    total_row_ranges = pivot_ranges.sum(axis=0)
    total_row_ranges.name = 'Всего закупок'
    pivot_ranges = pd.concat([pivot_ranges, total_row_ranges.to_frame().T])
    print(pivot_ranges)

    # -------------------------------------------------------------------------
    # ТАБЛИЦА 3 "Способ определения поставщика × Закон" - С СУММОЙ
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 120}")
    print("Таблица 3. Закупки по способу определения поставщика с учетом закона (кол-во и сумма)")
    print(f"{'=' * 120}")

    grouped_way_law = df_period.groupby(['placing_way_cat', 'law'])['price'].agg(['count', 'sum'])
    pivot_way_count = grouped_way_law['count'].unstack(fill_value=0)
    pivot_way_sum = grouped_way_law['sum'].unstack(fill_value=0)

    # Гарантируем наличие колонок
    for law_col in ['44-ФЗ', '223-ФЗ']:
        if law_col not in pivot_way_count.columns:
            pivot_way_count[law_col] = 0
        if law_col not in pivot_way_sum.columns:
            pivot_way_sum[law_col] = 0

    pivot_way_count = pivot_way_count[['44-ФЗ', '223-ФЗ']]
    pivot_way_sum = pivot_way_sum[['44-ФЗ', '223-ФЗ']]

    # Порядок строк
    order_way = [
        'Электронный аукцион',
        'Открытый конкурс в электронной форме',
        'Закупка у единственного поставщика',
        'Прочие'
    ]
    pivot_way_count = pivot_way_count.reindex(order_way).fillna(0).astype(int)
    pivot_way_sum = pivot_way_sum.reindex(order_way).fillna(0)

    # Итоговые колонки
    pivot_way_count['Всего'] = pivot_way_count.sum(axis=1)
    pivot_way_sum['Всего'] = pivot_way_sum.sum(axis=1)

    # Итоговая строка
    pivot_way_count.loc['Общий итог'] = pivot_way_count.sum()
    pivot_way_sum.loc['Общий итог'] = pivot_way_sum.sum()

    print(f"{'Способ определения поставщика':<45} {'Показатель':<15} {'44-ФЗ':>15} {'223-ФЗ':>15} {'Всего':>15}")
    print("-" * 120)

    for way in list(order_way) + ['Общий итог']:
        # Количество
        count_44 = int(pivot_way_count.loc[way, '44-ФЗ'])
        count_223 = int(pivot_way_count.loc[way, '223-ФЗ'])
        count_total = int(pivot_way_count.loc[way, 'Всего'])

        count_44_str = str(count_44) if count_44 > 0 else '-'
        count_223_str = str(count_223) if count_223 > 0 else '-'
        count_total_str = str(count_total) if count_total > 0 else '-'

        print(f"{way:<45} {'кол-во':<15} {count_44_str:>15} {count_223_str:>15} {count_total_str:>15}")

        # Сумма
        sum_44 = pivot_way_sum.loc[way, '44-ФЗ']
        sum_223 = pivot_way_sum.loc[way, '223-ФЗ']
        sum_total = pivot_way_sum.loc[way, 'Всего']

        sum_44_fmt = "{:,.0f}".format(sum_44).replace(',', ' ') if sum_44 > 0 else '-'
        sum_223_fmt = "{:,.0f}".format(sum_223).replace(',', ' ') if sum_223 > 0 else '-'
        sum_total_fmt = "{:,.0f}".format(sum_total).replace(',', ' ') if sum_total > 0 else '-'

        print(f"{'':45} {'сумма, руб':<15} {sum_44_fmt:>15} {sum_223_fmt:>15} {sum_total_fmt:>15}")

    print("-" * 120)

    # -------------------------------------------------------------------------
    # 4. ТАБЛИЦА 4: СЛОЖНЫЕ ДИАПАЗОНЫ (ед. и сумма)
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 90}")
    print("Таблица 4. Диапазоны НМЦК (ед. и сумма) по законам")
    print(f"{'=' * 90}")

    grouped = df.groupby(['category', 'law'])['price'].agg(['count', 'sum'])
    unstacked = grouped.unstack(fill_value=0)

    for metric in ['count', 'sum']:
        for law in ['44-ФЗ', '223-ФЗ']:
            if (metric, law) not in unstacked.columns: unstacked[(metric, law)] = 0

    unstacked[('count', 'Общий итог')] = unstacked[('count', '44-ФЗ')] + unstacked[('count', '223-ФЗ')]
    unstacked[('sum', 'Общий итог')] = unstacked[('sum', '44-ФЗ')] + unstacked[('sum', '223-ФЗ')]

    final_rows = []
    categories = sorted(df['category'].unique())
    for cat in categories:
        if cat == 'Без цены': continue
        row_data = unstacked.loc[cat]

        final_rows.append({
            'Диапазон': f"{cat[3:]}, ед.",
            '44-ФЗ': int(row_data[('count', '44-ФЗ')]),
            '223-ФЗ': int(row_data[('count', '223-ФЗ')]),
            'Общий итог': int(row_data[('count', 'Общий итог')])
        })
        final_rows.append({
            'Диапазон': "сумма НМЦК, руб.",
            '44-ФЗ': row_data[('sum', '44-ФЗ')],
            '223-ФЗ': row_data[('sum', '223-ФЗ')],
            'Общий итог': row_data[('sum', 'Общий итог')]
        })

    final_df4 = pd.DataFrame(final_rows)

    def format_val(x):
        if x == 0: return "-"
        if isinstance(x, (int, float)):
            if x % 1 == 0: return "{:,.0f}".format(x).replace(',', ' ')
            return "{:,.2f}".format(x).replace(',', ' ')
        return x

    for c in ['44-ФЗ', '223-ФЗ', 'Общий итог']:
        final_df4[c] = final_df4[c].apply(format_val)
    print(final_df4.to_string(index=False, justify='right'))

    # -------------------------------------------------------------------------
    # 5. ТАБЛИЦЫ 5 и 6: ДЕТАЛЬНО ПО ЗАКОНАМ (предполагается, что функции есть)
    # -------------------------------------------------------------------------
    # print_law_table(df, '44-ФЗ', 5)
    # print_law_table(df, '223-ФЗ', 6)

    # -------------------------------------------------------------------------
    # 6. ТАБЛИЦА 7: СТАТУСЫ - С СУММОЙ
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 120}")
    print("Таблица 7. Статус закупок в целом по 44-ФЗ и 223-ФЗ (кол-во и сумма)")
    print(f"{'=' * 120}")

    grouped_status = df.groupby(['status', 'law'])['price'].agg(['count', 'sum'])
    pivot_status_count = grouped_status['count'].unstack(fill_value=0)
    pivot_status_sum = grouped_status['sum'].unstack(fill_value=0)

    # Итоговые колонки
    pivot_status_count['Общий итог'] = pivot_status_count.sum(axis=1)
    pivot_status_sum['Общий итог'] = pivot_status_sum.sum(axis=1)

    # Сортируем по сумме
    pivot_status_count = pivot_status_count.sort_values('Общий итог', ascending=False)
    pivot_status_sum = pivot_status_sum.loc[pivot_status_count.index]

    print(f"{'Статус':<40} {'Показатель':<15} {'44-ФЗ':>20} {'223-ФЗ':>20} {'Общий итог':>20}")
    print("-" * 120)

    for status in pivot_status_count.index:
        # Количество
        count_44 = int(pivot_status_count.loc[status, '44-ФЗ']) if '44-ФЗ' in pivot_status_count.columns else 0
        count_223 = int(pivot_status_count.loc[status, '223-ФЗ']) if '223-ФЗ' in pivot_status_count.columns else 0
        count_total = int(pivot_status_count.loc[status, 'Общий итог'])

        count_44_str = str(count_44) if count_44 > 0 else '-'
        count_223_str = str(count_223) if count_223 > 0 else '-'

        print(f"{str(status):<40} {'кол-во':<15} {count_44_str:>20} {count_223_str:>20} {count_total:>20}")

        # Сумма
        sum_44 = pivot_status_sum.loc[status, '44-ФЗ'] if '44-ФЗ' in pivot_status_sum.columns else 0
        sum_223 = pivot_status_sum.loc[status, '223-ФЗ'] if '223-ФЗ' in pivot_status_sum.columns else 0
        sum_total = pivot_status_sum.loc[status, 'Общий итог']

        sum_44_fmt = "{:,.0f}".format(sum_44).replace(',', ' ') if sum_44 > 0 else '-'
        sum_223_fmt = "{:,.0f}".format(sum_223).replace(',', ' ') if sum_223 > 0 else '-'
        sum_total_fmt = "{:,.0f}".format(sum_total).replace(',', ' ') if sum_total > 0 else '-'

        print(f"{'':40} {'сумма, руб':<15} {sum_44_fmt:>20} {sum_223_fmt:>20} {sum_total_fmt:>20}")

    # Итог
    print("-" * 120)
    total_count_44 = int(pivot_status_count['44-ФЗ'].sum()) if '44-ФЗ' in pivot_status_count.columns else 0
    total_count_223 = int(pivot_status_count['223-ФЗ'].sum()) if '223-ФЗ' in pivot_status_count.columns else 0
    total_count_all = int(pivot_status_count['Общий итог'].sum())

    print(f"{'Общий итог':<40} {'кол-во':<15} {total_count_44:>20} {total_count_223:>20} {total_count_all:>20}")

    total_sum_44 = pivot_status_sum['44-ФЗ'].sum() if '44-ФЗ' in pivot_status_sum.columns else 0
    total_sum_223 = pivot_status_sum['223-ФЗ'].sum() if '223-ФЗ' in pivot_status_sum.columns else 0
    total_sum_all = pivot_status_sum['Общий итог'].sum()

    print(f"{'':40} {'сумма, руб':<15} {'{:,.0f}'.format(total_sum_44).replace(',', ' '):>20} "
          f"{'{:,.0f}'.format(total_sum_223).replace(',', ' '):>20} "
          f"{'{:,.0f}'.format(total_sum_all).replace(',', ' '):>20}")
    print("-" * 120)

    # -------------------------------------------------------------------------
    # 7. ТАБЛИЦА 9: СПОСОБЫ ОПРЕДЕЛЕНИЯ ПОСТАВЩИКА
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 90}")
    print("Таблица 9. Распределение закупок по способу определения поставщика (ед. и сумма)")
    print(f"{'=' * 90}")
    grouped = df.groupby(['placing_way', 'law'])['price'].agg(['count', 'sum'])
    unstacked = grouped.unstack(fill_value=0)

    for metric in ['count', 'sum']:
        for law in ['44-ФЗ', '223-ФЗ']:
            if (metric, law) not in unstacked.columns: unstacked[(metric, law)] = 0

    unstacked[('count', 'Общий итог')] = unstacked[('count', '44-ФЗ')] + unstacked[('count', '223-ФЗ')]
    unstacked[('sum', 'Общий итог')] = unstacked[('sum', '44-ФЗ')] + unstacked[('sum', '223-ФЗ')]

    sort_s = unstacked[('sum', 'Общий итог')]
    unstacked = unstacked.loc[sort_s.sort_values(ascending=False).index]

    final_rows9 = []

    total_count_44 = unstacked[('count', '44-ФЗ')].sum()
    total_count_223 = unstacked[('count', '223-ФЗ')].sum()
    total_count_all = unstacked[('count', 'Общий итог')].sum()
    total_sum_44 = unstacked[('sum', '44-ФЗ')].sum()
    total_sum_223 = unstacked[('sum', '223-ФЗ')].sum()
    total_sum_all = unstacked[('sum', 'Общий итог')].sum()

    for method in unstacked.index:
        row_data = unstacked.loc[method]
        final_rows9.append({
            'Способ': str(method)[:60],
            'Показатель': 'кол-во',
            '44-ФЗ': int(row_data[('count', '44-ФЗ')]),
            '223-ФЗ': int(row_data[('count', '223-ФЗ')]),
            'Общий итог': int(row_data[('count', 'Общий итог')])
        })
        final_rows9.append({
            'Способ': '',
            'Показатель': 'сумма',
            '44-ФЗ': row_data[('sum', '44-ФЗ')],
            '223-ФЗ': row_data[('sum', '223-ФЗ')],
            'Общий итог': row_data[('sum', 'Общий итог')]
        })

    final_rows9.append({'Способ': 'Общий итог', 'Показатель': 'кол-во',
                        '44-ФЗ': int(total_count_44), '223-ФЗ': int(total_count_223),
                        'Общий итог': int(total_count_all)})
    final_rows9.append({'Способ': '', 'Показатель': 'сумма',
                        '44-ФЗ': total_sum_44, '223-ФЗ': total_sum_223, 'Общий итог': total_sum_all})

    final_df9 = pd.DataFrame(final_rows9)
    for c in ['44-ФЗ', '223-ФЗ', 'Общий итог']:
        final_df9[c] = final_df9[c].apply(format_val)
    print(final_df9.to_string(index=False, justify='right'))

    # 2. ТАБЛИЦА 2: ДИАПАЗОНЫ ЦЕН (НМЦК × ЗАКОН) - С СУММОЙ
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 120}")
    print("Таблица 2. Распределение по диапазонам НМЦК (кол-во и сумма)")
    print(f"{'=' * 120}")

    price_order_custom = [
        'до 400 тыс.', '400 тыс. — 1 млн', '1 — 5 млн',
        '5 — 20 млн', '20 — 100 млн', '100 млн — 1 млрд',
        'более 1 млрд'
    ]
    df['price_category_tab2'] = df['price'].apply(categorize_price)
    df['price_category_tab2'] = pd.Categorical(df['price_category_tab2'], categories=price_order_custom, ordered=True)

    # Группируем по диапазону и закону, считаем количество и сумму
    grouped_tab2 = df.groupby(['price_category_tab2', 'law'])['price'].agg(['count', 'sum'])
    pivot_count = grouped_tab2['count'].unstack(fill_value=0).reindex(price_order_custom, fill_value=0)
    pivot_sum = grouped_tab2['sum'].unstack(fill_value=0).reindex(price_order_custom, fill_value=0)

    # Итоговые колонки
    pivot_count['Общий итог'] = pivot_count.sum(axis=1)
    pivot_sum['Общий итог'] = pivot_sum.sum(axis=1)

    # Формируем таблицу с чередованием строк (кол-во / сумма)
    print(f"{'Диапазон':<25} {'Показатель':<15} {'44-ФЗ':>20} {'223-ФЗ':>20} {'Общий итог':>20}")
    print("-" * 120)

    for cat in price_order_custom:
        # Строка с количеством
        count_44 = int(pivot_count.loc[cat, '44-ФЗ']) if '44-ФЗ' in pivot_count.columns else 0
        count_223 = int(pivot_count.loc[cat, '223-ФЗ']) if '223-ФЗ' in pivot_count.columns else 0
        count_total = int(pivot_count.loc[cat, 'Общий итог'])
        print(f"{cat:<25} {'кол-во':<15} {count_44:>20} {count_223:>20} {count_total:>20}")

        # Строка с суммой
        sum_44 = pivot_sum.loc[cat, '44-ФЗ'] if '44-ФЗ' in pivot_sum.columns else 0
        sum_223 = pivot_sum.loc[cat, '223-ФЗ'] if '223-ФЗ' in pivot_sum.columns else 0
        sum_total = pivot_sum.loc[cat, 'Общий итог']

        sum_44_fmt = "{:,.0f}".format(sum_44).replace(',', ' ') if sum_44 > 0 else '-'
        sum_223_fmt = "{:,.0f}".format(sum_223).replace(',', ' ') if sum_223 > 0 else '-'
        sum_total_fmt = "{:,.0f}".format(sum_total).replace(',', ' ') if sum_total > 0 else '-'

        print(f"{'':25} {'сумма, руб':<15} {sum_44_fmt:>20} {sum_223_fmt:>20} {sum_total_fmt:>20}")

    # Итоговая строка
    print("-" * 120)
    total_count_44 = int(pivot_count['44-ФЗ'].sum()) if '44-ФЗ' in pivot_count.columns else 0
    total_count_223 = int(pivot_count['223-ФЗ'].sum()) if '223-ФЗ' in pivot_count.columns else 0
    total_count_all = int(pivot_count['Общий итог'].sum())
    print(f"{'Всего закупок':<25} {'кол-во':<15} {total_count_44:>20} {total_count_223:>20} {total_count_all:>20}")

    total_sum_44 = pivot_sum['44-ФЗ'].sum() if '44-ФЗ' in pivot_sum.columns else 0
    total_sum_223 = pivot_sum['223-ФЗ'].sum() if '223-ФЗ' in pivot_sum.columns else 0
    total_sum_all = pivot_sum['Общий итог'].sum()

    print(f"{'':25} {'сумма, руб':<15} {'{:,.0f}'.format(total_sum_44).replace(',', ' '):>20} "
          f"{'{:,.0f}'.format(total_sum_223).replace(',', ' '):>20} "
          f"{'{:,.0f}'.format(total_sum_all).replace(',', ' '):>20}")
    print("-" * 120)

    # -------------------------------------------------------------------------
    # НОВОЕ: ТАБЛИЦА 3 "Способ определения поставщика × Закон"
    # -------------------------------------------------------------------------
    print(f"\n{'=' * 90}")
    print("Таблица 3. Количество закупок по способу определения поставщика с учетом закона")
    print(f"{'=' * 90}")

    # 1. Строим сводную таблицу (строки: Способ, столбцы: Закон)
    pivot_law = pd.crosstab(df_period['placing_way_cat'], df_period['law'])

    # Убеждаемся, что обе колонки существуют, даже если по одному из законов не было закупок
    for law_col in ['44-ФЗ', '223-ФЗ']:
        if law_col not in pivot_law.columns:
            pivot_law[law_col] = 0

    # Выбираем только нужные колонки в правильном порядке
    pivot_law = pivot_law[['44-ФЗ', '223-ФЗ']]

    # 2. Устанавливаем правильный порядок строк (Способов)
    order_way = [
        'Электронный аукцион',
        'Открытый конкурс в электронной форме',
        'Закупка у единственного поставщика',
        'Прочие'
    ]
    # Заполняем нулями способы, которых не было
    pivot_law = pivot_law.reindex(order_way).fillna(0).astype(int)

    # 3. Считаем ИТОГИ (строки и столбцы)
    pivot_law['Всего'] = pivot_law.sum(axis=1)  # Сумма по строкам
    pivot_law.loc['Общий итог'] = pivot_law.sum()  # Сумма по столбцам

    # 4. ИСПРАВЛЕНИЕ: Явно задаем имя индекса перед его сбросом
    pivot_law.index.name = 'Способ определения поставщика'
    pivot_law = pivot_law.reset_index()

    # 5. Функция форматирования вывода (заменяет 0 на '-')
    def format_zero_dash(val):
        if val == 0:
            return '-'
        return str(int(val))

    # Форматируем колонки с числами
    for col in ['44-ФЗ', '223-ФЗ', 'Всего']:
        pivot_law[col] = pivot_law[col].apply(format_zero_dash)

    # 6. Вывод таблицы в консоль
    print(f"{'Способ определения поставщика':<45} {'44-ФЗ':>10} {'223-ФЗ':>10} {'Всего':>10}")
    print("-" * 90)
    for _, row in pivot_law.iterrows():
        print(f"{row['Способ определения поставщика']:<45} {row['44-ФЗ']:>10} {row['223-ФЗ']:>10} {row['Всего']:>10}")
    print(f"{'-' * 90}")

    # -------------------------------------------------------------------------
    # 8. ГЛУБОКИЙ АНАЛИЗ JSON (ОКПД2/КТРУ) С ПРИВЯЗКОЙ К НОМЕРУ ЗАКУПКИ
    # -------------------------------------------------------------------------
    print("\n... Извлечение позиций из JSON (с привязкой к номеру закупки) ...")

    def extract_purchase_items_with_context(row):
        """
        Извлекает ОКПД2 из JSON, сохраняя привязку к реестровому номеру и объекту
        """
        law = str(row.get('law', ''))
        reg_number = str(row.get('reg_number', ''))
        # Обрезаем переносы строк для красивого вывода
        object_name = str(row.get('object_name', '')).replace('\n', ' ').strip()

        extracted_items = []

        # --- ЛОГИКА ДЛЯ 44-ФЗ ---
        if '44' in law:
            json_data = row.get('common_info_json')
            if isinstance(json_data, dict):
                try:
                    info_section = json_data.get('информация_об_объекте_закупки', {})
                    for item in info_section.get('items', []):
                        if item.get('kind') == 'table':
                            for r in item.get('table', {}).get('rows', []):
                                code = r.get('КОД ПОЗИЦИИ')
                                # Проверяем, что код есть и это не мусорная единица '1'
                                if code and str(code).strip() not in ['', '1']:
                                    extracted_items.append({'code': clean_okpd2(code)})
                except Exception:
                    pass

        # --- ЛОГИКА ДЛЯ 223-ФЗ ---
        elif '223' in law:
            json_data = row.get('lots_json')
            if isinstance(json_data, dict):
                try:
                    for key, section in json_data.items():
                        if isinstance(section, dict):
                            for item in section.get('items', []):
                                parsed = item.get('parsed_table', {})
                                for r in parsed.get('rows', []):
                                    okpd_raw = r.get('КЛАССИФИКАЦИЯ ПО ОКПД2')
                                    if okpd_raw:
                                        extracted_items.append({'code': clean_okpd2(okpd_raw)})
                except Exception:
                    pass

        # Если скрипт прошел по JSON, но не нашел ни одного ОКПД2
        if not extracted_items:
            extracted_items.append({'code': 'Нет ОКПД2'})

        # Обогащаем каждый найденный код (или отметку 'Нет ОКПД2') данными о закупке
        for item in extracted_items:
            item['reg_number'] = reg_number
            item['object_name'] = object_name
            item['law'] = law

        return extracted_items

    # Применяем парсер ко всем строкам (axis=1) и объединяем списки словарей (.sum())
    items_list = df.apply(extract_purchase_items_with_context, axis=1).sum()

    if items_list:
        items_df = pd.DataFrame(items_list)

        # Разделяем на 2 датафрейма: где есть код, и где кода нет
        df_has_okpd = items_df[items_df['code'] != 'Нет ОКПД2']
        df_no_okpd = items_df[items_df['code'] == 'Нет ОКПД2']

        # --- СВОДНАЯ: ЗАКУПКИ БЕЗ ОКПД2 ---
        print(f"\n{'=' * 130}")
        print(f"ЗАКУПКИ БЕЗ УКАЗАНИЯ ОКПД2 В JSON (Найдено: {len(df_no_okpd)})")
        print(f"{'=' * 130}")

        if not df_no_okpd.empty:
            print(f"{'Реестровый номер':<25} {'Закон':<10} {'Объект закупки (БД)'}")
            print("-" * 130)
            for _, r in df_no_okpd.iterrows():
                obj_short = r['object_name'][:90] + '...' if len(r['object_name']) > 90 else r['object_name']
                print(f"{r['reg_number']:<25} {r['law']:<10} {obj_short}")
        else:
            print("У всех загруженных закупок успешно найден ОКПД2.")

        print(f"{'-' * 130}")

        # --- СТАНДАРТНАЯ СВОДНАЯ: ТОП ПОЗИЦИЙ ОКПД2 ---
        if not df_has_okpd.empty:
            # Используем ваш старый метод вывода для успешных кодов
            print_summary(df_has_okpd, 'code', 'ЗАКУПКИ: ТОП ПОЗИЦИЙ В КРУПНЫХ ТЕНДЕРАХ (ОКПД2)', limit=30)

    else:
        print("Не удалось извлечь информацию о позициях.")

    print(f"\n{'-' * 130}")

def print_summary_with_sum(df, group_col, value_col, title, limit=None):
    """Выводит сводную таблицу с количеством и суммой value_col по группировке group_col"""
    print(f"\n{'=' * 80}")
    print(f"СВОДНАЯ ТАБЛИЦА: {title}")
    print(f"{'=' * 80}")

    if df is None or df.empty:
        print("Нет данных для анализа")
        return

    grouped = df.groupby(group_col)[value_col].agg(['count', 'sum']).sort_values('sum', ascending=False)
    if limit:
        grouped = grouped.head(limit)

    # Форматирование вывода
    print(f"{'Категория':<50} {'Кол-во':>8} {'Сумма, руб':>20}")
    print("-" * 80)
    for idx, row in grouped.iterrows():
        count = int(row['count'])
        total = row['sum']
        clean_name = str(idx).strip()
        short_name = (clean_name[:50] + '...') if len(clean_name) > 50 else clean_name
        total_fmt = "{:,.0f}".format(total).replace(',', ' ') if total > 0 else '-'
        print(f"{short_name:<50} {count:>8} {total_fmt:>20}")

    print("-" * 80)
    if limit and len(grouped) > limit:
        print(f"{f'... и еще {len(grouped) - limit} строк ...':<50}")
    total_count = grouped['count'].sum()
    total_sum = grouped['sum'].sum()
    total_sum_fmt = "{:,.0f}".format(total_sum).replace(',', ' ')
    print(f"{'ИТОГО':<50} {total_count:>8} {total_sum_fmt:>20}")
def clean_okpd2(code):
    """Очищает код ОКПД2 от лишнего текста (оставляет только цифры и точки в начале)"""
    if not code: return None
    # Ищем паттерн вида "30.11.2" в начале строки
    match = re.match(r'^([\d\.]+)', str(code).strip())
    if match:
        return match.group(1).strip('.')
    return str(code).strip()


def extract_purchase_items_with_context(row):
    """
    Извлекает товары из common_info_json (44-ФЗ) или lots_json (223-ФЗ)
    """
    law = row['law']
    extracted_items = []

    # --- ЛОГИКА ДЛЯ 44-ФЗ ---
    if '44' in str(law):
        json_data = row['common_info_json']
        if isinstance(json_data, dict):
            try:
                info_section = json_data.get('информация_об_объекте_закупки', {})
                items = info_section.get('items', [])
                for item in items:
                    if item.get('kind') == 'table':
                        rows = item.get('table', {}).get('rows', [])
                        for r in rows:
                            code = r.get('КОД ПОЗИЦИИ')  # ОКПД2 / КТРУ
                            cost = r.get('СТОИМОСТЬ, ₽')
                            if code:
                                cost_val = clean_price_value(cost)
                                extracted_items.append({
                                    'code': clean_okpd2(code),
                                    'law': '44-ФЗ',
                                    'cost': cost_val if cost_val else 0
                                })
            except Exception:
                pass

    # --- ЛОГИКА ДЛЯ 223-ФЗ ---
    elif '223' in str(law):
        json_data = row['lots_json']
        if isinstance(json_data, dict):
            try:
                # Проходим по всем ключам (сведения_о_лотах, table_standalone и т.д.)
                for key, section in json_data.items():
                    if isinstance(section, dict):
                        items = section.get('items', [])
                        for item in items:
                            parsed = item.get('parsed_table', {})
                            rows = parsed.get('rows', [])
                            for r in rows:
                                # Извлекаем ОКПД2 из поля "КЛАССИФИКАЦИЯ ПО ОКПД2"
                                # Пример: "30.11 Корабли..." -> берем "30.11"
                                okpd_raw = r.get('КЛАССИФИКАЦИЯ ПО ОКПД2')

                                # Цена из "СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА"
                                # Пример: "Начальная ... цена ...: 29 690 000,00 ₽"
                                price_raw = r.get('СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА')

                                if okpd_raw:
                                    code = clean_okpd2(okpd_raw)

                                    # Чистим цену: удаляем текст, оставляем числа
                                    cost_val = 0
                                    if price_raw:
                                        # Регулярка для поиска цены (числа с пробелами и запятой перед символом рубля или в конце)
                                        # Ищем последнее число в строке
                                        params = re.findall(r'([\d\s]+,\d{2})', str(price_raw))
                                        if params:
                                            cost_val = clean_price_value(
                                                params[-1])  # Берем последнее найденное (обычно это цена)

                                    extracted_items.append({
                                        'code': code,
                                        'law': '223-ФЗ',
                                        'cost': cost_val if cost_val else 0
                                    })
            except Exception:
                pass

    return extracted_items


def analyze_okpd2_usage(engine):
    query = f"""
    SELECT law, common_info_json, lots_json
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND {_DATE_EXPR} <= '2025-12-31'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    """
    try:
        print("\n>>> Анализ использования кодов ОКПД2 (Common + Lots)...")
        df = pd.read_sql_query(query, engine)
        df = _parse_json_cols(df, 'common_info_json', 'lots_json')
        print(f"✓ Загружено {len(df)} закупок для анализа товаров")
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    if df.empty: return

    # Применяем новую функцию
    items_list = df.apply(extract_purchase_items_with_context, axis=1).sum()

    if not items_list:
        print("Товары не найдены (проверьте структуру JSON).")
        return

    items_df = pd.DataFrame(items_list)

    # === ТАБЛИЦА 10 ===
    print(f"\n{'=' * 90}")
    print("Таблица 10. Информация о применении кодов ОКПД2 (ед. и сумма)")
    print(f"{'=' * 90}")

    grouped = items_df.groupby(['code', 'law'])['cost'].agg(['count', 'sum'])
    unstacked = grouped.unstack(fill_value=0)

    # Гарантируем колонки
    for metric in ['count', 'sum']:
        for law in ['44-ФЗ', '223-ФЗ']:
            if (metric, law) not in unstacked.columns:
                unstacked[(metric, law)] = 0

    # Итоги
    unstacked[('count', 'Общий Итог')] = unstacked[('count', '44-ФЗ')] + unstacked[('count', '223-ФЗ')]
    unstacked[('sum', 'Общий Итог')] = unstacked[('sum', '44-ФЗ')] + unstacked[('sum', '223-ФЗ')]

    # Сортировка и вывод
    unstacked = unstacked.sort_values(('count', 'Общий Итог'), ascending=False).head(50)

    final_rows = []
    for code in unstacked.index:
        row_data = unstacked.loc[code]
        final_rows.append({
            'Код ОКПД2': str(code)[:60],
            'Показатель': 'количество закупок, ед.',
            '44-ФЗ': int(row_data[('count', '44-ФЗ')]),
            '223-ФЗ': int(row_data[('count', '223-ФЗ')]),
            'Общий Итог': int(row_data[('count', 'Общий Итог')])
        })
        final_rows.append({
            'Код ОКПД2': '',
            'Показатель': 'сумма НМЦК, руб.',
            '44-ФЗ': row_data[('sum', '44-ФЗ')],
            '223-ФЗ': row_data[('sum', '223-ФЗ')],
            'Общий Итог': row_data[('sum', 'Общий Итог')]
        })

    final_df = pd.DataFrame(final_rows)

    def format_val(x):
        if x == 0: return "-"
        if isinstance(x, (int, float)):
            if x % 1 == 0: return "{:,.0f}".format(x).replace(',', ' ')
            return "{:,.2f}".format(x).replace(',', ' ')
        return x

    for c in ['44-ФЗ', '223-ФЗ', 'Общий Итог']:
        final_df[c] = final_df[c].apply(format_val)

    print(final_df.to_string(index=False, justify='right'))
    print(f"{'-' * 90}")


# --- Блок анализа поставщиков ---
def analyze_suppliers(engine):
    query = """
    SELECT s.organization 
    FROM supplier s
    JOIN contracts c ON s.contract_id = c.id
    JOIN purchase p ON c.reg_number = p.reg_number
    WHERE CAST(p.initial_price_amount AS REAL) >= 100000000
    """
    try:
        print("\n>>> Загрузка поставщиков по крупным контрактам...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} записей поставщиков")

        if df.empty:
            print("Поставщики для таких закупок не найдены.")
        else:
            print_summary(df, 'organization', 'ПОСТАВЩИКИ КРУПНЫХ КОНТРАКТОВ', limit=30)

    except Exception as e:
        print(f"Ошибка загрузки поставщиков: {e}")


def analyze_contracts(engine):
    query = """
    SELECT c.law, c.status, c.customer_name, 
           c.contract_price, c.payment_targets_json 
    FROM contracts c
    JOIN purchase p ON c.reg_number = p.reg_number
    WHERE CAST(p.initial_price_amount AS REAL) >= 20000000
    """
    try:
        df = pd.read_sql_query(query, engine)
        df = _parse_json_cols(df, 'payment_targets_json')
    except Exception as e:
        print(f"Ошибка загрузки контрактов: {e}")
        return

    if df.empty:
        print("Контракты для таких закупок не найдены.")
        return

    # 1. Сводные
    print_summary(df, 'law', 'КОНТРАКТЫ: ЗАКОНЫ')
    print_summary(df, 'customer_name', 'КОНТРАКТЫ: ЗАКАЗЧИКИ')

    # 2. Товары внутри контрактов
    print("\n... Извлечение позиций из контрактов ...")
    items_series = df['payment_targets_json'].apply(extract_contract_items_new)
    items_df = pd.DataFrame(items_series.explode().dropna().tolist())

    if not items_df.empty:
        print_summary(items_df, 'ktru', 'КОНТРАКТЫ: ПОПУЛЯРНЫЕ ПОЗИЦИИ', limit=30)

        # Анализ цен внутри позиций
        items_df['price_float'] = pd.to_numeric(items_df['price'], errors='coerce')
        items_df['item_price_category'] = items_df['price_float'].apply(categorize_price)

        price_order = [
            'до 400 тыс.', '400 тыс. — 1 млн', '1 — 5 млн',
            '5 — 20 млн', '20 — 100 млн', '100 млн — 1 млрд',
            'более 1 млрд'
        ]
        items_df['item_price_category'] = pd.Categorical(
            items_df['item_price_category'], categories=price_order, ordered=True
        )

        print_summary(
            items_df.sort_values('item_price_category'),
            'item_price_category',
            'КОНТРАКТЫ: СТОИМОСТЬ ПОЗИЦИЙ'
        )
    else:
        print("Товары в контрактах не найдены.")


def analyze_contract_status(engine):
    query = f"""
    SELECT p.law, c.status as contract_status, c.contract_price
    FROM purchase p
    LEFT JOIN contracts c ON p.reg_number = c.reg_number
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND {_DATE_EXPR} <= '2025-12-31'
      AND CAST(p.initial_price_amount AS REAL) >= 100000000
    """

    try:
        print("\n>>> Анализ статусов контрактов...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} записей")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    if df.empty:
        return

    # Заполняем пропуски (закупки без контракта)
    # Заполняем пропуски (закупки без контракта)
    df['contract_status'] = df['contract_status'].fillna('Нет контракта')

    # ИСПРАВЛЕНИЕ: используем clean_price_value вместо pd.to_numeric напрямую
    df['price'] = df['contract_price'].apply(
        lambda x: clean_price_value(x) if pd.notna(x) and str(x).strip() != '' else 0.0
    )

    # =========================================================================
    # ТАБЛИЦА 1: СТАТУС КОНТРАКТА × ЗАКОН (кол-во и сумма)
    # =========================================================================
    print(f"\n{'=' * 120}")
    print("Таблица. Статус контракта/договора по законам (кол-во и сумма)")
    print(f"{'=' * 120}")

    grouped_cs = df.groupby(['contract_status', 'law'])['price'].agg(['count', 'sum'])
    pivot_cs_count = grouped_cs['count'].unstack(fill_value=0)
    pivot_cs_sum   = grouped_cs['sum'].unstack(fill_value=0)

    # Гарантируем наличие обеих колонок законов
    for law_col in ['44-ФЗ', '223-ФЗ']:
        if law_col not in pivot_cs_count.columns:
            pivot_cs_count[law_col] = 0
        if law_col not in pivot_cs_sum.columns:
            pivot_cs_sum[law_col] = 0

    # Итоговые колонки
    pivot_cs_count['Общий итог'] = pivot_cs_count.sum(axis=1)
    pivot_cs_sum['Общий итог']   = pivot_cs_sum.sum(axis=1)

    # Сортируем по убыванию итогового количества
    pivot_cs_count = pivot_cs_count.sort_values('Общий итог', ascending=False)
    pivot_cs_sum   = pivot_cs_sum.loc[pivot_cs_count.index]

    # Добавляем итоговую строку
    pivot_cs_count.loc['Общий итог'] = pivot_cs_count.sum()
    pivot_cs_sum.loc['Общий итог']   = pivot_cs_sum.sum()

    print(f"{'Статус контракта':<40} {'Показатель':<15} {'44-ФЗ':>20} {'223-ФЗ':>20} {'Общий итог':>20}")
    print("-" * 120)

    for status in pivot_cs_count.index:
        # Строка кол-во
        c_44    = int(pivot_cs_count.loc[status, '44-ФЗ'])
        c_223   = int(pivot_cs_count.loc[status, '223-ФЗ'])
        c_total = int(pivot_cs_count.loc[status, 'Общий итог'])

        print(f"{str(status):<40} {'кол-во':<15} "
              f"{(str(c_44) if c_44 > 0 else '-'):>20} "
              f"{(str(c_223) if c_223 > 0 else '-'):>20} "
              f"{c_total:>20}")

        # Строка сумма
        s_44    = pivot_cs_sum.loc[status, '44-ФЗ']
        s_223   = pivot_cs_sum.loc[status, '223-ФЗ']
        s_total = pivot_cs_sum.loc[status, 'Общий итог']

        fmt = lambda x: "{:,.0f}".format(x).replace(',', ' ') if x > 0 else '-'
        print(f"{'':40} {'сумма, руб':<15} "
              f"{fmt(s_44):>20} "
              f"{fmt(s_223):>20} "
              f"{fmt(s_total):>20}")

    print("-" * 120)

    # =========================================================================
    # ТАБЛИЦА 2: ТОЛЬКО КОНТРАКТЫ (без "Нет контракта") - общая статистика
    # =========================================================================
    df_with = df[df['contract_status'] != 'Нет контракта']

    if not df_with.empty:
        print(f"\n{'=' * 120}")
        print("Таблица. Общая статистика по сумме контрактов (contract_price)")
        print(f"{'=' * 120}")

        stats = df_with.groupby('law')['price'].agg(['count', 'sum', 'max', 'min', 'mean'])
        stats_t = stats.T

        # Добавляем итоговую колонку
        total_col = pd.Series({
            'count': df_with['price'].count(),
            'sum':   df_with['price'].sum(),
            'max':   df_with['price'].max(),
            'min':   df_with['price'].min(),
            'mean':  df_with['price'].mean()
        }, name='Общий итог')
        stats_t = pd.concat([stats_t, total_col.to_frame()], axis=1)

        index_map = {
            'count': 'Количество контрактов, ед.',
            'sum':   'Сумма контрактов, руб.',
            'max':   'Максимальная цена, руб.',
            'min':   'Минимальная цена, руб.',
            'mean':  'Средняя цена, руб.'
        }
        stats_t = stats_t.rename(index=index_map)
        pd.options.display.float_format = '{:,.2f}'.format
        print(stats_t.fillna(0))
        print("-" * 120)

    # =========================================================================
    # ТАБЛИЦА 3: КОНВЕРСИЯ - закупки С контрактом vs БЕЗ (по кол-ву и сумме)
    # =========================================================================
    print(f"\n{'=' * 120}")
    print("Таблица. Конверсия: закупки с контрактом vs без контракта")
    print(f"{'=' * 120}")

    df['conv_group'] = df['contract_status'].apply(
        lambda x: 'Заключён контракт' if x != 'Нет контракта' else 'Без контракта'
    )

    grouped_conv = df.groupby(['conv_group', 'law'])['price'].agg(['count', 'sum'])
    pivot_conv_count = grouped_conv['count'].unstack(fill_value=0)
    pivot_conv_sum   = grouped_conv['sum'].unstack(fill_value=0)

    for law_col in ['44-ФЗ', '223-ФЗ']:
        if law_col not in pivot_conv_count.columns:
            pivot_conv_count[law_col] = 0
        if law_col not in pivot_conv_sum.columns:
            pivot_conv_sum[law_col] = 0

    pivot_conv_count['Общий итог'] = pivot_conv_count.sum(axis=1)
    pivot_conv_sum['Общий итог']   = pivot_conv_sum.sum(axis=1)

    pivot_conv_count.loc['Общий итог'] = pivot_conv_count.sum()
    pivot_conv_sum.loc['Общий итог']   = pivot_conv_sum.sum()

    # Считаем процент конверсии по количеству и сумме
    total_count = pivot_conv_count.loc['Общий итог', 'Общий итог']
    total_sum   = pivot_conv_sum.loc['Общий итог', 'Общий итог']

    print(f"{'Группа':<25} {'Показатель':<15} {'44-ФЗ':>20} {'223-ФЗ':>20} {'Общий итог':>20} {'Доля, %':>10}")
    print("-" * 120)

    for group in pivot_conv_count.index:
        c_44    = int(pivot_conv_count.loc[group, '44-ФЗ'])
        c_223   = int(pivot_conv_count.loc[group, '223-ФЗ'])
        c_total = int(pivot_conv_count.loc[group, 'Общий итог'])
        pct_c   = round(c_total / total_count * 100, 1) if total_count > 0 and group != 'Общий итог' else '-'

        print(f"{str(group):<25} {'кол-во':<15} "
              f"{(str(c_44) if c_44 > 0 else '-'):>20} "
              f"{(str(c_223) if c_223 > 0 else '-'):>20} "
              f"{c_total:>20} "
              f"{str(pct_c) + '%' if pct_c != '-' else '-':>10}")

        s_44    = pivot_conv_sum.loc[group, '44-ФЗ']
        s_223   = pivot_conv_sum.loc[group, '223-ФЗ']
        s_total = pivot_conv_sum.loc[group, 'Общий итог']
        pct_s   = round(s_total / total_sum * 100, 1) if total_sum > 0 and group != 'Общий итог' else '-'

        fmt = lambda x: "{:,.0f}".format(x).replace(',', ' ') if x > 0 else '-'
        print(f"{'':25} {'сумма, руб':<15} "
              f"{fmt(s_44):>20} "
              f"{fmt(s_223):>20} "
              f"{fmt(s_total):>20} "
              f"{str(pct_s) + '%' if pct_s != '-' else '-':>10}")

    print("-" * 120)


# --- Блок анализа контрактов ---
def extract_contract_okpd2(json_data):
    if not isinstance(json_data, dict): return []
    extracted = []
    try:
        items = json_data.get('товары_работы_услуги', {}).get('items', [])
        for item in items:
            if item.get('kind') == 'goods_table':
                for row in item.get('rows', []):
                    code = row.get('ОКПД2')
                    if code and code != '-': extracted.append(code)
    except:
        pass
    return extracted




def extract_contract_items_new(json_data):
    """
    Извлекает KTRU и цену из новой структуры JSON (объекты_закупки)
    """
    if not isinstance(json_data, dict):
        return []

    extracted_items = []

    try:
        # 1. Заходим в "объекты_закупки" -> "items"
        main_section = json_data.get('объекты_закупки', {})
        items = main_section.get('items', [])

        for item in items:
            # 2. Ищем элемент с kind="table"
            if item.get('kind') == 'table':
                # 3. Заходим в table -> rows
                rows = item.get('table', {}).get('rows', [])

                for row in rows:
                    # Извлекаем нужные поля
                    ktru_raw = row.get('ktru')
                    price = row.get('price')

                    # Небольшая очистка KTRU (убираем перенос строки, чтобы таблица не разъезжалась)
                    ktru_clean = str(ktru_raw).replace('\n', ' ').strip() if ktru_raw else None

                    if ktru_clean or price is not None:
                        extracted_items.append({
                            'ktru': ktru_clean,
                            'price': price
                        })
    except Exception:
        pass

    return extracted_items


def analyze_purchase_contract_links(engine):
    query = """
    SELECT law,
           CASE WHEN contract_id IS NOT NULL 
                THEN 'Заключен контракт' 
                ELSE 'Нет контракта' END as status_contract
    FROM purchase
    """
    try:
        print("\n>>> Анализ связей: Закупки -> Контракты...")
        df = pd.read_sql_query(query, engine)

        # 1. Общая сводная
        print_summary(df, 'status_contract', 'КОНВЕРСИЯ В КОНТРАКТ')

        # 2. Детальная разбивка по законам (через кросс-таблицу)
        print(f"\n{'=' * 60}")
        print(f"ДЕТАЛИЗАЦИЯ ПО ЗАКОНАМ")
        print(f"{'=' * 60}")

        # Строим таблицу: Строки = Закон, Столбцы = Есть контракт или нет
        pivot = pd.crosstab(df['law'], df['status_contract'])
        print(pivot)
        print(f"{'-' * 60}")

    except Exception as e:
        print(f"Ошибка анализа связей: {e}")


def analyze_purchase_by_year(engine, start_date=None, end_date=None):
    query = f"""
    SELECT law, published 
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    """

    try:
        print("\n>>> Анализ закупок по годам (published)...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} записей")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    # Остальной код без изменений...
    # Явно указываем формат DD.MM.YYYY
    df['published_dt'] = pd.to_datetime(df['published'], format='%d.%m.%Y', errors='coerce')

    df = df.dropna(subset=['published_dt'])

    if start_date:
        start_dt = pd.to_datetime(start_date, dayfirst=True, errors='coerce')
        if pd.notna(start_dt):
            df = df[df['published_dt'] >= start_dt]

    if end_date:
        end_dt = pd.to_datetime(end_date, dayfirst=True, errors='coerce')
        if pd.notna(end_dt):
            df = df[df['published_dt'] < end_dt]

    if df.empty:
        print("Нет данных после обработки дат.")
        return

    df['year'] = df['published_dt'].dt.year

    print_summary(df, 'year', 'ЗАКУПКИ: КОЛИЧЕСТВО ПО ГОДАМ')

    print(f"\n{'=' * 60}")
    print("ЗАКУПКИ: ГОД × ЗАКОН")
    print(f"{'=' * 60}")

    pivot = pd.crosstab(df['year'], df['law']).sort_index()
    print(pivot)
    print(f"{'-' * 60}")


def analyze_purchase_amounts_by_year(engine, start_date=None, end_date=None):
    query = f"""
    SELECT law, published, initial_price_amount
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    """

    try:
        print("\n>>> Анализ ОБЪЕМОВ ЗАКУПОК (ДЕНЬГИ) по годам...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} записей")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    # 1. Обработка дат (формат DD.MM.YYYY)
    df['published_dt'] = pd.to_datetime(df['published'], format='%d.%m.%Y', errors='coerce')

    # 2. Обработка цен (используем вашу функцию очистки clean_price_value или аналог)
    # Если clean_price_value недоступна в этом скоупе, можно продублировать простую логику:
    def clean_price(val):
        if pd.isna(val): return 0.0
        try:
            # Убираем пробелы, меняем запятую на точку (стандартная чистка)
            s = str(val).replace(' ', '').replace(',', '.').replace('₽', '')
            return float(s)
        except:
            return 0.0

    df['price_clean'] = df['initial_price_amount'].apply(clean_price)

    # Убираем записи, где нет даты
    df = df.dropna(subset=['published_dt'])

    # Фильтр по датам (если нужен)
    if start_date:
        start_dt = pd.to_datetime(start_date, dayfirst=True, errors='coerce')
        if pd.notna(start_dt):
            df = df[df['published_dt'] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date, dayfirst=True, errors='coerce')
        if pd.notna(end_dt):
            df = df[df['published_dt'] < end_dt]

    if df.empty:
        print("Нет данных для анализа.")
        return

    # Выделяем год
    df['year'] = df['published_dt'].dt.year

    # --- 1) Общая сумма по годам ---
    print(f"\n{'=' * 60}")
    print("ДЕНЬГИ: ОБЩАЯ СУММА ПО ГОДАМ (в рублях)")
    print(f"{'=' * 60}")

    # Группируем по году и суммируем цену
    yearly_sum = df.groupby('year')['price_clean'].sum().sort_index()

    # Красивый вывод с разделителями тысяч
    for year, amount in yearly_sum.items():
        print(f"{year}: {amount:,.2f}".replace(',', ' '))
    print(f"{'-' * 60}")

    # --- 2) Сводная таблица: Год × Закон (Сумма) ---
    print(f"\n{'=' * 60}")
    print("ДЕНЬГИ: ГОД × ЗАКОН (СУММА)")
    print(f"{'=' * 60}")

    # aggfunc='sum' делает сумму вместо подсчета количества
    pivot_sum = pd.pivot_table(
        df,
        values='price_clean',
        index='year',
        columns='law',
        aggfunc='sum',
        fill_value=0
    ).sort_index()

    # Форматируем вывод таблицы (чтобы не было научной нотации 1.5e+09)
    pd.options.display.float_format = '{:,.2f}'.format
    print(pivot_sum)
    print(f"{'-' * 60}")


def extract_item_names(row):
    """
    Извлекает НАИМЕНОВАНИЕ ТОВАРА (44-ФЗ) и НАИМЕНОВАНИЕ ЛОТА (223-ФЗ) из JSON.
    """
    law = str(row.get('law', ''))
    extracted_items = []

    # --- 44-ФЗ: Из common_info_json ---
    if '44' in law:
        json_data = row.get('common_info_json')
        if isinstance(json_data, dict):
            try:
                info_section = json_data.get('информация_об_объекте_закупки', {})
                for item in info_section.get('items', []):
                    if item.get('kind') == 'table':
                        for r in item.get('table', {}).get('rows', []):
                            name = r.get('НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ ПО ОКПД2, КТРУ')
                            cost = r.get('СТОИМОСТЬ, ₽')

                            if name:
                                # Очищаем стоимость
                                cost_val = clean_price_value(cost) if cost else 0
                                extracted_items.append({
                                    'name': str(name).strip(),
                                    'cost': cost_val
                                })
            except Exception:
                pass

    # --- 223-ФЗ: Из lots_json ---
    elif '223' in law:
        json_data = row.get('lots_json')
        if isinstance(json_data, dict):
            try:
                for key, section in json_data.items():
                    if isinstance(section, dict):
                        for item in section.get('items', []):
                            for r in item.get('parsed_table', {}).get('rows', []):
                                name_field = r.get('НОМЕР, НАИМЕНОВАНИЕ ЛОТА')
                                name = None

                                # Поле может быть словарем с "text" или просто строкой
                                if isinstance(name_field, dict):
                                    name = name_field.get('text')
                                elif isinstance(name_field, str):
                                    name = name_field

                                price_raw = r.get('СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА')
                                cost_val = 0

                                if price_raw:
                                    params = re.findall(r'([\d\s]+,\d{2})', str(price_raw))
                                    if params:
                                        cost_val = clean_price_value(params[-1])

                                if name:
                                    # В 223-ФЗ название лота часто начинается с номера "1 Выполнение...".
                                    # Убираем цифры в начале для красивой группировки.
                                    clean_name = re.sub(r'^\d+\s+', '', str(name)).strip()
                                    extracted_items.append({
                                        'name': clean_name,
                                        'cost': cost_val
                                    })
            except Exception:
                pass

    return extracted_items


def analyze_item_names_only(engine):
    """
    СВОДНАЯ ТОЛЬКО ПО НАИМЕНОВАНИЯМ ТОВАРОВ ИЗ JSON (20+ млн, 2018-2025)
    """
    # Достаем оба JSON-поля
    query = """
    SELECT 
        law,
        common_info_json,
        lots_json
    FROM public.purchase
    WHERE to_date(published, 'DD.MM.YYYY') >= DATE '2018-01-01'
      AND to_date(published, 'DD.MM.YYYY') <= DATE '2025-12-31'
      AND initial_price_amount >= 100000000
    """

    try:
        print("\n>>> ИЗВЛЕЧЕНИЕ НАИМЕНОВАНИЙ ИЗ JSON (20+ млн, 2018-2025)...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} закупок для анализа")
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    if df.empty:
        print("Нет данных.")
        return

    # Применяем парсер
    items_list = df.apply(extract_item_names, axis=1).sum()

    if not items_list:
        print("Наименования не найдены (проверьте структуру JSON).")
        return

    items_df = pd.DataFrame(items_list)

    # Группируем по наименованию
    grouped = items_df.groupby('name')['cost'].agg(['count', 'sum']).sort_values('sum', ascending=False)

    # Вывод
    # Я сделал колонку наименования шире (80 символов), так как названия товаров бывают очень длинными
    print(f"\n{'=' * 120}")
    print("СВОДНАЯ: НАИМЕНОВАНИЯ ТОВАРОВ И ЛОТОВ (из JSON, 20+ млн руб)")
    print(f"{'=' * 120}")
    print(f"{'Наименование товара/лота':<85} {'Кол-во':>10} {'Сумма, руб':>20}")
    print(f"{'-' * 120}")

    for name, row in grouped.iterrows():
        # Обрезаем сверхдлинные названия для красоты консоли
        raw_name = str(name).replace('\n', ' ')
        short_name = raw_name[:80] + '...' if len(raw_name) > 80 else raw_name

        count = int(row['count'])
        price = row['sum']
        price_fmt = "{:,.0f}".format(price).replace(',', ' ') if price > 0 else '-'

        print(f"{short_name:<85} {count:>10} {price_fmt:>20}")

    print(f"{'-' * 120}")
    total_all = grouped['sum'].sum()
    print(f"{'ИТОГО':<85} {'-':>10} {'{:,.0f}'.format(total_all).replace(',', ' '):>20}")


def analyze_objects_only(engine):
    query = f"""
    SELECT object_name,
           COUNT(*) as count_purchase,
           SUM(CAST(initial_price_amount AS REAL)) as total_price
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND {_DATE_EXPR} <= '2025-12-31'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    GROUP BY object_name
    ORDER BY total_price DESC
    """

    try:
        print("\n>>> СВОДНАЯ ПО ОБЪЕКТАМ ЗАКУПКИ (20+ млн, 2018-2025)...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Найдено {len(df)} уникальных объектов закупки")
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    if df.empty:
        print("Нет данных.")
        return

    # Цена в числовой формат
    df['total_price_num'] = pd.to_numeric(df['total_price'], errors='coerce').fillna(0)

    print(f"\n{'=' * 90}")
    print("СВОДНАЯ: ОБЪЕКТЫ ЗАКУПКИ (20+ млн руб)")
    print(f"{'=' * 90}")
    print(f"{'Object Name':<60} {'Кол-во':>10} {'Сумма, руб':>20}")
    print(f"{'-' * 90}")

    # ПОЛНЫЙ ВЫВОД БЕЗ ОГРАНИЧЕНИЙ
    for _, row in df.iterrows():
        obj_name = str(row['object_name'])[:60]
        count = int(row['count_purchase'])
        price = row['total_price_num']

        price_fmt = "{:,.0f}".format(price).replace(',', ' ') if price > 0 else '-'

        print(f"{obj_name:<60} {count:>10} {price_fmt:>20}")

    print(f"{'-' * 90}")
    total_all = df['total_price_num'].sum()
    print(f"{'ИТОГО':<60} {'-':>10} {'{:,.0f}'.format(total_all).replace(',', ' '):>20}")



def extract_item_names(row):
    """
    Вспомогательная функция.
    Извлекает НАИМЕНОВАНИЕ ТОВАРА (44-ФЗ) и НАИМЕНОВАНИЕ ЛОТА (223-ФЗ) из JSON.
    """
    law = str(row.get('law', ''))
    extracted_items = []

    # --- 44-ФЗ: Из common_info_json ---
    if '44' in law:
        json_data = row.get('common_info_json')
        if isinstance(json_data, dict):
            try:
                info_section = json_data.get('информация_об_объекте_закупки', {})
                for item in info_section.get('items', []):
                    if item.get('kind') == 'table':
                        for r in item.get('table', {}).get('rows', []):
                            name = r.get('НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ')
                            cost = r.get('СТОИМОСТЬ, ₽')

                            if name:
                                # Очищаем стоимость (предполагается, что clean_price_value определена выше)
                                cost_val = clean_price_value(cost) if cost else 0
                                extracted_items.append({
                                    'name': str(name).strip(),
                                    'cost': cost_val
                                })
            except Exception:
                pass

    # --- 223-ФЗ: Из lots_json ---
    elif '223' in law:
        json_data = row.get('lots_json')
        if isinstance(json_data, dict):
            try:
                for key, section in json_data.items():
                    if isinstance(section, dict):
                        for item in section.get('items', []):
                            for r in item.get('parsed_table', {}).get('rows', []):
                                name_field = r.get('НОМЕР, НАИМЕНОВАНИЕ ЛОТА')
                                name = None

                                # Поле может быть словарем с "text" или просто строкой
                                if isinstance(name_field, dict):
                                    name = name_field.get('text')
                                elif isinstance(name_field, str):
                                    name = name_field

                                price_raw = r.get('СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА')
                                cost_val = 0

                                if price_raw:
                                    params = re.findall(r'([\d\s]+,\d{2})', str(price_raw))
                                    if params:
                                        cost_val = clean_price_value(params[-1])

                                if name:
                                    # Убираем цифры в начале номера лота "1 Выполнение..." -> "Выполнение..."
                                    clean_name = re.sub(r'^\d+\s+', '', str(name)).strip()
                                    extracted_items.append({
                                        'name': clean_name,
                                        'cost': cost_val
                                    })
            except Exception:
                pass

    return extracted_items


def extract_items_with_object(row):
    law = str(row.get('law', ''))
    obj_name = str(row.get('object_name', '')).replace('\n', ' ').strip()
    reg_number = str(row.get('reg_number', '')).strip()
    published = str(row.get('published', '')).strip()  # ← ДОБАВЛЕНО

    initial_price = pd.to_numeric(row.get('initial_price_amount'), errors='coerce')
    if pd.isna(initial_price):
        initial_price = 0

    extracted_items = []

    # === СТОП-ЛИСТ ===
    stop_words = [
        'вольт', 'киловатт', 'штука', 'комплект', 'килограмм', 'тонна',
        'метр', 'миллиметр', 'литр', 'час', 'человек', 'дециметр',
        'наименование характеристики', 'значение характеристики',
        'услуги по финансовой аренде', 'сантиметр',
        'дюйм (25,4 мм)', 'кубический метр', 'кубический метр в час',
        'мегаватт; тысяча киловатт', 'лошадиная сила', 'мегагерц',
        'километр в час', 'километр; тысяча метров'
    ]

    def is_valid_name(name_str):
        if not name_str:
            return False
        clean_str = str(name_str).strip().lower()
        if not clean_str:
            return False
        for word in stop_words:
            if clean_str == word or clean_str.startswith(word + ' ') or clean_str.startswith(word + ';'):
                return False
        return True

    # --- 44-ФЗ ---
    if '44' in law:
        json_data = row.get('common_info_json')
        if isinstance(json_data, dict):
            try:
                info_section = json_data.get('информация_об_объекте_закупки', {})
                for item in info_section.get('items', []):
                    if item.get('kind') == 'table':
                        for r in item.get('table', {}).get('rows', []):
                            name = (
                                    r.get('НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ ПО ОКПД2, КТРУ') or
                                    r.get('НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ')
                            )
                            cost = r.get('СТОИМОСТЬ, ₽')

                            if is_valid_name(name):
                                cost_val = clean_price_value(cost) if cost else 0
                                extracted_items.append({'item_name': str(name).strip(), 'cost': cost_val})
            except Exception:
                pass

    # --- 223-ФЗ ---
    elif '223' in law:
        json_data = row.get('lots_json')
        if isinstance(json_data, dict):
            try:
                for key, section in json_data.items():
                    if isinstance(section, dict):
                        for item in section.get('items', []):
                            for r in item.get('parsed_table', {}).get('rows', []):
                                name_field = r.get('НОМЕР, НАИМЕНОВАНИЕ ЛОТА')
                                name = None
                                if isinstance(name_field, dict):
                                    name = name_field.get('text')
                                elif isinstance(name_field, str):
                                    name = name_field
                                price_raw = r.get('СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА')
                                cost_val = 0
                                if price_raw:
                                    params = re.findall(r'([\d\s]+,\d{2})', str(price_raw))
                                    if params:
                                        cost_val = clean_price_value(params[-1])

                                if is_valid_name(name):
                                    clean_name = re.sub(r'^\d+\s+', '', str(name)).strip()
                                    extracted_items.append({'item_name': clean_name, 'cost': cost_val})
            except Exception:
                pass

    if not extracted_items:
        extracted_items.append({
            'item_name': '<Детализация в JSON отсутствует>',
            'cost': 0
        })

    # Добавляем данные закупки к каждому товару
    for item in extracted_items:
        item['object_name'] = obj_name
        item['reg_number'] = reg_number
        item['initial_price'] = initial_price
        item['published'] = published  # ← ДОБАВЛЕНО

    return extracted_items


def analyze_combined_objects_items(engine):
    query = f"""
    SELECT reg_number, published, object_name, law,
           initial_price_amount, common_info_json, lots_json
    FROM purchase
    WHERE {_DATE_EXPR} >= '2018-01-01'
      AND {_DATE_EXPR} <= '2025-12-31'
      AND CAST(initial_price_amount AS REAL) >= 100000000
    """
    try:
        df = pd.read_sql_query(query, engine)
        df = _parse_json_cols(df, 'common_info_json', 'lots_json')
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    try:
        print("\n>>> ЗАГРУЗКА И ОБЪЕДИНЕНИЕ ОБЪЕКТОВ И ТОВАРОВ (20+ млн, 2018-2025)...")
        df = pd.read_sql_query(query, engine)
        print(f"✓ Загружено {len(df)} закупок")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return

    if df.empty:
        print("Нет данных.")
        return

    items_list = df.apply(extract_items_with_object, axis=1).sum()
    if not items_list:
        print("Не удалось сформировать список товаров.")
        return

    items_df = pd.DataFrame(items_list)

    # Добавляем published в ключи группировки
    grouped = items_df.groupby(['reg_number', 'published', 'initial_price', 'object_name', 'item_name'])['cost'].agg(
        ['count', 'sum']).reset_index()

    # Переименование колонок
    grouped.rename(columns={
        'reg_number': 'Реестровый номер',
        'published': 'Дата публикации',
        'initial_price': 'НМЦК закупки (руб)',
        'object_name': 'Объект закупки (БД)',
        'item_name': 'Товар / Лот (JSON)',
        'count': 'Кол-во',
        'sum': 'Сумма товара (руб)'
    }, inplace=True)

    # Сортировка: по НМЦК, затем по дате, затем по сумме товара
    grouped = grouped.sort_values(by=['НМЦК закупки (руб)', 'Дата публикации', 'Сумма товара (руб)'],
                                  ascending=[False, False, False])

    # --- ВЫВОД В КОНСОЛЬ ---
    print(f"\n{'=' * 160}")
    print("СВОДНАЯ: ОБЪЕКТЫ ЗАКУПКИ И ВЛОЖЕННЫЕ ТОВАРЫ/ЛОТЫ (20+ млн руб, 2018-2025)")
    print(f"{'=' * 160}")

    console_df = grouped.copy()

    # Форматируем НМЦК
    console_df['НМЦК закупки (руб)'] = console_df['НМЦК закупки (руб)'].apply(
        lambda x: "{:,.0f}".format(x).replace(',', ' ') if x > 0 else '-'
    )

    # Устанавливаем 5-уровневый индекс
    console_df.set_index(
        ['Реестровый номер', 'Дата публикации', 'НМЦК закупки (руб)', 'Объект закупки (БД)', 'Товар / Лот (JSON)'],
        inplace=True)

    console_df['Сумма товара (руб)'] = console_df['Сумма товара (руб)'].apply(
        lambda x: "{:,.0f}".format(x).replace(',', ' ') if x > 0 else '-'
    )

    # Обрезаем длинные названия для консоли
    new_index = []
    for idx in console_df.index:
        new_index.append((
            idx[0],  # reg_number
            idx[1],  # published
            idx[2],  # НМЦК
            idx[3][:35] + '...' if len(idx[3]) > 35 else idx[3],  # Объект
            idx[4][:35] + '...' if len(idx[4]) > 35 else idx[4]  # Товар
        ))
    console_df.index = pd.MultiIndex.from_tuples(new_index, names=console_df.index.names)

    print(console_df.to_string(justify='right'))
    print(f"{'-' * 160}")

    # --- СОХРАНЕНИЕ В CSV ---
    filename = 'combined_objects_items.csv'
    try:
        csv_df = grouped.copy()

        # Добавляем '№' к реестровому номеру
        csv_df['Реестровый номер'] = csv_df['Реестровый номер'].apply(
            lambda x: f"№{x}" if pd.notna(x) and str(x).strip() != '' else x
        )

        # Добавляем апостроф к НМЦК и Сумме
        csv_df['НМЦК закупки (руб)'] = csv_df['НМЦК закупки (руб)'].apply(
            lambda x: f"'{x:,.0f}".replace(',', ' ') if pd.notna(x) and x > 0 else x
        )

        csv_df['Сумма товара (руб)'] = csv_df['Сумма товара (руб)'].apply(
            lambda x: f"'{x:,.0f}".replace(',', ' ') if pd.notna(x) and x > 0 else x
        )

        csv_df.to_csv(filename, sep=';', encoding='cp1251', index=False, errors='replace')
        print(f"✓ Сохранено в: {filename} (кодировка Windows-1251, разделитель ';')")
    except Exception as e:
        print(f"Ошибка при сохранении CSV: {e}")


# --- Главная функция ---
def main():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Критическая ошибка подключения: {e}")
        return
    # analyze_combined_objects_items(engine)
    # analyze_item_names_only(engine)
    # analyze_objects_only(engine)
    analyze_purchase(engine)
    # analyze_okpd2_usage(engine)
    # analyze_contract_status(engine)
    # analyze_suppliers(engine)
    # analyze_contracts(engine)
    # analyze_purchase_contract_links(engine)
    # analyze_purchase_by_year(engine)
    # analyze_purchase_amounts_by_year(engine)
if __name__ == "__main__":
    main()
