"""
analyze_purchases_peewee.py
Анализ закупок на основе Peewee-моделей (SQLite).
Полный аналог analyze_purchases.py, адаптированный под ORM.
"""

import re
import json
import pandas as pd

from smtuIdle.BD.initialize_db import db
from smtuIdle.BD.models import *



db_path = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

    # 2. ПЕРЕИНИЦИАЛИЗИРУЕМ импортированную базу правильным путем!
db.init(db_path)

    # 3. Подключаемся
db.connect(reuse_if_open=True)

# ─── Константы ───────────────────────────────────────────────────────────────
LAWS = ("44-ФЗ", "223-ФЗ")

PRICE_ORDER = [
    "до 400 тыс.", "400 тыс. — 1 млн", "1 — 5 млн",
    "5 — 20 млн", "20 — 100 млн", "100 млн — 1 млрд",
    "более 1 млрд", "Нет цены",
]

PLACING_WAY_ORDER = [
    "Электронный аукцион",
    "Открытый конкурс в электронной форме",
    "Закупка у единственного поставщика",
    "Прочие",
]

PLACING_WAY_MAP = {
    "электронный аукцион":        "Электронный аукцион",
    "открытый конкурс":           "Открытый конкурс в электронной форме",
    "единственного поставщика":   "Закупка у единственного поставщика",
    "единственным поставщиком":   "Закупка у единственного поставщика",
}

STOP_WORDS = {"", "1"}

# ─────────────────────────────────────────────────────────────────────────────
#  Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json(value):
    """TEXT → dict/list. Если уже dict/list — возвращает как есть."""
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            pass
    return None


def fmt_num(x):
    """Число → строка с разделителями тысяч."""
    if pd.isna(x):
        return "-"
    if isinstance(x, (int, float)):
        if x == 0:
            return "0"
        if x % 1 == 0:
            return "{:,.0f}".format(x).replace(",", " ")
        return "{:,.2f}".format(x).replace(",", " ")
    return x


def fmt_nonzero(x):
    """0 → '-', иначе fmt_num."""
    return "-" if x == 0 else fmt_num(x)


def _strip_prefix(name: str) -> str:
    return name[3:] if name and name[0].isdigit() else name


def clean_price_value(value):
    if pd.isna(value):
        return None
    try:
        s = str(value).replace(" ", "").replace(",", ".").replace("₽", "")
        return float(s)
    except (ValueError, TypeError):
        return None


def clean_okpd2(code):
    if not code:
        return None
    m = re.match(r"^([\d.]+)", str(code).strip())
    return m.group(1).strip(".") if m else str(code).strip()


def categorize_price(price) -> str:
    if pd.isna(price):
        return "Нет цены"
    p = float(price)
    if p < 400_000:        return "до 400 тыс."
    if p < 1_000_000:      return "400 тыс. — 1 млн"
    if p < 5_000_000:      return "1 — 5 млн"
    if p < 20_000_000:     return "5 — 20 млн"
    if p < 100_000_000:    return "20 — 100 млн"
    if p < 1_000_000_000:  return "100 млн — 1 млрд"
    return "более 1 млрд"


def map_placing_way(way) -> str:
    if pd.isna(way):
        return "Прочие"
    w = str(way).strip().lower()
    for keyword, label in PLACING_WAY_MAP.items():
        if keyword in w:
            return label
    return "Прочие"

# ─────────────────────────────────────────────────────────────────────────────
#  Генераторы строк из JSON-полей (структура не изменилась)
# ─────────────────────────────────────────────────────────────────────────────

def _iter_44_table_rows(raw_json):
    """
    Итерирует строки таблиц из common_info_json (44-ФЗ).
    Структура: информация_об_объекте_закупки -> items -> kind==table -> table -> rows
    """
    data = _parse_json(raw_json)
    if not isinstance(data, dict):
        return
    info = data.get("информация_об_объекте_закупки", {})
    for item in info.get("items", []):
        if item.get("kind") == "table":
            yield from item.get("table", {}).get("rows", [])


def _iter_223_table_rows(raw_json):
    """
    Итерирует строки таблиц из lots_json (223-ФЗ).
    Структура: {ключ} -> items -> parsed_table -> rows
    """
    data = _parse_json(raw_json)
    if not isinstance(data, dict):
        return
    for section in data.values():
        if isinstance(section, dict):
            for item in section.get("items", []):
                yield from item.get("parsed_table", {}).get("rows", [])

