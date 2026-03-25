
import sys
sys.path.insert(0, r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle")

import pandas as pd
import re
import json
import sqlite3


# ─── Подключение к SQLite ──────────────────────────────────
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def read_sql(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)
# ─── Утилиты ───────────────────────────────────────────────

def clean_price_value(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        s = str(value).replace('\xa0', '').replace(' ', '').replace(',', '.').replace('₽', '').strip()
        return float(s)
    except (ValueError, TypeError):
        return None


def fmt(x) -> str:
    """Форматирование числа: 0 → '-', иначе разряды через пробел."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return '-'
    if x == 0:
        return '-'
    return "{:,.0f}".format(x).replace(',', ' ')


def extract_contract_price_from_json(common_info_json) -> float | None:
    """
    Пытается достать цену контракта из common_info_json версии.
    Перебирает несколько возможных ключей (44-ФЗ / 223-ФЗ).
    """
    if not isinstance(common_info_json, dict):
        return None

    # Возможные ключи верхнего уровня
    top_keys = [
        "общая_информация",
        "информация_о_договоре",
        "основные_сведения",
    ]
    # Возможные метки поля цены
    price_labels = [
        "цена контракта",
        "цена договора",
        "сумма контракта",
        "сумма договора",
        "цена",
    ]

    for top_key in top_keys:
        section = common_info_json.get(top_key)
        if not isinstance(section, dict):
            continue
        for item in section.get("items", []):
            if item.get("kind") != "field_list":
                continue
            for field in item.get("fields", []):
                label = str(field.get("label") or "").strip().lower()
                for pl in price_labels:
                    if pl in label:
                        raw = field.get("value")
                        val = clean_price_value(raw)
                        if val is not None:
                            return val

    # Фоллбэк: рекурсивно ищем ключ "contract_price" / "price"
    def _find(d, keys):
        if isinstance(d, dict):
            for k, v in d.items():
                if k.lower() in keys and isinstance(v, (int, float, str)):
                    r = clean_price_value(v)
                    if r:
                        return r
                result = _find(v, keys)
                if result:
                    return result
        elif isinstance(d, list):
            for el in d:
                result = _find(el, keys)
                if result:
                    return result
        return None

    return _find(common_info_json, {"contract_price", "price", "цена"})


# ─── Загрузка данных ───────────────────────────────────────
def diagnose_json_structure(engine):
    """Печатает ключи верхнего уровня common_info_json первых 3 версий."""
    query = """
    SELECT cv.id, cv.common_info_json
    FROM public.contract_versions cv
    WHERE cv.common_info_json IS NOT NULL
    LIMIT 3
    """
    df = pd.read_sql_query(query, engine)
    for _, row in df.iterrows():
        j = row['common_info_json']
        if isinstance(j, dict):
            print(f"\n[version_id={row['id']}] Ключи верхнего уровня: {list(j.keys())}")
            for top_key, section in j.items():
                if isinstance(section, dict):
                    print(f"  [{top_key}] → items count: {len(section.get('items', []))}")
                    for item in section.get('items', [])[:2]:
                        print(f"    kind={item.get('kind')}  keys={list(item.keys())}")
                        if item.get('kind') == 'field_list':
                            for f in item.get('fields', [])[:5]:
                                print(f"      label={f.get('label')!r}  value={f.get('value')!r}")

def load_versions_data() -> pd.DataFrame:
    """
    Аналог PG-запроса:
    contracts JOIN purchases ON reg_number
    LEFT JOIN contract_versions ON contract_id
    """
    query = """
    SELECT
        c.Id              AS contract_id,
        c.RegistryNumber  AS reg_number,
        c.PurchaseOrder   AS law,
        c.ContractPrice   AS contract_price_raw,
        p.NMCKMarket      AS initial_price,
        p.PublishedDate   AS published,
        COUNT(cv.id)      AS version_count
    FROM contract c
    JOIN purchase p ON c.purchase_id = p.Id
    LEFT JOIN contract_version cv ON cv.contract_id = c.Id
    GROUP BY c.Id, c.RegistryNumber, c.PurchaseOrder, c.ContractPrice,
             p.NMCKMarket, p.PublishedDate
    ORDER BY c.RegistryNumber
    """
    print("\n>>> Загрузка данных из SQLite...")
    try:
        df = read_sql(query)
        print(f"✓ Загружено {len(df)} контрактов")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return pd.DataFrame()
    return df


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['contract_price'] = df['contract_price_raw'].apply(clean_price_value)
    df['initial_price'] = pd.to_numeric(df['initial_price'], errors='coerce').replace(0, float('nan'))
    df['published_dt']   = pd.to_datetime(df['published'], format='%d.%m.%Y', errors='coerce')
    df['year']           = df['published_dt'].dt.year
    df['law']            = df['law'].fillna('').str.strip()

    # Дельта: итоговая цена контракта vs НМЦК
    df['delta']     = df['contract_price'] - df['initial_price']
    df['delta_pct'] = (df['delta'] / df['initial_price'] * 100).round(2)
    return df


def analyze_price_vs_nmck(df: pd.DataFrame):
    """Таблица 1. contract_price vs initial_price_amount (НМЦК)."""
    print(f"\n{'=' * 130}")
    print("ТАБЛИЦА 1. Сравнение цены контракта с НМЦК (initial_price_amount)")
    print(f"{'=' * 130}")

    df_v = df[df['contract_price'].notna() & df['initial_price'].notna()].copy()

    if df_v.empty:
        print("Нет данных с заполненным contract_price.")
        return df_v

    total = len(df_v)
    inc   = (df_v['delta'] > 0).sum()
    dec   = (df_v['delta'] < 0).sum()
    unch  = (df_v['delta'] == 0).sum()

    print(f"\n  Всего контрактов с ценой  : {total}")
    print(f"  Цена контракта > НМЦК     : {inc}  ({inc/total*100:.1f}%)")
    print(f"  Цена контракта < НМЦК     : {dec}  ({dec/total*100:.1f}%)")
    print(f"  Цена контракта == НМЦК    : {unch} ({unch/total*100:.1f}%)")
    print(f"  Средняя дельта, %         : {df_v['delta_pct'].mean():.2f}%")
    print(f"  Суммарный перерасход      : {fmt(df_v[df_v['delta']>0]['delta'].sum())} руб.")
    print(f"  Суммарная экономия        : {fmt(abs(df_v[df_v['delta']<0]['delta'].sum()))} руб.")

    print(f"\n{'Реестровый номер':<28} {'Закон':<8} {'Версий':>7} "
          f"{'НМЦК':>20} {'Цена контракта':>20} {'Δ руб.':>20} {'Δ %':>8}")
    print("-" * 130)

    top = df_v.reindex(df_v['delta'].abs().sort_values(ascending=False).index).head(30)
    for _, row in top.iterrows():
        sign = "↑" if row['delta'] > 0 else ("↓" if row['delta'] < 0 else "→")
        print(
            f"{row['reg_number']:<28} {row['law']:<8} {int(row['version_count']):>7} "
            f"{fmt(row['initial_price']):>20} {fmt(row['contract_price']):>20} "
            f"{sign}{fmt(abs(row['delta'])):>19} {row['delta_pct']:>7.1f}%"
        )
    print("-" * 130)
    return df_v


def analyze_by_law(df_v: pd.DataFrame):
    print(f"\n{'=' * 90}")
    print("ТАБЛИЦА 2. Сводная по законам: contract_price vs НМЦК")
    print(f"{'=' * 90}")

    # Диагностика: уникальные значения law
    print(f"\n  [DEBUG] Уникальные значения law: {df_v['law'].unique().tolist()}")

    for law in ['44-ФЗ', '223-ФЗ']:
        # Ищем точное совпадение вместо contains(без дефиса)
        sub = df_v[df_v['law'].str.strip() == law]

        # Фоллбэк: если точное совпадение не сработало — ищем по числу
        if sub.empty:
            num = law.split('-')[0]   # '44' или '223'
            sub = df_v[df_v['law'].str.contains(num, na=False)]

        if sub.empty:
            print(f"\n  {law}: нет данных")
            continue

        total = len(sub)
        inc   = (sub['delta'] > 0).sum()
        dec   = (sub['delta'] < 0).sum()
        unch  = (sub['delta'] == 0).sum()
        print(f"\n  {law}  (контрактов: {total})")
        print(f"  {'Цена выросла (> НМЦК)':<35}: {inc} ({inc/total*100:.1f}%)")
        print(f"  {'Цена упала   (< НМЦК)':<35}: {dec} ({dec/total*100:.1f}%)")
        print(f"  {'Цена равна НМЦК':<35}: {unch} ({unch/total*100:.1f}%)")
        print(f"  {'Средняя дельта %':<35}: {sub['delta_pct'].mean():.2f}%")
        print(f"  {'Суммарный перерасход':<35}: {fmt(sub[sub['delta']>0]['delta'].sum())} руб.")
        print(f"  {'Суммарная экономия':<35}: {fmt(abs(sub[sub['delta']<0]['delta'].sum()))} руб.")



def analyze_delta_distribution(df_v: pd.DataFrame):
    print(f"\n{'=' * 70}")
    print("ТАБЛИЦА 3. Распределение по диапазонам Δ% (contract_price vs НМЦК)")
    print(f"{'=' * 70}")

    bins   = [-float('inf'), -50, -20, -5, 0, 5, 20, 50, float('inf')]
    labels = ['< -50%', '-50% … -20%', '-20% … -5%', '-5% … 0%',
              '0% … +5%', '+5% … +20%', '+20% … +50%', '> +50%']
    df_v = df_v.copy()
    df_v['bin'] = pd.cut(df_v['delta_pct'], bins=bins, labels=labels)

    pivot = df_v.groupby(['bin', 'law'], observed=True)['reg_number'].count().unstack(fill_value=0)
    for col in ['44-ФЗ', '223-ФЗ']:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot['Итого'] = pivot.sum(axis=1)

    print(f"\n{'Диапазон':<20} {'44-ФЗ':>10} {'223-ФЗ':>10} {'Итого':>10}")
    print("-" * 55)
    for label in labels:
        if label not in pivot.index:
            continue
        row = pivot.loc[label]
        print(f"{label:<20} {int(row.get('44-ФЗ', 0)):>10} "
              f"{int(row.get('223-ФЗ', 0)):>10} {int(row['Итого']):>10}")
    print("-" * 55)
    print(f"{'Итого':<20} {int(pivot.get('44-ФЗ', pd.Series(dtype=int)).sum()):>10} "
          f"{int(pivot.get('223-ФЗ', pd.Series(dtype=int)).sum()):>10} "
          f"{int(pivot['Итого'].sum()):>10}")


def analyze_by_year(df_v: pd.DataFrame):
    print(f"\n{'=' * 70}")
    print("ТАБЛИЦА 4. Динамика по годам: среднее Δ% (contract_price vs НМЦК)")
    print(f"{'=' * 70}")

    yearly = df_v.groupby('year').agg(
        контрактов=('reg_number', 'count'),
        avg_pct=('delta_pct', 'mean'),
        sum_delta=('delta', 'sum'),
    ).reset_index()

    print(f"\n{'Год':<8} {'Контрактов':>12} {'Среднее Δ %':>14} {'Суммарная Δ, руб':>22}")
    print("-" * 60)
    for _, row in yearly.iterrows():
        print(f"{int(row['year']):<8} {int(row['контрактов']):>12} "
              f"{row['avg_pct']:>13.2f}% {fmt(row['sum_delta']):>22}")
    print("-" * 60)


def analyze_version_counts(df: pd.DataFrame):
    print(f"\n{'=' * 60}")
    print("ТАБЛИЦА 5. Распределение контрактов по количеству версий")
    print(f"{'=' * 60}")

    bins   = [0, 1, 2, 3, 5, 10, float('inf')]
    labels = ['1', '2', '3', '4–5', '6–10', '> 10']
    df = df.copy()
    df['bin'] = pd.cut(df['version_count'], bins=bins, labels=labels)
    summary = df.groupby('bin', observed=True)['reg_number'].count()

    print(f"\n{'Кол-во версий':<15} {'Контрактов':>12}")
    print("-" * 30)
    for label, cnt in summary.items():
        print(f"{label:<15} {cnt:>12}")
    print("-" * 30)
    print(f"{'Итого':<15} {summary.sum():>12}")
    print(f"\n  Среднее кол-во версий : {df['version_count'].mean():.2f}")
    print(f"  Максимум версий       : {int(df['version_count'].max())}")





#---------------изменениея контракта-----------------
def extract_contract_items_new(json_data) -> list[dict]:
    if not isinstance(json_data, dict):
        return []
    extracted = []
    try:
        for item in json_data.get('объекты_закупки', {}).get('items', []):
            if item.get('kind') != 'table':
                continue
            for row in item.get('table', {}).get('rows', []):
                ktru_raw = row.get('ktru')
                price    = row.get('price')
                qty      = row.get('quantity') or row.get('qty') or row.get('количество')
                ktru_clean = str(ktru_raw).replace('\n', ' ').strip() if ktru_raw else None
                price_val  = clean_price_value(price)
                if ktru_clean or price_val is not None:
                    extracted.append({
                        'ktru':  ktru_clean,
                        'price': price_val,
                        'qty':   clean_price_value(qty),
                    })
    except Exception:
        pass
    return extracted


# ─── Загрузка версий с payment_targets_json ────────────────

def load_versions_payment() -> pd.DataFrame:
    query = """
    SELECT
        cv.id              AS version_id,
        cv.contract_id,
        cv.version         AS version_label,
        c.RegistryNumber   AS reg_number,
        c.PurchaseOrder    AS law,
        p.NMCKMarket       AS initial_price,
        p.PublishedDate    AS published,
        cv.payment_targets_json,
        COUNT(cv.id) OVER (
            PARTITION BY cv.contract_id
        )                  AS version_total
    FROM contract_version cv
    JOIN contract c ON cv.contract_id = c.Id
    JOIN purchase p ON c.purchase_id = p.Id
    WHERE cv.payment_targets_json IS NOT NULL
    ORDER BY c.RegistryNumber, cv.id
    """
    print("\n>>> Загрузка версий с payment_targets_json из SQLite...")
    try:
        df = read_sql(query)
        # SQLite не парсит JSON автоматически — парсим вручную
        df['payment_targets_json'] = df['payment_targets_json'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        print(f"✓ Загружено {len(df)} версий | контрактов: {df['reg_number'].nunique()}")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return pd.DataFrame()
    return df

def parse_version_label(label: str) -> tuple[int, pd.Timestamp | None]:
    """
    '№ 3890800303219000006 (Версия № 3 от 15.04.2021, действующая версия)'
    → (3, Timestamp('2021-04-15'))

    Возвращает (version_num, date) для сортировки.
    Если не удалось разобрать — возвращает (999, None).
    """
    if not label or not isinstance(label, str):
        return 999, None

    # Номер версии: "Версия № 3"
    num_match = re.search(r'Версия\s*№\s*(\d+)', label, re.IGNORECASE)
    version_num = int(num_match.group(1)) if num_match else 999

    # Дата: "от 15.04.2021"
    date_match = re.search(r'от\s+(\d{2}\.\d{2}\.\d{4})', label)
    version_date = None
    if date_match:
        try:
            version_date = pd.to_datetime(date_match.group(1), format='%d.%m.%Y')
        except Exception:
            pass

    return version_num, version_date
# ─── Разворачиваем позиции ─────────────────────────────────

def explode_items(df: pd.DataFrame) -> pd.DataFrame:
    # Парсим номер и дату версии
    parsed = df['version_label'].apply(parse_version_label)
    df = df.copy()
    df['version_num']  = parsed.apply(lambda x: x[0])
    df['version_date'] = parsed.apply(lambda x: x[1])

    # Для сортировки: сначала по дате, потом по номеру версии
    df['version_sort'] = df['version_date'].apply(
        lambda d: d.timestamp() if pd.notna(d) else float('inf')
    )

    records = []
    for _, row in df.iterrows():
        items = extract_contract_items_new(row['payment_targets_json'])
        for it in items:
            records.append({
                'version_id':    row['version_id'],
                'version_num':   row['version_num'],
                'version_date':  row['version_date'],
                'version_sort':  row['version_sort'],
                'version_label': row['version_label'],
                'contract_id':   row['contract_id'],
                'reg_number':    row['reg_number'],
                'law':           row['law'],
                'initial_price': row['initial_price'],
                'version_total': row['version_total'],
                'ktru':          it['ktru'],
                'price':         it['price'],
                'qty':           it['qty'],
            })

    result = pd.DataFrame(records)
    print(f"✓ Извлечено {len(result)} позиций | контрактов: {result['reg_number'].nunique()}")
    return result



# ─── Анализ 1: дельта цены позиции (v1 → vN) ──────────────
def diagnose_version_order(engine, reg_number: str):
    """Печатает все версии контракта с их ID и ценой позиций."""
    query = f"""
    SELECT
        cv.id               AS version_id,
        cv.contract_url,
        ROW_NUMBER() OVER (PARTITION BY cv.contract_id ORDER BY cv.id)     AS seq_asc,
        ROW_NUMBER() OVER (PARTITION BY cv.contract_id ORDER BY cv.id DESC) AS seq_desc
    FROM public.contract_versions cv
    JOIN public.contracts c ON cv.contract_id = c.id
    WHERE c.reg_number = '{reg_number}'
      AND cv.payment_targets_json IS NOT NULL
    ORDER BY cv.id
    """
    df = pd.read_sql_query(query, engine)
    print(df.to_string(index=False))

def analyze_item_price_changes(items_df: pd.DataFrame):
    print(f"\n{'=' * 140}")
    print("ТАБЛИЦА 6. Изменение цены позиций КТРУ: первая → последняя версия контракта")
    print(f"{'=' * 140}")

    df = items_df[items_df['price'].notna() & items_df['ktru'].notna()].copy()
    if df.empty:
        print("Нет позиций с заполненными КТРУ и ценой.")
        return None

    key = ['reg_number', 'ktru']

    # ── сортируем по version_sort (дата) внутри каждой группы ──
    df = df.sort_values(['reg_number', 'ktru', 'version_sort'])

    min_sort = df.groupby(key)['version_sort'].transform('min')
    max_sort = df.groupby(key)['version_sort'].transform('max')

    # v1 — самая ранняя дата версии, vN — самая поздняя
    price_v1 = (
        df[df['version_sort'] == min_sort]
        .groupby(key)['price']
        .mean()
        .rename('price_v1')
    )

    last_rows = (
        df[df['version_sort'] == max_sort]
        .groupby(key)
        .last()[['price', 'version_total', 'law', 'initial_price', 'version_label']]
        .rename(columns={'price': 'price_vN', 'version_label': 'version_last_label'})
    )

    # v1 label для отображения
    first_label = (
        df[df['version_sort'] == min_sort]
        .groupby(key)['version_label']
        .first()
        .rename('version_first_label')
    )

    merged = last_rows.join(price_v1).join(first_label).reset_index()

    # Пропускаем если v1 == vN (единственная версия)
    merged = merged[merged['price_v1'] != merged['price_vN']].copy()

    merged['delta']     = merged['price_vN'] - merged['price_v1']
    merged['delta_pct'] = (merged['delta'] / merged['price_v1'] * 100).round(2)

    total_all = len(price_v1)
    total     = len(merged)
    inc       = (merged['delta'] > 0).sum()
    dec       = (merged['delta'] < 0).sum()

    # ── Сводка ──
    print(f"\n  Всего позиций (контракт × КТРУ)         : {total_all}")
    print(f"  Из них с изменением цены                 : {total}")
    print(f"  Цена выросла  (vN > v1)                  : {inc}  ({inc/total*100:.1f}%)" if total else "")
    print(f"  Цена упала    (vN < v1)                  : {dec}  ({dec/total*100:.1f}%)" if total else "")

    full = merged.reindex(merged['delta'].abs().sort_values(ascending=False).index)

    print(f"\n{'Реестровый номер':<28} {'КТРУ':<35} {'Версий':>6} "
          f"{'v1 (ранняя дата)':>16} {'vN (поздняя дата)':>17} "
          f"{'Цена v1':>18} {'Цена vN':>18} {'Δ руб.':>18} {'Δ %':>8}")
    print("-" * 170)

    for _, row in full.iterrows():
        sign = "↑" if row['delta'] > 0 else "↓"
        ktru_short = (str(row['ktru'])[:33] + '..') if len(str(row['ktru'])) > 35 else row['ktru']

        # Извлекаем краткую метку версии "№X от ДД.ММ.ГГГГ"
        def short_ver(label):
            if not label:
                return '?'
            m = re.search(r'Версия\s*№\s*(\d+)\s*от\s*(\d{2}\.\d{2}\.\d{4})', str(label), re.I)
            return f"v{m.group(1)} {m.group(2)}" if m else str(label)[:15]

        print(
            f"{row['reg_number']:<28} {str(ktru_short):<35} {int(row['version_total']):>6} "
            f"{short_ver(row['version_first_label']):>16} {short_ver(row['version_last_label']):>17} "
            f"{fmt(row['price_v1']):>18} {fmt(row['price_vN']):>18} "
            f"{sign}{fmt(abs(row['delta'])):>17} {row['delta_pct']:>7.1f}%"
        )

    print("-" * 170)
    print(f"  Строк выведено: {len(full)}")
    return merged

# ─── Анализ 2: топ КТРУ по суммарному изменению ────────────

def analyze_top_ktru_by_delta(merged: pd.DataFrame):
    print(f"\n{'=' * 90}")
    print("ТАБЛИЦА 7. Топ-20 КТРУ по суммарному росту цены (все контракты)")
    print(f"{'=' * 90}")

    grp = (merged.groupby('ktru')['delta']
                 .agg(['count', 'sum', 'mean'])
                 .sort_values('sum', ascending=False))

    print(f"\n{'КТРУ':<50} {'Контрактов':>10} {'Σ Δ руб.':>20} {'Avg Δ руб.':>18}")
    print("-" * 100)

    for label, row in grp.head(20).iterrows():
        ktru_short = (str(label)[:48] + '..') if len(str(label)) > 50 else str(label)
        sign = "↑" if row['sum'] > 0 else "↓"
        print(f"{ktru_short:<50} {int(row['count']):>10} "
              f"{sign}{fmt(abs(row['sum'])):>19} {fmt(row['mean']):>18}")
    print("-" * 100)

    # Топ-20 по снижению
    print(f"\n{'КТРУ':<50} {'Контрактов':>10} {'Σ Δ руб.':>20} {'Avg Δ руб.':>18}")
    print("Топ-20 КТРУ по суммарному СНИЖЕНИЮ цены:")
    print("-" * 100)
    for label, row in grp.tail(20).sort_values('sum').iterrows():
        ktru_short = (str(label)[:48] + '..') if len(str(label)) > 50 else str(label)
        print(f"{ktru_short:<50} {int(row['count']):>10} "
              f"↓{fmt(abs(row['sum'])):>19} {fmt(abs(row['mean'])):>18}")
    print("-" * 100)


# ─── Анализ 3: распределение Δ% позиций ───────────────────

def analyze_item_delta_distribution(merged: pd.DataFrame):
    print(f"\n{'=' * 60}")
    print("ТАБЛИЦА 8. Распределение позиций по диапазонам Δ%")
    print(f"{'=' * 60}")

    bins   = [-float('inf'), -50, -20, -5, 0, 5, 20, 50, float('inf')]
    labels = ['< -50%', '-50%…-20%', '-20%…-5%', '-5%…0%',
              '0%…+5%', '+5%…+20%', '+20%…+50%', '> +50%']

    merged = merged.copy()
    merged['bin'] = pd.cut(merged['delta_pct'], bins=bins, labels=labels)
    summary = merged.groupby('bin', observed=True)['reg_number'].count()

    print(f"\n{'Диапазон':<15} {'Позиций':>10} {'%':>8}")
    print("-" * 36)
    total = summary.sum()
    for label, cnt in summary.items():
        print(f"{label:<15} {cnt:>10} {cnt/total*100:>7.1f}%")
    print("-" * 36)
    print(f"{'Итого':<15} {total:>10}")


# ─── Главный блок (добавить в main()) ─────────────────────

def analyze_payment_targets(engine):
    df_raw   = load_versions_payment(engine)
    if df_raw.empty:
        return

    items_df = explode_items(df_raw)
    if items_df.empty:
        print("Нет позиций для анализа — проверьте структуру payment_targets_json")
        # Диагностика:
        sample = df_raw['payment_targets_json'].dropna().iloc[0] if not df_raw.empty else {}
        if isinstance(sample, dict):
            print(f"  Ключи верхнего уровня JSON: {list(sample.keys())}")
        return

    merged = analyze_item_price_changes(items_df)
    if merged is not None and not merged.empty:
        analyze_top_ktru_by_delta(merged)
        analyze_item_delta_distribution(merged)


def extract_execution_stages(process_json) -> list[dict]:
    """Извлекает этапы исполнения контракта."""
    if not isinstance(process_json, dict):
        return []
    records = []
    try:
        for item in process_json.get('исполнение_контракта', {}).get('items', []):
            if item.get('kind') != 'table':
                continue
            for row in item.get('table', {}).get('rows', []):
                records.append({
                    'stage':            row.get('ЭТАП КОНТРАКТА', ''),
                    'completed':        row.get('ИСПОЛНЕНИЕ ЗАВЕРШЕНО', ''),
                    'paid_raw':         row.get('ФАКТИЧЕСКИ ОПЛАЧЕНО, ₽'),
                    'obligated_raw':    row.get('СТОИМОСТЬ ИСПОЛНЕННЫХ ОБЯЗАТЕЛЬСТВ, ₽'),
                    'has_penalty':      row.get('НЕУСТОЙКИ (ШТРАФЫ, ПЕНИ)', 'Нет'),
                })
    except Exception:
        pass
    return records


def extract_penalties(process_json) -> list[dict]:
    if not isinstance(process_json, dict):
        return []
    records = []
    try:
        for item in process_json.get(
            'информация_о_начислении_неустоек_штрафов_пеней', {}
        ).get('items', []):
            if item.get('kind') != 'table':
                continue
            for row in item.get('table', {}).get('rows', []):
                requirement_raw = row.get('ТРЕБОВАНИЕ', '') or ''
                code_match = re.match(r'^(\d+)', requirement_raw.strip())
                req_code = code_match.group(1) if code_match else 'прочее'

                # ПРИЧИНА НАЧИСЛЕНИЯ содержит организацию (ИНН)
                # ПЛАТЕЛЬЩИК в данных пустой — используем ПРИЧИНА НАЧИСЛЕНИЯ
                payer_raw = row.get('ПРИЧИНА НАЧИСЛЕНИЯ', '') or ''
                inn_match = re.search(r'ИНН[:\s]+(\d{10,12})', payer_raw)
                inn = inn_match.group(1) if inn_match else None

                # НАЧИСЛЕНО, ₽ содержит текст документа ("Требование об уплате пеней №...")
                # Пытаемся достать сумму из текста: "...пеней №4440 от 10.10.2019"
                # Реальная сумма — в поле ОПЛАЧЕНО, ₽
                nachisleno_raw = row.get('НАЧИСЛЕНО, ₽', '') or ''
                oplacheno_raw  = row.get('ОПЛАЧЕНО, ₽',  '') or ''

                # Пробуем распарсить НАЧИСЛЕНО как число, иначе None
                charged_val = clean_price_value(nachisleno_raw)

                # Если НАЧИСЛЕНО не число — это текст документа,
                # тогда charged = paid (нет отдельной суммы начисления)
                paid_val = clean_price_value(oplacheno_raw)

                records.append({
                    'requirement_code': req_code,
                    'requirement_text': requirement_raw[:80],
                    'payer':            payer_raw[:100],
                    'inn':              inn,
                    'charged_doc':      nachisleno_raw[:80],   # текст документа
                    'charged':          charged_val,            # число если было
                    'paid':             paid_val,               # фактически оплачено
                })
    except Exception:
        pass
    return records

# ─── Загрузка ─────────────────────────────────────────────

def load_process_info() -> pd.DataFrame:
    query = """
    SELECT
        cv.id              AS version_id,
        cv.contract_id,
        cv.version         AS version_label,
        cv.process_info_json,
        c.RegistryNumber   AS reg_number,
        c.PurchaseOrder    AS law,
        p.NMCKMarket       AS initial_price,
        p.PublishedDate    AS published,
        COUNT(cv.id) OVER (
            PARTITION BY cv.contract_id
        )                  AS version_total
    FROM contract_version cv
    JOIN contract c ON cv.contract_id = c.Id
    JOIN purchase p ON c.purchase_id = p.Id
    WHERE cv.process_info_json IS NOT NULL
    ORDER BY c.RegistryNumber, cv.id
    """
    print("\n>>> Загрузка process_info_json из SQLite...")
    try:
        df = read_sql(query)
        df['process_info_json'] = df['process_info_json'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        print(f"✓ Загружено {len(df)} версий | контрактов: {df['reg_number'].nunique()}")
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return pd.DataFrame()
    return df



# ─── Анализ 2: неустойки ──────────────────────────────────

def analyze_penalties(df: pd.DataFrame):
    print(f"\n{'=' * 100}")
    print("ТАБЛИЦА 10. Неустойки (штрафы, пени): начислено vs оплачено")
    print(f"{'=' * 100}")

    records = []
    for _, row in df.iterrows():
        for p in extract_penalties(row['process_info_json']):
            p['reg_number'] = row['reg_number']
            p['law']        = row['law']
            records.append(p)

    if not records:
        print("Нет данных о неустойках.")
        return

    p = pd.DataFrame(records)

    # charged может быть None если поле содержало текст документа
    has_charged     = p['charged'].notna().sum()
    total_charged   = p['charged'].sum() if has_charged > 0 else None
    total_paid      = p['paid'].sum()
    contracts_cnt   = p['reg_number'].nunique()

    print(f"\n  Контрактов с неустойками         : {contracts_cnt}")
    print(f"  Всего записей неустоек           : {len(p)}")

    if has_charged > 0:
        print(f"  Суммарно начислено               : {fmt(total_charged)} руб.")
        print(f"  Суммарно оплачено                : {fmt(total_paid)} руб.")
        print(f"  Долг (начислено − оплачено)      : {fmt(total_charged - total_paid)} руб.")
    else:
        # НАЧИСЛЕНО содержит только текст документов — показываем только ОПЛАЧЕНО
        print(f"  [!] Поле НАЧИСЛЕНО содержит тексты документов, числа не найдены")
        print(f"  Суммарно оплачено пеней          : {fmt(total_paid)} руб.")

    # Топ причин нарушений по количеству и сумме оплаченного
    print(f"\n  --- Топ причин нарушений (по сумме оплаченных пеней) ---")
    req_grp = (p.groupby('requirement_text')['paid']
                .agg(['count', 'sum'])
                .sort_values('sum', ascending=False)
                .head(10))
    print(f"\n{'Причина':<85} {'Кол-во':>7} {'Σ оплачено':>18}")
    print("-" * 115)
    for label, row in req_grp.iterrows():
        short = (str(label)[:83] + '..') if len(str(label)) > 85 else str(label)
        print(f"{short:<85} {int(row['count']):>7} {fmt(row['sum']):>18}")

    # Топ плательщиков
    print(f"\n  --- Топ плательщиков по сумме оплаченных пеней ---")
    pay_grp = (p[p['inn'].notna()]
               .groupby(['payer', 'inn'])['paid']
               .agg(['count', 'sum'])
               .sort_values('sum', ascending=False)
               .head(15))
    print(f"\n{'Организация':<80} {'ИНН':>13} {'Записей':>7} {'Σ оплачено':>18}")
    print("-" * 125)
    for (payer, inn), row in pay_grp.iterrows():
        short = (str(payer)[:78] + '..') if len(str(payer)) > 80 else str(payer)
        print(f"{short:<80} {inn:>13} {int(row['count']):>7} {fmt(row['sum']):>18}")
    print("-" * 125)


def analyze_execution_stages(df: pd.DataFrame):
    print(f"\n{'=' * 100}")
    print("ТАБЛИЦА 9. Исполнение контракта: оплачено vs обязательства по этапам")
    print(f"{'=' * 100}")

    records = []
    for _, row in df.iterrows():
        for stage in extract_execution_stages(row['process_info_json']):
            stage['reg_number'] = row['reg_number']
            stage['law']        = row['law']
            records.append(stage)

    if not records:
        print("Нет данных об этапах исполнения.")
        return

    s = pd.DataFrame(records)
    s['paid']       = s['paid_raw'].apply(clean_price_value)
    s['obligated']  = s['obligated_raw'].apply(clean_price_value)
    s['delta']      = s['paid'] - s['obligated']

    # FutureWarning fix: явное приведение к bool
    s['completed'] = (
        s['completed'].str.strip().str.lower()
        .isin(['да', 'yes'])
    )
    s['has_penalty'] = (
        s['has_penalty'].str.strip().str.lower()
        .isin(['да', 'yes'])
    )

    total_stages    = len(s)
    completed       = int(s['completed'].sum())
    with_penalty    = int(s['has_penalty'].sum())
    total_paid      = s['paid'].sum()
    total_obligated = s['obligated'].sum()

    print(f"\n  Всего этапов                     : {total_stages}")
    print(f"  Завершено (ИСПОЛНЕНИЕ = Да)      : {completed} ({completed/total_stages*100:.1f}%)")
    print(f"  С неустойкой на этапе            : {with_penalty} ({with_penalty/total_stages*100:.1f}%)")
    print(f"  Суммарно обязательств            : {fmt(total_obligated)} руб.")
    print(f"  Суммарно оплачено                : {fmt(total_paid)} руб.")
    print(f"  Разница (оплачено − обяз.)       : {fmt(total_paid - total_obligated)} руб.")

    print(f"\n{'Закон':<10} {'Этапов':>8} {'Завершено':>10} {'С пенями':>10} "
          f"{'Σ обяз., руб.':>22} {'Σ оплачено, руб.':>22}")
    print("-" * 90)
    for law, g in s.groupby('law'):
        print(
            f"{law:<10} {len(g):>8} {int(g['completed'].sum()):>10} "
            f"{int(g['has_penalty'].sum()):>10} "
            f"{fmt(g['obligated'].sum()):>22} {fmt(g['paid'].sum()):>22}"
        )
    print("-" * 90)

def analyze_process_info(engine):
    df = load_process_info(engine)
    if df.empty:
        return
    analyze_execution_stages(df)
    analyze_penalties(df)
def main():
    # Проверка подключения
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        print("✓ Подключение к SQLite успешно")
        print(f"  БД: {DB_PATH}")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return

    df_raw = load_versions_data()
    if df_raw.empty:
        return

    df = prepare_df(df_raw)

    # df_v = analyze_price_vs_nmck(df)
    # if df_v is not None and not df_v.empty:
    #     analyze_by_law(df_v)
    #     analyze_delta_distribution(df_v)
    #     analyze_by_year(df_v)

    # analyze_version_counts(df)
    # analyze_payment_targets()        # ← без engine
    analyze_process_info()             # ← без engine


if __name__ == "__main__":
    main()