# ─────────────────────────────────────────────────────────────────────────────
#  Вывод таблиц
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame, column_name: str, title: str, limit=None):
    print(f"\n{'=' * 60}")
    print(f"СВОДНАЯ ТАБЛИЦА: {title}")
    print(f"{'=' * 60}")
    if df is None or df.empty:
        print("Нет данных для анализа")
        return
    counts = df[column_name].value_counts()
    items = counts.head(limit) if limit else counts
    for cat, cnt in items.items():
        s = str(cat).strip()
        short = (s[:50] + "...") if len(s) > 50 else s
        print(f"{short:<50} {cnt:>8}")
    print(f"{'-' * 60}")
    if limit and len(counts) > limit:
        print(f"{'... и еще ' + str(len(counts) - limit) + ' строк ...':<50}")
    print(f"{'ИТОГО записей':<50} {len(df):>8}")


def print_summary_with_sum(df: pd.DataFrame, group_col: str, value_col: str,
                           title: str, limit=None):
    print(f"\n{'=' * 80}")
    print(f"СВОДНАЯ ТАБЛИЦА: {title}")
    print(f"{'=' * 80}")
    if df is None or df.empty:
        print("Нет данных для анализа")
        return
    grouped = (
        df.groupby(group_col)[value_col]
        .agg(["count", "sum"])
        .sort_values("sum", ascending=False)
    )
    if limit:
        grouped = grouped.head(limit)
    print(f"{'Категория':<50} {'Кол-во':>8} {'Сумма, руб':>20}")
    print("-" * 80)
    for idx, row in grouped.iterrows():
        s = str(idx).strip()
        short = (s[:50] + "...") if len(s) > 50 else s
        print(f"{short:<50} {int(row['count']):>8} {fmt_nonzero(row['sum']):>20}")
    print("-" * 80)
    if limit and len(grouped) >= limit:
        print(f"{'... и еще строк ...':<50}")
    print(f"{'ИТОГО':<50} {int(grouped['count'].sum()):>8} {fmt_num(grouped['sum'].sum()):>20}")


def build_count_sum_pivots(df: pd.DataFrame, row_col: str, row_order=None):
    grouped = df.groupby([row_col, "law"])["price"].agg(["count", "sum"])
    p_cnt = grouped["count"].unstack(fill_value=0)
    p_sum = grouped["sum"].unstack(fill_value=0)

    for col in LAWS:
        if col not in p_cnt.columns:
            p_cnt[col] = 0
        if col not in p_sum.columns:
            p_sum[col] = 0

    p_cnt = p_cnt[list(LAWS)]
    p_sum = p_sum[list(LAWS)]

    if row_order:
        p_cnt = p_cnt.reindex(row_order).fillna(0).astype(int)
        p_sum = p_sum.reindex(row_order).fillna(0)

    p_cnt["Всего"] = p_cnt.sum(axis=1)
    p_sum["Всего"] = p_sum.sum(axis=1)
    p_cnt.loc["Общий итог"] = p_cnt.sum()
    p_sum.loc["Общий итог"] = p_sum.sum()

    return p_cnt, p_sum


def print_count_sum_table(title: str, p_cnt: pd.DataFrame, p_sum: pd.DataFrame,
                          row_label_width=45):
    W = row_label_width
    print(f"\n{'=' * 120}")
    print(title)
    print(f"{'=' * 120}")
    print(f"{'':^{W}} {'Показатель':<15} {'44-ФЗ':>15} {'223-ФЗ':>15} {'Всего':>15}")
    print("-" * 120)

    data_rows = [r for r in p_cnt.index if r != "Общий итог"]
    all_rows = data_rows + ["Общий итог"]
    for i, row in enumerate(all_rows):
        if row == "Общий итог":
            print("-" * 120)
        c44  = int(p_cnt.loc[row, "44-ФЗ"])
        c223 = int(p_cnt.loc[row, "223-ФЗ"])
        ctot = int(p_cnt.loc[row, "Всего"])
        print(
            f"{str(row):<{W}} {'кол-во':<15} "
            f"{(str(c44) if c44 else '-'):>15} "
            f"{(str(c223) if c223 else '-'):>15} "
            f"{(str(ctot) if ctot else '-'):>15}"
        )
        s44  = p_sum.loc[row, "44-ФЗ"]
        s223 = p_sum.loc[row, "223-ФЗ"]
        stot = p_sum.loc[row, "Всего"]
        print(
            f"{'':^{W}} {'сумма, руб':<15} "
            f"{fmt_nonzero(s44):>15} "
            f"{fmt_nonzero(s223):>15} "
            f"{fmt_nonzero(stot):>15}"
        )
    print("-" * 120)

# ─────────────────────────────────────────────────────────────────────────────
#  Загрузка данных через Peewee (вся БД, без фильтра по дате)
# ─────────────────────────────────────────────────────────────────────────────

def _load_purchases(min_price: float = 100_000_000) -> pd.DataFrame:
    """
    Загружает ВСЕ закупки с НМЦК >= min_price.
    JSON-поля common_info_json и lots_json включены напрямую.
    """
    db.connect(reuse_if_open=True)
    query = (
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PurchaseName,
            Purchase.PurchaseOrder,
            Purchase.ProcurementStage,
            Purchase.ProcurementMethod,
            Purchase.CustomerName,
            Purchase.InitialMaxContractPrice,
            Purchase.PlacementDate,
            Purchase.common_info_json,
            Purchase.lots_json,
        )
        .where(Purchase.InitialMaxContractPrice >= min_price)
        .namedtuples()
    )
    rows = list(query)
    db.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "RegistryNumber":          "reg_number",
        "PurchaseName":            "object_name",
        "PurchaseOrder":           "law",
        "ProcurementStage":        "status",
        "ProcurementMethod":       "placing_way",
        "CustomerName":            "customer_name",
        "InitialMaxContractPrice": "initial_price_amount",
        "PlacementDate":           "published",
    })

    # JSON-поля хранятся как TEXT в SQLite — декодируем сразу
    df["common_info_json"] = df["common_info_json"].apply(_parse_json)
    df["lots_json"]        = df["lots_json"].apply(_parse_json)

    df["price"] = pd.to_numeric(df["initial_price_amount"], errors="coerce").fillna(0)
    df["category"] = df["price"].apply(categorize_price)
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce")
    df["year"] = df["published_dt"].dt.year
    df["placing_way_cat"] = df["placing_way"].apply(map_placing_way)
    df["price_category_simple"] = pd.Categorical(
        df["price"].apply(categorize_price), categories=PRICE_ORDER, ordered=True
    )
    return df


def _load_contracts(min_price: float = 20_000_000) -> pd.DataFrame:
    """
    Загружает контракты, JOIN с Purchase по RegistryNumber.
    Вся БД без ограничения по дате.
    """
    db.connect(reuse_if_open=True)
    # JOIN вручную через подзапрос: выбираем reg_number закупок с нужной ценой
    eligible = (
        Purchase
        .select(Purchase.RegistryNumber)
        .where(Purchase.InitialMaxContractPrice >= min_price)
    )
    eligible_nums = {r.RegistryNumber for r in eligible}

    query = (
        Contract
        .select(
            Contract.Id,
            Contract.RegistryNumber,
            Contract.ContractPrice,
            Contract.payment_targets_json,
        )
        .where(Contract.RegistryNumber.in_(eligible_nums))
        .namedtuples()
    )
    rows = list(query)
    db.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Подтягиваем поля Purchase по RegistryNumber
    db.connect(reuse_if_open=True)
    purchases_map = {
        p.RegistryNumber: {"law": p.PurchaseOrder, "customer_name": p.CustomerName}
        for p in Purchase.select(
            Purchase.RegistryNumber, Purchase.PurchaseOrder, Purchase.CustomerName
        ).where(Purchase.RegistryNumber.in_(set(df["RegistryNumber"].tolist())))
    }
    db.close()

    df["law"]           = df["RegistryNumber"].map(lambda x: purchases_map.get(x, {}).get("law"))
    df["customer_name"] = df["RegistryNumber"].map(lambda x: purchases_map.get(x, {}).get("customer_name"))
    df["price"]         = pd.to_numeric(df["ContractPrice"], errors="coerce").fillna(0)
    df["payment_targets_json"] = df["payment_targets_json"].apply(_parse_json)
    return df


def _load_suppliers(min_price: float = 100_000_000) -> pd.DataFrame:
    """
    Загружает поставщиков через цепочку:
    Supplier -> Contract.RegistryNumber -> Purchase.RegistryNumber (фильтр по цене).
    """
    db.connect(reuse_if_open=True)
    eligible = {
        r.RegistryNumber
        for r in Purchase.select(Purchase.RegistryNumber)
        .where(Purchase.InitialMaxContractPrice >= min_price)
    }
    eligible_contracts = {
        r.Id
        for r in Contract.select(Contract.Id)
        .where(Contract.RegistryNumber.in_(eligible))
    }
    query = (
        Supplier
        .select(Supplier.organization)
        .where(Supplier.contract_id.in_(eligible_contracts))
        .namedtuples()
    )
    rows = list(query)
    db.close()
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────────────────────
#  Извлечение ОКПД2 из JSON-полей закупки
# ─────────────────────────────────────────────────────────────────────────────

def extract_okpd2_items(row: dict) -> list:
    """
    44-ФЗ: парсит common_info_json
      информация_об_объекте_закупки -> items -> kind==table -> table -> rows
      Ключи: КОД ПОЗИЦИИ, СТОИМОСТЬ, ₽

    223-ФЗ: парсит lots_json
      {любой ключ} -> items -> parsed_table -> rows
      Ключи: КЛАССИФИКАЦИЯ ПО ОКПД2, СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА
    """
    law        = str(row.get("law", ""))
    reg_number = str(row.get("reg_number", ""))
    object_name = str(row.get("object_name", "")).replace("\n", " ").strip()
    items = []

    if "44" in law:
        try:
            for r in _iter_44_table_rows(row.get("common_info_json")):
                code = r.get("КОД ПОЗИЦИИ")
                cost = r.get("СТОИМОСТЬ, ₽")
                if code and str(code).strip() not in STOP_WORDS:
                    items.append({
                        "code": clean_okpd2(code),
                        "cost": clean_price_value(cost) or 0,
                        "law":  "44-ФЗ",
                    })
        except Exception:
            pass

    elif "223" in law:
        try:
            for r in _iter_223_table_rows(row.get("lots_json")):
                okpd_raw  = r.get("КЛАССИФИКАЦИЯ ПО ОКПД2")
                price_raw = r.get("СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА")
                if okpd_raw:
                    cost_val = 0
                    if price_raw:
                        params = re.findall(r"([\d\s]+,\d{2})", str(price_raw))
                        if params:
                            cost_val = clean_price_value(params[-1]) or 0
                    items.append({
                        "code": clean_okpd2(okpd_raw),
                        "cost": cost_val,
                        "law":  "223-ФЗ",
                    })
        except Exception:
            pass

    if not items:
        items.append({"code": "Нет ОКПД2", "cost": 0, "law": law})

    for item in items:
        item["reg_number"]  = reg_number
        item["object_name"] = object_name
    return items


def extract_item_names(row: dict) -> list:
    """
    Извлекает НАИМЕНОВАНИЕ ТОВАРА (44-ФЗ) и НАИМЕНОВАНИЕ ЛОТА (223-ФЗ).
    44-ФЗ: common_info_json -> информация_об_объекте_закупки -> items -> table -> rows
           ключ НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ ПО ОКПД2, КТРУ
    223-ФЗ: lots_json -> {ключ} -> items -> parsed_table -> rows
           ключ НАИМЕНОВАНИЕ ТОВАРА (РАБОТЫ, УСЛУГИ)
    """
    law = str(row.get("law", ""))
    items = []

    if "44" in law:
        try:
            for r in _iter_44_table_rows(row.get("common_info_json")):
                name = r.get("НАИМЕНОВАНИЕ ТОВАРА, РАБОТЫ, УСЛУГИ ПО ОКПД2, КТРУ")
                cost = r.get("СТОИМОСТЬ, ₽")
                if name:
                    items.append({
                        "name": str(name).strip(),
                        "cost": clean_price_value(cost) or 0,
                    })
        except Exception:
            pass

    elif "223" in law:
        try:
            for r in _iter_223_table_rows(row.get("lots_json")):
                name = r.get("НАИМЕНОВАНИЕ ТОВАРА (РАБОТЫ, УСЛУГИ)")
                cost = r.get("СВЕДЕНИЯ О ЦЕНЕ ДОГОВОРА")
                if name:
                    cost_val = 0
                    if cost:
                        params = re.findall(r"([\d\s]+,\d{2})", str(cost))
                        if params:
                            cost_val = clean_price_value(params[-1]) or 0
                    items.append({"name": str(name).strip(), "cost": cost_val})
        except Exception:
            pass

    return items


def extract_contract_items_new(json_data) -> list:
    """
    Извлекает КТРУ и цену из payment_targets_json контракта.
    Структура: объекты_закупки -> items -> kind==table -> table -> rows
    """
    data = _parse_json(json_data)
    if not isinstance(data, dict):
        return []
    items = []
    try:
        for item in data.get("объекты_закупки", {}).get("items", []):
            if item.get("kind") == "table":
                for row in item.get("table", {}).get("rows", []):
                    ktru  = row.get("ktru")
                    price = row.get("price")
                    if ktru or price is not None:
                        items.append({
                            "ktru":  str(ktru).replace("\n", " ").strip() if ktru else None,
                            "price": price,
                        })
    except Exception:
        pass
    return items

# ─────────────────────────────────────────────────────────────────────────────
#  Функции анализа
# ─────────────────────────────────────────────────────────────────────────────

def analyze_purchases():
    """Основной блок: таблицы 2–9 (вся БД, от 100 млн)."""
    print("\n>>> Загрузка данных закупок (вся БД, от 100 млн)...")
    df = _load_purchases()
    if df.empty:
        print("Нет данных.")
        return
    print(f"✓ Загружено {len(df)} закупок")

    # ── Стандартные сводные ───────────────────────────────────────────────
    print_summary(df, "law",           "ЗАКУПКИ: ЗАКОНЫ")
    print_summary(df, "status",        "ЗАКУПКИ: СТАТУС (таблица 8)")
    print_summary(df, "customer_name", "ЗАКУПКИ: ЗАКАЗЧИКИ (ТОП-20)", limit=20)
    print_summary(df.sort_values("price_category_simple"),
                  "price_category_simple", "ЗАКУПКИ: БЮДЖЕТ (НМЦК)")

    # ── Таблица 2: диапазоны × закон (кол-во) ────────────────────────────
    price_cats = [c for c in PRICE_ORDER if c != "Нет цены"]
    df["price_category_tab2"] = pd.Categorical(
        df["price"].apply(categorize_price), categories=price_cats, ordered=True
    )
    pivot_ranges = pd.crosstab(df["price_category_tab2"], df["law"]).reindex(price_cats)
    pivot_ranges["Общий итог"] = pivot_ranges.sum(axis=1)
    pivot_ranges.loc["Всего закупок"] = pivot_ranges.sum()
    print(f"\n{'=' * 80}")
    print("Таблица 2. Распределение по диапазонам НМЦК (кол-во)")
    print(f"{'=' * 80}")
    print(pivot_ranges)

    # ── Таблица 3: способ × закон (кол-во + сумма) ───────────────────────
    p_cnt, p_sum = build_count_sum_pivots(df, "placing_way_cat", PLACING_WAY_ORDER)
    print_count_sum_table(
        "Таблица 3. Закупки по способу определения поставщика (кол-во и сумма)",
        p_cnt, p_sum,
    )

    # ── Таблица 4: диапазоны (ед. + сумма) по законам ────────────────────
    print(f"\n{'=' * 90}")
    print("Таблица 4. Диапазоны НМЦК (ед. и сумма) по законам")
    print(f"{'=' * 90}")
    grouped4 = df.groupby(["category", "law"])["price"].agg(["count", "sum"])
    unstacked4 = grouped4.unstack(fill_value=0)
    for metric in ["count", "sum"]:
        for law in LAWS:
            if (metric, law) not in unstacked4.columns:
                unstacked4[(metric, law)] = 0
    unstacked4[("count", "Общий итог")] = (
        unstacked4[("count", "44-ФЗ")] + unstacked4[("count", "223-ФЗ")]
    )
    unstacked4[("sum", "Общий итог")] = (
        unstacked4[("sum", "44-ФЗ")] + unstacked4[("sum", "223-ФЗ")]
    )
    final_rows4 = []
    for cat in sorted(df["category"].unique()):
        if cat in ("Без цены", "Нет цены"):
            continue
        if cat not in unstacked4.index:
            continue
        r = unstacked4.loc[cat]
        final_rows4 += [
            {"Диапазон": f"{_strip_prefix(cat)}, ед.",
             "44-ФЗ": int(r[("count", "44-ФЗ")]),
             "223-ФЗ": int(r[("count", "223-ФЗ")]),
             "Общий итог": int(r[("count", "Общий итог")])},
            {"Диапазон": "сумма НМЦК, руб.",
             "44-ФЗ": r[("sum", "44-ФЗ")],
             "223-ФЗ": r[("sum", "223-ФЗ")],
             "Общий итог": r[("sum", "Общий итог")]},
        ]
    df4 = pd.DataFrame(final_rows4)
    for c in ["44-ФЗ", "223-ФЗ", "Общий итог"]:
        df4[c] = df4[c].apply(fmt_nonzero)
    print(df4.to_string(index=False, justify="right"))

    # ── Таблица 7: статусы (кол-во + сумма) ──────────────────────────────
    p_cnt7, p_sum7 = build_count_sum_pivots(df, "status")
    print_count_sum_table(
        "Таблица 7. Статус закупок по 44-ФЗ и 223-ФЗ (кол-во и сумма)",
        p_cnt7, p_sum7, row_label_width=40,
    )

    # ── Таблица 9: способы детально (ед. + сумма) ────────────────────────
    p_cnt9, p_sum9 = build_count_sum_pivots(df, "placing_way")
    print_count_sum_table(
        "Таблица 9. Распределение по способу определения поставщика (ед. и сумма)",
        p_cnt9, p_sum9,
    )

    # ── ОКПД2 с привязкой к номеру закупки ───────────────────────────────
    print("\n... Извлечение позиций ОКПД2 из JSON ...")
    items_list = []
    for _, row in df.iterrows():
        items_list.extend(extract_okpd2_items(row.to_dict()))

    if items_list:
        items_df = pd.DataFrame(items_list)
        df_has = items_df[items_df["code"] != "Нет ОКПД2"]
        df_no  = items_df[items_df["code"] == "Нет ОКПД2"]

        print(f"\n{'=' * 130}")
        print(f"ЗАКУПКИ БЕЗ УКАЗАНИЯ ОКПД2 В JSON (Найдено: {len(df_no)})")
        print(f"{'=' * 130}")
        if not df_no.empty:
            print(f"{'Реестровый номер':<25} {'Закон':<10} {'Объект закупки'}")
            print("-" * 130)
            for _, r in df_no.iterrows():
                obj = r["object_name"]
                short = (obj[:90] + "...") if len(obj) > 90 else obj
                print(f"{r['reg_number']:<25} {r['law']:<10} {short}")
        else:
            print("У всех загруженных закупок успешно найден ОКПД2.")

        if not df_has.empty:
            print_summary(df_has, "code", "ЗАКУПКИ: ТОП ПОЗИЦИЙ (ОКПД2)", limit=30)
    else:
        print("Не удалось извлечь информацию о позициях.")


def analyze_okpd2_usage():
    """Таблица 10: коды ОКПД2 — ед. и сумма НМЦК по законам."""
    print("\n>>> Анализ кодов ОКПД2 (вся БД, от 100 млн)...")
    df = _load_purchases()
    if df.empty:
        return
    print(f"✓ Загружено {len(df)} закупок")

    items_list = []
    for _, row in df.iterrows():
        items_list.extend(extract_okpd2_items(row.to_dict()))

    if not items_list:
        print("Товары не найдены (проверьте структуру JSON).")
        return

    items_df = pd.DataFrame(items_list)
    grouped = items_df.groupby(["code", "law"])["cost"].agg(["count", "sum"])
    unstacked = grouped.unstack(fill_value=0)

    for metric in ["count", "sum"]:
        for law in LAWS:
            if (metric, law) not in unstacked.columns:
                unstacked[(metric, law)] = 0

    unstacked[("count", "Общий Итог")] = (
        unstacked[("count", "44-ФЗ")] + unstacked[("count", "223-ФЗ")]
    )
    unstacked[("sum", "Общий Итог")] = (
        unstacked[("sum", "44-ФЗ")] + unstacked[("sum", "223-ФЗ")]
    )
    unstacked = unstacked.sort_values(("count", "Общий Итог"), ascending=False).head(50)

    rows = []
    for code in unstacked.index:
        r = unstacked.loc[code]
        rows += [
            {"Код ОКПД2": str(code)[:60], "Показатель": "количество закупок, ед.",
             "44-ФЗ": int(r[("count", "44-ФЗ")]),
             "223-ФЗ": int(r[("count", "223-ФЗ")]),
             "Общий Итог": int(r[("count", "Общий Итог")])},
            {"Код ОКПД2": "", "Показатель": "сумма НМЦК, руб.",
             "44-ФЗ": r[("sum", "44-ФЗ")],
             "223-ФЗ": r[("sum", "223-ФЗ")],
             "Общий Итог": r[("sum", "Общий Итог")]},
        ]

    final_df = pd.DataFrame(rows)
    for c in ["44-ФЗ", "223-ФЗ", "Общий Итог"]:
        final_df[c] = final_df[c].apply(fmt_nonzero)

    print(f"\n{'=' * 90}")
    print("Таблица 10. Применение кодов ОКПД2 (ед. и сумма)")
    print(f"{'=' * 90}")
    print(final_df.to_string(index=False, justify="right"))
    print(f"{'-' * 90}")


def analyze_item_names():
    """Топ наименований товаров/работ/услуг из JSON-полей закупок."""
    print("\n>>> Анализ наименований товаров (вся БД, от 100 млн)...")
    df = _load_purchases()
    if df.empty:
        return
    print(f"✓ Загружено {len(df)} закупок")

    items_list = []
    for _, row in df.iterrows():
        items_list.extend(extract_item_names(row.to_dict()))

    if not items_list:
        print("Наименования не найдены.")
        return

    items_df = pd.DataFrame(items_list)
    print_summary_with_sum(items_df, "name", "cost",
                           "ТОП НАИМЕНОВАНИЙ ТОВАРОВ/РАБОТ/УСЛУГ", limit=30)


def analyze_contracts():
    """Анализ контрактов: статусы, заказчики, позиции ТКП."""
    print("\n>>> Загрузка контрактов (вся БД, от 20 млн)...")
    df = _load_contracts(min_price=20_000_000)
    if df.empty:
        print("Контракты не найдены.")
        return
    print(f"✓ Загружено {len(df)} контрактов")

    print_summary(df, "law",           "КОНТРАКТЫ: ЗАКОНЫ")
    print_summary(df, "customer_name", "КОНТРАКТЫ: ЗАКАЗЧИКИ")

    print("\n... Извлечение позиций из контрактов ...")
    items_series = df["payment_targets_json"].apply(extract_contract_items_new)
    exploded = items_series.explode().dropna()
    items_df = pd.DataFrame(exploded.tolist()) if not exploded.empty else pd.DataFrame()

    if not items_df.empty:
        print_summary(items_df, "ktru", "КОНТРАКТЫ: ПОПУЛЯРНЫЕ ПОЗИЦИИ", limit=30)
        items_df["price_float"] = pd.to_numeric(items_df["price"], errors="coerce")
        items_df["item_price_category"] = pd.Categorical(
            items_df["price_float"].apply(categorize_price),
            categories=PRICE_ORDER, ordered=True,
        )
        print_summary(
            items_df.sort_values("item_price_category"),
            "item_price_category",
            "КОНТРАКТЫ: СТОИМОСТЬ ПОЗИЦИЙ",
        )
    else:
        print("Товары в контрактах не найдены.")


def analyze_contract_status():
    """
    Статус контракта × закон; конверсия закупка → контракт.
    JOIN по RegistryNumber.
    Статус = Purchase.ProcurementStage (статус закупки).
    Наличие контракта определяется по Contract.RegistryNumber.
    """
    print("\n>>> Анализ статусов контрактов (вся БД, от 100 млн)...")
    db.connect(reuse_if_open=True)

    # Загружаем все нужные закупки — явно включаем ProcurementStage
    purchases_qs = list(
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PurchaseOrder,
            Purchase.ProcurementStage,
            Purchase.InitialMaxContractPrice,
        )
        .where(Purchase.InitialMaxContractPrice >= float(100_000_000))
        .dicts()          # dicts() надёжнее namedtuples() при частичном select
    )

    # Загружаем контракты: только факт наличия + цена
    reg_numbers = {p["RegistryNumber"] for p in purchases_qs}
    contracts_by_reg = {}
    if reg_numbers:  # guard: .in_(set()) вызывает Ellipsis-ошибку в Peewee
        for c in (
            Contract
            .select(Contract.RegistryNumber, Contract.ContractPrice)
            .where(Contract.RegistryNumber.in_(list(reg_numbers)))
            .dicts()
        ):
            contracts_by_reg[c["RegistryNumber"]] = c

    db.close()

    rows = []
    for p in purchases_qs:
        c = contracts_by_reg.get(p["RegistryNumber"])
        rows.append({
            "law":             p["PurchaseOrder"],
            "contract_status": p["ProcurementStage"] if c else "Нет контракта",
            "contract_price":  c["ContractPrice"] if c else None,
        })

    df = pd.DataFrame(rows)
    df["contract_status"] = df["contract_status"].fillna("Нет контракта")
    df["price"] = df["contract_price"].apply(
        lambda x: clean_price_value(x) if pd.notna(x) and str(x).strip() != "" else 0.0
    )
    print(f"✓ Загружено {len(df)} записей")

    # Статус × закон
    p_cnt, p_sum = build_count_sum_pivots(df, "contract_status")
    print_count_sum_table(
        "Таблица. Статус контракта/договора по законам (кол-во и сумма)",
        p_cnt, p_sum, row_label_width=40,
    )

    # Статистика по контрактам
    df_with = df[df["contract_status"] != "Нет контракта"]
    if not df_with.empty:
        print(f"\n{'=' * 120}")
        print("Таблица. Общая статистика по сумме контрактов")
        print(f"{'=' * 120}")
        stats = df_with.groupby("law")["price"].agg(["count", "sum", "max", "min", "mean"])
        stats_t = stats.T
        stats_t["Общий итог"] = pd.Series({
            "count": df_with["price"].count(),
            "sum":   df_with["price"].sum(),
            "max":   df_with["price"].max(),
            "min":   df_with["price"].min(),
            "mean":  df_with["price"].mean(),
        })
        stats_t.index = [
            "Количество контрактов, ед.", "Сумма контрактов, руб.",
            "Максимальная цена, руб.",    "Минимальная цена, руб.",
            "Средняя цена, руб.",
        ]
        pd.options.display.float_format = "{:,.2f}".format
        print(stats_t.fillna(0))
        print("-" * 120)

    # Конверсия
    df["conv_group"] = df["contract_status"].apply(
        lambda x: "Заключён контракт" if x != "Нет контракта" else "Без контракта"
    )
    p_cnt_c, p_sum_c = build_count_sum_pivots(df, "conv_group")
    print_count_sum_table(
        "Таблица. Конверсия: закупки с контрактом vs без контракта",
        p_cnt_c, p_sum_c, row_label_width=25,
    )
def analyze_suppliers():
    """Топ-30 поставщиков крупных контрактов."""
    print("\n>>> Загрузка поставщиков (вся БД, от 100 млн)...")
    df = _load_suppliers()
    if df.empty:
        print("Поставщики не найдены.")
        return
    print(f"✓ Загружено {len(df)} записей поставщиков")
    print_summary(df, "organization", "ПОСТАВЩИКИ КРУПНЫХ КОНТРАКТОВ", limit=30)


def analyze_purchases_by_year():
    """Сводная по годам: кол-во и объём НМЦК."""
    print("\n>>> Анализ закупок по годам (вся БД, от 100 млн)...")
    df = _load_purchases()
    if df.empty:
        return

    print_summary(df, "year", "ЗАКУПКИ: КОЛИЧЕСТВО ПО ГОДАМ")

    print(f"\n{'=' * 60}")
    print("ЗАКУПКИ: ГОД × ЗАКОН")
    print(f"{'=' * 60}")
    pivot = pd.crosstab(df["year"], df["law"]).sort_index()
    print(pivot)
    print(f"{'-' * 60}")

    print(f"\n{'=' * 60}")
    print("ДЕНЬГИ: ГОД × ЗАКОН (СУММА)")
    print(f"{'=' * 60}")
    pivot_sum = pd.pivot_table(
        df, values="price", index="year", columns="law",
        aggfunc="sum", fill_value=0,
    ).sort_index()
    pd.options.display.float_format = "{:,.2f}".format
    print(pivot_sum)
    print(f"{'-' * 60}")


def analyze_vessels():
    """Анализ судовой базы: типы, верфи, годы постройки, ценовые диапазоны."""
    print("\n>>> Загрузка данных по судам...")
    db.connect(reuse_if_open=True)

    # Загружаем суда с ценами контрактов через RegistryNumber
    vessels = list(
        Vessel
        .select(
            Vessel.id,
            Vessel.ship_type_rmrs,
            Vessel.ship_type_rko,
            Vessel.ship_class,
            Vessel.year_built,
            Vessel.country_built,
            Vessel.shipyard_name,
            Vessel.federal_district,
            Vessel.gross_tonnage,
            Vessel.deadweight,
            Vessel.hull_material,
            Vessel.contract,
        )
        .namedtuples()
    )

    contract_ids = {v.contract_id for v in vessels if v.contract_id}
    prices_by_contract = {}
    if contract_ids:
        for c in Contract.select(Contract.Id, Contract.ContractPrice).where(
            Contract.Id.in_(contract_ids)
        ).namedtuples():
            prices_by_contract[c.Id] = c.ContractPrice

    db.close()

    if not vessels:
        print("Нет данных по судам.")
        return

    rows = []
    for v in vessels:
        rows.append({
            "ship_type_rmrs":   v.ship_type_rmrs,
            "ship_type_rko":    v.ship_type_rko,
            "ship_class":       v.ship_class,
            "year_built":       v.year_built,
            "country_built":    v.country_built,
            "shipyard_name":    v.shipyard_name,
            "federal_district": v.federal_district,
            "hull_material":    v.hull_material,
            "contract_price":   prices_by_contract.get(v.contract_id),
        })

    df = pd.DataFrame(rows)
    df["contract_price_num"] = pd.to_numeric(df["ContractPrice"], errors="coerce")
    print(f"✓ Загружено {len(df)} записей о судах")

    print_summary(df, "ship_type_rmrs",   "СУДА: ТИП (РМРС)", limit=20)
    print_summary(df, "ship_class",       "СУДА: КЛАСС", limit=20)
    print_summary(df, "shipyard_name",    "СУДА: ВЕРФИ ПОСТРОЙКИ", limit=20)
    print_summary(df, "federal_district", "СУДА: ФЕДЕРАЛЬНЫЙ ОКРУГ")
    print_summary(df, "hull_material",    "СУДА: МАТЕРИАЛ КОРПУСА")

    df_year = df.dropna(subset=["year_built"])
    if not df_year.empty:
        print_summary(df_year, "year_built", "СУДА: ГОД ПОСТРОЙКИ")

    df_price = df.dropna(subset=["contract_price_num"])
    if not df_price.empty:
        df_price = df_price.copy()
        df_price["price_cat"] = df_price["contract_price_num"].apply(categorize_price)
        print_summary(df_price, "price_cat", "СУДА: ЦЕНОВЫЕ ДИАПАЗОНЫ КОНТРАКТА")

        print(f"\n{'=' * 80}")
        print("СУДА: СТАТИСТИКА ЦЕН КОНТРАКТОВ")
        print(f"{'=' * 80}")
        for k, v in df_price["contract_price_num"].describe().items():
            labels = {"count": "Кол-во", "mean": "Среднее", "std": "Откл.",
                      "min": "Мин", "25%": "Q1", "50%": "Медиана",
                      "75%": "Q3", "max": "Макс"}
            print(f"{labels.get(k, k):<20} {fmt_num(v):>20}")
        print("-" * 80)


# ─────────────────────────────────────────────────────────────────────────────
#  Точка входа
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":


    print("=" * 60)
    print("  АНАЛИЗ ЗАКУПОК (Peewee / SQLite) — вся БД")
    print("=" * 60)

    analyze_purchases()
    analyze_okpd2_usage()
    analyze_item_names()
    analyze_contracts()
    analyze_contract_status()
    analyze_suppliers()
    analyze_purchases_by_year()
    analyze_vessels()