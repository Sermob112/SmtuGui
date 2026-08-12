"""
analyze_purchases_peewee.py
Анализ закупок на основе Peewee-моделей (SQLite).
Полный аналог analyze_purchases.py, адаптированный под ORM.
Во всех сводных таблицах добавлена конверсия (доля, %) по каждому закону
и общая сумма/итог по всем законам.

ДОБАВЛЕНО: фильтр по дате публикации закупки — от DATE_FROM до DATE_TO
(по умолчанию: 15.04.2023 -> сегодня), применяется совместно с фильтром
по НМЦК/цене контракта.
"""

import re
import json
from datetime import date, datetime

import pandas as pd

from smtuIdle.BD.initialize_db import db
from smtuIdle.BD.models import *


db_path = r"C:\\Users\\Sergey\\Desktop\\Work\\SmtuGui\\smtuIdle\\database.db"
# 2. ПЕРЕИНИЦИАЛИЗИРУЕМ импортированную базу правильным путем!
db.init(db_path)
# 3. Подключаемся
db.connect(reuse_if_open=True)
# ─── Константы ───────────────────────────────────────────────────────────────
LAWS = ("44-ФЗ", "223-ФЗ")
DATE_FROM_STR = "15.04.2023"
MIN_PRICE = 100_000_000
DATE_FROM = datetime.strptime(DATE_FROM_STR, "%d.%m.%Y")
DATE_TO = pd.Timestamp(date.today())  # текущая дата на момент запуска

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


def _filter_by_date_range(df: pd.DataFrame, date_col: str = "published",
                           date_from: datetime = DATE_FROM,
                           date_to: pd.Timestamp = DATE_TO) -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df
    dt = pd.to_datetime(df[date_col], format="%d.%m.%Y", errors="coerce")
    # fallback на общий парсер (dayfirst) для нестандартных значений
    mask_na = dt.isna()
    if mask_na.any():
        dt.loc[mask_na] = pd.to_datetime(df.loc[mask_na, date_col], dayfirst=True, errors="coerce")
    keep = dt.notna() & (dt >= date_from) & (dt <= date_to)
    return df.loc[keep].copy()
# ────────────────────────────────────────────────────────────────────────────
#  Генераторы строк из JSON-полей (структура не изменилась)
# ─────────────────────────────────────────────────────────────────────────────
def _iter_44_table_rows(raw_json):
    data = _parse_json(raw_json)
    if not isinstance(data, dict):
        return
    info = data.get("информация_об_объекте_закупки", {})
    for item in info.get("items", []):
        if item.get("kind") == "table":
            yield from item.get("table", {}).get("rows", [])
def _iter_223_table_rows(raw_json):
    data = _parse_json(raw_json)
    if not isinstance(data, dict):
        return
    for section in data.values():
        if isinstance(section, dict):
            for item in section.get("items", []):
                yield from item.get("parsed_table", {}).get("rows", [])
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
    total_cnt = grouped["count"].sum()
    total_sum = grouped["sum"].sum()
    print(f"{'Категория':<50} {'Кол-во':>8} {'Доля,%':>8} {'Сумма, руб':>20} {'Доля,%':>8}")
    print("-" * 100)
    for idx, row in grouped.iterrows():
        s = str(idx).strip()
        short = (s[:50] + "...") if len(s) > 50 else s
        cnt_pct = _pct(row["count"], total_cnt)
        sum_pct = _pct(row["sum"], total_sum)
        print(f"{short:<50} {int(row['count']):>8} {cnt_pct:>8} {fmt_nonzero(row['sum']):>20} {sum_pct:>8}")
    print("-" * 100)
    if limit and len(grouped) >= limit:
        print(f"{'... и еще строк ...':<50}")
    print(f"{'ИТОГО':<50} {int(grouped['count'].sum()):>8} {'100.0%':>8} {fmt_num(grouped['sum'].sum()):>20} {'100.0%':>8}")


def _pct(value, total):
    """Доля value от total в процентах, строкой вида '12.3%'. Безопасна при total==0."""
    try:
        if total == 0 or pd.isna(total):
            return "0.0%"
        return f"{(value / total) * 100:.1f}%"
    except Exception:
        return "0.0%"
def build_count_sum_pivots(df: pd.DataFrame, row_col: str, value_col: str = "price",
                           row_order=None, limit=None):

    grouped = df.groupby([row_col, "law"])[value_col].agg(["count", "sum"])
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
    else:
        order_idx = p_cnt.sum(axis=1).sort_values(ascending=False).index
        p_cnt = p_cnt.reindex(order_idx)
        p_sum = p_sum.reindex(order_idx)
        if limit:
            keep = p_cnt.head(limit).index
            p_cnt = p_cnt.loc[keep]
            p_sum = p_sum.loc[keep]

    p_cnt["Всего"] = p_cnt.sum(axis=1)
    p_sum["Всего"] = p_sum.sum(axis=1)
    p_cnt.loc["Общий итог"] = p_cnt.sum()
    p_sum.loc["Общий итог"] = p_sum.sum()

    return p_cnt, p_sum


def print_count_sum_table(title: str, p_cnt: pd.DataFrame, p_sum: pd.DataFrame,
                          row_label_width=45):
    W = row_label_width
    total_cnt = p_cnt.loc["Общий итог"]
    total_sum = p_sum.loc["Общий итог"]
    print(f"\n{'=' * 140}")
    print(title)
    print(f"{'=' * 140}")
    print(f"{'':^{W}} {'Показатель':<15} {'44-ФЗ':>22} {'223-ФЗ':>22} {'Всего':>22}")
    print("-" * 140)

    data_rows = [r for r in p_cnt.index if r != "Общий итог"]
    all_rows = data_rows + ["Общий итог"]
    for row in all_rows:
        if row == "Общий итог":
            print("-" * 140)

        c44, c223, ctot = p_cnt.loc[row, "44-ФЗ"], p_cnt.loc[row, "223-ФЗ"], p_cnt.loc[row, "Всего"]
        s44, s223, stot = p_sum.loc[row, "44-ФЗ"], p_sum.loc[row, "223-ФЗ"], p_sum.loc[row, "Всего"]

        c44_s  = f"{int(c44):>6} ({_pct(c44, total_cnt['44-ФЗ'])})" if c44 else "-"
        c223_s = f"{int(c223):>6} ({_pct(c223, total_cnt['223-ФЗ'])})" if c223 else "-"
        ctot_s = f"{int(ctot):>6} ({_pct(ctot, total_cnt['Всего'])})" if ctot else "-"
        print(f"{str(row):<{W}} {'кол-во':<15} {c44_s:>22} {c223_s:>22} {ctot_s:>22}")

        s44_s  = f"{fmt_nonzero(s44):>12} ({_pct(s44, total_sum['44-ФЗ'])})" if s44 else "-"
        s223_s = f"{fmt_nonzero(s223):>12} ({_pct(s223, total_sum['223-ФЗ'])})" if s223 else "-"
        stot_s = f"{fmt_nonzero(stot):>12} ({_pct(stot, total_sum['Всего'])})" if stot else "-"
        print(f"{'':^{W}} {'сумма, руб':<15} {s44_s:>22} {s223_s:>22} {stot_s:>22}")

    print("-" * 140)
def _get_eligible_registry_numbers(
    min_price: float = MIN_PRICE,
) -> set:
    db.connect(reuse_if_open=True)

    rows = list(
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PlacementDate,
            Purchase.InitialMaxContractPriceInCurrency,
        )
        .where(
            Purchase.InitialMaxContractPriceInCurrency >= min_price
        )
        .dicts()
    )

    db.close()

    if not rows:
        return set()

    df = pd.DataFrame(rows).rename(
        columns={
            "PlacementDate": "published",
        }
    )

    df = _filter_by_date_range(df, "published")

    return set(df["RegistryNumber"].tolist())


def _load_purchases(min_price: float = 100_000_000) -> pd.DataFrame:
    """
    Загружает закупки с НМЦК >= min_price и датой публикации в диапазоне
    [DATE_FROM, DATE_TO]. JSON-поля common_info_json и lots_json включены напрямую.
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
            Purchase.InitialMaxContractPriceInCurrency,
            Purchase.PlacementDate,
            Purchase.common_info_json,
            Purchase.lots_json,
            Purchase.OKPD2Classification,
        )
        .where(Purchase.InitialMaxContractPriceInCurrency >= min_price)
        .namedtuples()
    )
    rows = list(query)
    db.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "RegistryNumber": "reg_number",
        "PurchaseName": "object_name",
        "PurchaseOrder": "law",
        "ProcurementStage": "status",
        "ProcurementMethod": "placing_way",
        "CustomerName": "customer_name",
        "InitialMaxContractPriceInCurrency": "initial_price_amount",
        "PlacementDate": "published",
        "OKPD2Classification": "okpd2_classification",
    })

    # ── Фильтр по дате публикации [DATE_FROM, DATE_TO] ─────────────────────
    df = _filter_by_date_range(df, "published")
    if df.empty:
        return df

    df["common_info_json"] = df["common_info_json"].apply(_parse_json)
    df["lots_json"]        = df["lots_json"].apply(_parse_json)

    df["price"] = pd.to_numeric(df["initial_price_amount"], errors="coerce").fillna(0)
    df["category"] = df["price"].apply(categorize_price)
    df["published_dt"] = pd.to_datetime(df["published"], format="%d.%m.%Y", errors="coerce")
    df["year"] = df["published_dt"].dt.year
    df["placing_way_cat"] = df["placing_way"].apply(map_placing_way)
    df["price_category_simple"] = pd.Categorical(
        df["price"].apply(categorize_price), categories=PRICE_ORDER, ordered=True
    )
    return df


def _load_contracts(min_price: float = 100_000_000) -> pd.DataFrame:
    """
    Загружает контракты, JOIN с Purchase по RegistryNumber.
    Учитывает фильтр по цене закупки И по дате публикации закупки
    [DATE_FROM, DATE_TO].
    """
    eligible_nums = _get_eligible_registry_numbers(min_price)
    if not eligible_nums:
        return pd.DataFrame()

    db.connect(reuse_if_open=True)
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
    df["price"] = df["ContractPrice"].apply(clean_price_value)
    df["payment_targets_json"] = df["payment_targets_json"].apply(_parse_json)
    return df


def _load_suppliers(min_price: float = 100_000_000) -> pd.DataFrame:
    eligible = _get_eligible_registry_numbers(min_price)
    if not eligible:
        return pd.DataFrame()

    db.connect(reuse_if_open=True)
    purchases_law = {
        r.RegistryNumber: r.PurchaseOrder
        for r in Purchase.select(Purchase.RegistryNumber, Purchase.PurchaseOrder)
        .where(Purchase.RegistryNumber.in_(eligible))
    }
    contracts_info = {
        r.Id: {"RegistryNumber": r.RegistryNumber, "ContractPrice": r.ContractPrice}
        for r in Contract.select(Contract.Id, Contract.RegistryNumber, Contract.ContractPrice)
        .where(Contract.RegistryNumber.in_(eligible))
    }

    query = (
        SupplierContract
        .select(Supplier.organization, SupplierContract.contract)
        .join(Supplier, on=SupplierContract.supplier)
        .where(SupplierContract.contract.in_(set(contracts_info.keys())))
        .dicts()
    )
    rows = list(query)
    db.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # При .dicts() FK-поле SupplierContract.contract возвращается под ключом
    # "contract" (сырое значение contract_id), а не "contract_id".
    id_col = "contract" if "contract" in df.columns else "contract_id"
    if id_col not in df.columns:
        raise KeyError(
            f"Не найдена колонка с id контракта среди {list(df.columns)}. "
            "Проверьте имя FK-поля в модели SupplierContract."
        )

    df["law"] = df[id_col].map(
        lambda cid: purchases_law.get(contracts_info.get(cid, {}).get("RegistryNumber"))
    )
    df["price"] = df[id_col].map(
        lambda cid: pd.to_numeric(contracts_info.get(cid, {}).get("ContractPrice"), errors="coerce")
    ).fillna(0)
    return df

# ─────────────────────────────────────────────────────────────────────────────
#  Извлечение ОКПД2 из JSON-полей закупки
# ─────────────────────────────────────────────────────────────────────────────

def extract_okpd2_items(row: dict) -> list:
    law         = str(row.get("law", ""))
    reg_number  = str(row.get("reg_number", ""))
    object_name = str(row.get("object_name", "")).replace("\n", " ").strip()
    okpd2_field = row.get("okpd2_classification")
    price_total = row.get("price", 0) or 0
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
                        "source": "json",
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
                        "source": "json",
                    })
        except Exception:
            pass

    if not items and okpd2_field and str(okpd2_field).strip() not in ("", "Нет данных"):
        fallback_law = "44-ФЗ" if "44" in law else ("223-ФЗ" if "223" in law else (law or "Прочее"))
        items.append({
            "code": clean_okpd2(okpd2_field),
            "cost": price_total,
            "law": fallback_law,
            "source": "field",
        })

    if not items:
        items.append({"code": "Нет ОКПД2", "cost": 0, "law": law, "source": "none"})

    for item in items:
        item["reg_number"]  = reg_number
        item["object_name"] = object_name
    return items


def extract_item_names(row: dict) -> list:
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
                        "law": "44-ФЗ",
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
                    items.append({"name": str(name).strip(), "cost": cost_val, "law": "223-ФЗ"})
        except Exception:
            pass

    return items


def extract_contract_items_new(json_data) -> list:
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
    """Основной блок: таблицы 2–9 (вся БД, от 100 млн, дата публикации в диапазоне)."""
    print(f"\n>>> Загрузка данных закупок (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")
    df = _load_purchases()
    if df.empty:
        print("Нет данных.")
        return
    print(f"✓ Загружено {len(df)} закупок")

    p_cnt_law, p_sum_law = build_count_sum_pivots(df, "law")
    print_count_sum_table("ЗАКУПКИ: ЗАКОНЫ (кол-во и сумма)", p_cnt_law, p_sum_law, row_label_width=20)

    p_cnt_status, p_sum_status = build_count_sum_pivots(df, "status")
    print_count_sum_table("ЗАКУПКИ: СТАТУС (таблица 8)", p_cnt_status, p_sum_status)

    p_cnt_cust, p_sum_cust = build_count_sum_pivots(df, "customer_name", limit=20)
    print_count_sum_table("ЗАКУПКИ: ЗАКАЗЧИКИ (ТОП-20)", p_cnt_cust, p_sum_cust, row_label_width=50)

    p_cnt_budget, p_sum_budget = build_count_sum_pivots(df, "price_category_simple", row_order=PRICE_ORDER)
    print_count_sum_table("ЗАКУПКИ: БЮДЖЕТ (НМЦК)", p_cnt_budget, p_sum_budget)

    price_cats = [c for c in PRICE_ORDER if c != "Нет цены"]
    df["price_category_tab2"] = pd.Categorical(
        df["price"].apply(categorize_price), categories=price_cats, ordered=True
    )
    p_cnt2, p_sum2 = build_count_sum_pivots(df, "price_category_tab2", row_order=price_cats)
    print_count_sum_table("Таблица 2. Распределение по диапазонам НМЦК (кол-во и сумма)", p_cnt2, p_sum2)

    p_cnt, p_sum = build_count_sum_pivots(df, "placing_way_cat", row_order=PLACING_WAY_ORDER)
    print_count_sum_table(
        "Таблица 3. Закупки по способу определения поставщика (кол-во и сумма)",
        p_cnt, p_sum,
    )

    p_cnt4, p_sum4 = build_count_sum_pivots(df, "category")
    print_count_sum_table(
        "Таблица 4. Диапазоны НМЦК (ед. и сумма) по законам",
        p_cnt4, p_sum4,
    )

    p_cnt7, p_sum7 = build_count_sum_pivots(df, "status")
    print_count_sum_table(
        "Таблица 7. Статус закупок по 44-ФЗ и 223-ФЗ (кол-во и сумма)",
        p_cnt7, p_sum7, row_label_width=40,
    )

    p_cnt9, p_sum9 = build_count_sum_pivots(df, "placing_way")
    print_count_sum_table(
        "Таблица 9. Распределение по способу определения поставщика (ед. и сумма)",
        p_cnt9, p_sum9,
    )

    print("\n... Извлечение позиций ОКПД2 из JSON (с fallback на поле OKPD2Classification) ...")
    items_list = []
    for _, row in df.iterrows():
        items_list.extend(extract_okpd2_items(row.to_dict()))

    if items_list:
        items_df = pd.DataFrame(items_list)
        df_has = items_df[items_df["code"] != "Нет ОКПД2"]
        df_no = items_df[items_df["code"] == "Нет ОКПД2"]

        print(f"\n{'=' * 130}")
        print(f"ЗАКУПКИ БЕЗ УКАЗАНИЯ ОКПД2 (Найдено: {len(df_no)})")
        print(f"{'=' * 130}")
        if not df_no.empty:
            print(f"{'Реестровый номер':<25} {'Закон':<10} {'Объект закупки'}")
            print("-" * 130)
            for _, r in df_no.iterrows():
                obj = r["object_name"]
                short = (obj[:90] + "...") if len(obj) > 90 else obj
                print(f"{r['reg_number']:<25} {r['law']:<10} {short}")
        else:
            print("У всех загруженных закупок успешно найден ОКПД2 (JSON или поле OKPD2Classification).")

        if not df_has.empty:
            print(f"\n{'=' * 90}")
            print("ИСТОЧНИК ОКПД2: JSON (построчно) vs OKPD2Classification (fallback)")
            print(f"{'=' * 90}")
            p_cnt_src, p_sum_src = build_count_sum_pivots(df_has, "source", value_col="cost")
            print_count_sum_table("Источник данных ОКПД2 по законам (кол-во позиций и сумма)", p_cnt_src, p_sum_src,
                                  row_label_width=20)

            p_cnt_okpd, p_sum_okpd = build_count_sum_pivots(df_has, "code", value_col="cost", limit=30)
            print_count_sum_table("ЗАКУПКИ: ТОП ПОЗИЦИЙ (ОКПД2)", p_cnt_okpd, p_sum_okpd, row_label_width=30)
    else:
        print("Не удалось извлечь информацию о позициях.")


def analyze_okpd2_usage():
    print(f"\n>>> Анализ кодов ОКПД2 (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")
    df = _load_purchases()
    if df.empty:
        return
    print(f"✓ Загружено {len(df)} закупок")

    items_list = []
    for _, row in df.iterrows():
        items_list.extend(extract_okpd2_items(row.to_dict()))

    if not items_list:
        print("Товары не найдены (проверьте структуру JSON и поле OKPD2Classification).")
        return

    items_df = pd.DataFrame(items_list)
    df_has = items_df[items_df["code"] != "Нет ОКПД2"]

    if df_has.empty:
        print("Ни у одной закупки не заполнен ОКПД2 (ни в JSON, ни в OKPD2Classification).")
        return

    p_cnt_src, p_sum_src = build_count_sum_pivots(df_has, "source", value_col="cost")
    print_count_sum_table("Таблица 10а. Источник ОКПД2: JSON vs OKPD2Classification (fallback)", p_cnt_src, p_sum_src, row_label_width=20)

    p_cnt, p_sum = build_count_sum_pivots(df_has, "code", value_col="cost", limit=50)
    print_count_sum_table("Таблица 10. Применение кодов ОКПД2 (ед. и сумма)", p_cnt, p_sum, row_label_width=45)


def analyze_item_names():
    print(f"\n>>> Анализ наименований товаров (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")
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
    p_cnt, p_sum = build_count_sum_pivots(items_df, "name", value_col="cost", limit=30)
    print_count_sum_table("ТОП НАИМЕНОВАНИЙ ТОВАРОВ/РАБОТ/УСЛУГ", p_cnt, p_sum, row_label_width=50)


def analyze_contracts():
    """Анализ контрактов: статусы, заказчики, позиции ТКП (закупки в диапазоне дат)."""
    print(f"\n>>> Загрузка контрактов (от 100 млн, дата публикации закупки {DATE_FROM_STR} — {DATE_TO.date()})...")
    df = _load_contracts(min_price=100_000_000)
    if df.empty:
        print("Контракты не найдены.")
        return
    print(f"✓ Загружено {len(df)} контрактов")

    p_cnt_law, p_sum_law = build_count_sum_pivots(df, "law")
    print_count_sum_table("КОНТРАКТЫ: ЗАКОНЫ (кол-во и сумма)", p_cnt_law, p_sum_law, row_label_width=20)

    p_cnt_cust, p_sum_cust = build_count_sum_pivots(df, "customer_name", limit=30)
    print_count_sum_table("КОНТРАКТЫ: ЗАКАЗЧИКИ", p_cnt_cust, p_sum_cust, row_label_width=50)

    print("\n... Извлечение позиций из контрактов ...")
    items_series = df["payment_targets_json"].apply(extract_contract_items_new)
    exploded = items_series.explode().dropna()
    idx_map = exploded.index
    items_df = pd.DataFrame(exploded.tolist()) if not exploded.empty else pd.DataFrame()

    if not items_df.empty:
        items_df["law"] = df.loc[idx_map, "law"].values
        items_df["price_float"] = pd.to_numeric(items_df["price"], errors="coerce").fillna(0)

        p_cnt_ktru, p_sum_ktru = build_count_sum_pivots(items_df, "ktru", value_col="price_float", limit=30)
        print_count_sum_table("КОНТРАКТЫ: ПОПУЛЯРНЫЕ ПОЗИЦИИ", p_cnt_ktru, p_sum_ktru, row_label_width=40)

        items_df["item_price_category"] = pd.Categorical(
            items_df["price_float"].apply(categorize_price),
            categories=PRICE_ORDER, ordered=True,
        )
        p_cnt_ipc, p_sum_ipc = build_count_sum_pivots(items_df, "item_price_category", value_col="price_float", row_order=PRICE_ORDER)
        print_count_sum_table("КОНТРАКТЫ: СТОИМОСТЬ ПОЗИЦИЙ", p_cnt_ipc, p_sum_ipc)
    else:
        print("Товары в контрактах не найдены.")


def analyze_contract_status():
    """
    Статус контракта × закон; конверсия закупка → контракт.
    Закупки отфильтрованы по цене И по дате публикации [DATE_FROM, DATE_TO].
    """
    print(f"\n>>> Анализ статусов контрактов (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")

    eligible = _get_eligible_registry_numbers(100_000_000)
    if not eligible:
        print("Нет данных.")
        return

    db.connect(reuse_if_open=True)
    purchases_qs = list(
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PurchaseOrder,
            Purchase.ProcurementStage,
            Purchase.InitialMaxContractPriceInCurrency,
        )
        .where(Purchase.RegistryNumber.in_(eligible))
        .dicts()
    )

    contracts_by_reg = {}
    if eligible:
        for c in (
            Contract
            .select(Contract.RegistryNumber, Contract.ContractPrice)
            .where(Contract.RegistryNumber.in_(list(eligible)))
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
    df["price"] = df["contract_price"].apply(clean_price_value)
    print(f"✓ Загружено {len(df)} записей")

    p_cnt, p_sum = build_count_sum_pivots(df, "contract_status")
    print_count_sum_table(
        "Таблица. Статус контракта/договора по законам (кол-во и сумма)",
        p_cnt, p_sum, row_label_width=40,
    )

    df_with = df[
        (df["contract_status"] != "Нет контракта")
        & df["price"].notna()
        ]
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

    df["conv_group"] = df["contract_status"].apply(
        lambda x: "Заключён контракт" if x != "Нет контракта" else "Без контракта"
    )
    p_cnt_c, p_sum_c = build_count_sum_pivots(df, "conv_group")
    print_count_sum_table(
        "Таблица. Конверсия: закупки с контрактом vs без контракта",
        p_cnt_c, p_sum_c, row_label_width=25,
    )


def analyze_suppliers():
    """Топ-30 поставщиков крупных контрактов (закупки в диапазоне дат)."""
    print(f"\n>>> Загрузка поставщиков (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")
    df = _load_suppliers()
    if df.empty:
        print("Поставщики не найдены.")
        return
    print(f"✓ Загружено {len(df)} записей поставщиков")
    p_cnt, p_sum = build_count_sum_pivots(df, "organization", limit=30)
    print_count_sum_table("ПОСТАВЩИКИ КРУПНЫХ КОНТРАКТОВ", p_cnt, p_sum, row_label_width=50)


def analyze_purchases_by_year():
    """Сводная по годам: кол-во и объём НМЦК (закупки в диапазоне дат)."""
    print(f"\n>>> Анализ закупок по годам (от 100 млн, дата публикации {DATE_FROM_STR} — {DATE_TO.date()})...")
    df = _load_purchases()
    if df.empty:
        return

    p_cnt, p_sum = build_count_sum_pivots(df, "year")
    print_count_sum_table("ЗАКУПКИ ПО ГОДАМ: ГОД × ЗАКОН (кол-во и сумма)", p_cnt, p_sum, row_label_width=15)


def analyze_vessels():
    """Анализ судовой базы: типы, верфи, годы постройки, ценовые диапазоны.
    Контракты ограничены закупками, попавшими в фильтр даты/цены."""
    print("\n>>> Загрузка данных по судам...")

    eligible = _get_eligible_registry_numbers(MIN_PRICE) # 0 — не фильтруем по цене здесь, только по дате
    db.connect(reuse_if_open=True)

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
        .dicts()
    )

    def _get_contract_id(v):
        return v.get("contract_id", v.get("contract"))

    contract_ids = {_get_contract_id(v) for v in vessels if _get_contract_id(v)}
    prices_by_contract = {}
    law_by_contract = {}
    allowed_contract_ids = set()
    if contract_ids:
        contracts = list(
            Contract.select(Contract.Id, Contract.ContractPrice, Contract.RegistryNumber)
            .where(Contract.Id.in_(contract_ids))
        )
        for c in contracts:
            prices_by_contract[c.Id] = c.ContractPrice
            if c.RegistryNumber in eligible:
                allowed_contract_ids.add(c.Id)

        reg_nums = {c.RegistryNumber for c in contracts}
        purchase_laws = {
            p.RegistryNumber: p.PurchaseOrder
            for p in Purchase.select(Purchase.RegistryNumber, Purchase.PurchaseOrder).where(Purchase.RegistryNumber.in_(reg_nums))
        }
        for c in contracts:
            law_by_contract[c.Id] = purchase_laws.get(c.RegistryNumber)

    db.close()

    if not vessels:
        print("Нет данных по судам.")
        return

    rows = []
    for v in vessels:
        cid = _get_contract_id(v)
        # оставляем только суда, чей контракт относится к закупке в нужном диапазоне дат
        # (либо у судна вовсе нет контракта — оставляем как есть, без привязки к дате)
        if cid and cid not in allowed_contract_ids:
            continue
        rows.append({
            "ship_type_rmrs":   v.get("ship_type_rmrs"),
            "ship_type_rko":    v.get("ship_type_rko"),
            "ship_class":       v.get("ship_class"),
            "year_built":       v.get("year_built"),
            "country_built":    v.get("country_built"),
            "shipyard_name":    v.get("shipyard_name"),
            "federal_district": v.get("federal_district"),
            "hull_material":    v.get("hull_material"),
            "contract_price":   prices_by_contract.get(cid),
            "law":              law_by_contract.get(cid),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("Нет судов, попадающих в выбранный диапазон дат.")
        return

    df["contract_price_num"] = pd.to_numeric(df["contract_price"], errors="coerce")
    df["law"] = df["law"].fillna("Неизвестно")
    print(f"✓ Загружено {len(df)} записей о судах")

    p_cnt, p_sum = build_count_sum_pivots(df.assign(price=df["contract_price_num"].fillna(0)), "ship_type_rmrs", limit=20)
    print_count_sum_table("СУДА: ТИП (РМРС)", p_cnt, p_sum, row_label_width=30)

    p_cnt, p_sum = build_count_sum_pivots(df.assign(price=df["contract_price_num"].fillna(0)), "ship_class", limit=20)
    print_count_sum_table("СУДА: КЛАСС", p_cnt, p_sum, row_label_width=30)

    p_cnt, p_sum = build_count_sum_pivots(df.assign(price=df["contract_price_num"].fillna(0)), "shipyard_name", limit=20)
    print_count_sum_table("СУДА: ВЕРФИ ПОСТРОЙКИ", p_cnt, p_sum, row_label_width=40)

    p_cnt, p_sum = build_count_sum_pivots(df.assign(price=df["contract_price_num"].fillna(0)), "federal_district")
    print_count_sum_table("СУДА: ФЕДЕРАЛЬНЫЙ ОКРУГ", p_cnt, p_sum, row_label_width=30)

    p_cnt, p_sum = build_count_sum_pivots(df.assign(price=df["contract_price_num"].fillna(0)), "hull_material")
    print_count_sum_table("СУДА: МАТЕРИАЛ КОРПУСА", p_cnt, p_sum, row_label_width=30)

    df_year = df.dropna(subset=["year_built"])
    if not df_year.empty:
        p_cnt, p_sum = build_count_sum_pivots(df_year.assign(price=df_year["contract_price_num"].fillna(0)), "year_built")
        print_count_sum_table("СУДА: ГОД ПОСТРОЙКИ", p_cnt, p_sum, row_label_width=15)

    df_price = df.dropna(subset=["contract_price_num"])
    if not df_price.empty:
        df_price = df_price.copy()
        df_price["price_cat"] = df_price["contract_price_num"].apply(categorize_price)
        p_cnt, p_sum = build_count_sum_pivots(df_price.assign(price=df_price["contract_price_num"]), "price_cat", row_order=PRICE_ORDER)
        print_count_sum_table("СУДА: ЦЕНОВЫЕ ДИАПАЗОНЫ КОНТРАКТА", p_cnt, p_sum)

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
def diagnose_contract_difference(min_price=MIN_PRICE):
    print("\n>>> Диагностика расхождения контрактов")

    eligible_nums = _get_eligible_registry_numbers(min_price)

    db.connect(reuse_if_open=True)

    purchase_rows = list(
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PurchaseOrder,
            Purchase.PlacementDate,
            Purchase.InitialMaxContractPriceInCurrency,
        )
        .where(Purchase.RegistryNumber.in_(eligible_nums))
        .dicts()
    )

    contract_rows = list(
        Contract
        .select(
            Contract.Id,
            Contract.RegistryNumber,
            Contract.ContractPrice,
        )
        .where(Contract.RegistryNumber.in_(eligible_nums))
        .dicts()
    )

    version_rows = list(
        ContractVersion
        .select(
            ContractVersion.id,
            ContractVersion.contract,
            ContractVersion.payment_targets_json,
            ContractVersion.process_info_json,
        )
        .where(
            ContractVersion.contract.in_(
                [row["Id"] for row in contract_rows]
            )
        )
        .dicts()
    )

    db.close()

    contract_ids = {
        row["Id"]
        for row in contract_rows
    }

    contracts_with_payment = {
        row["contract"]
        for row in version_rows
        if row["payment_targets_json"] is not None
    }

    contracts_with_process = {
        row["contract"]
        for row in version_rows
        if row["process_info_json"] is not None
    }

    print(f"Подходящих закупок: {len(eligible_nums)}")
    print(f"Контрактов по закупкам: {len(contract_ids)}")
    print(f"Контрактов с payment_targets_json: {len(contracts_with_payment)}")
    print(f"Контрактов с process_info_json: {len(contracts_with_process)}")

    print("\nКонтракты без payment_targets_json:")
    for row in contract_rows:
        if row["Id"] not in contracts_with_payment:
            print(
                row["Id"],
                row["RegistryNumber"],
                row["ContractPrice"],
            )

    print("\nКонтракты без process_info_json:")
    for row in contract_rows:
        if row["Id"] not in contracts_with_process:
            print(
                row["Id"],
                row["RegistryNumber"],
                row["ContractPrice"],
            )

    print("\nСумма всех контрактов:")
    print(
        sum(
            clean_price_value(row["ContractPrice"]) or 0
            for row in contract_rows
        )
    )

    print("\nСумма контрактов с payment_targets_json:")
    print(
        sum(
            clean_price_value(row["ContractPrice"]) or 0
            for row in contract_rows
            if row["Id"] in contracts_with_payment
        )
    )

    print("\nСумма контрактов с process_info_json:")
    print(
        sum(
            clean_price_value(row["ContractPrice"]) or 0
            for row in contract_rows
            if row["Id"] in contracts_with_process
        )
    )
if __name__ == "__main__":

    print("=" * 60)
    print("  АНАЛИЗ ЗАКУПОК (Peewee / SQLite) — вся БД")
    print(f"  Диапазон дат публикации: {DATE_FROM_STR} — {DATE_TO.date()}")
    print("=" * 60)

    analyze_purchases()
    analyze_okpd2_usage()
    analyze_item_names()
    analyze_contracts()
    analyze_contract_status()
    analyze_suppliers()
    analyze_purchases_by_year()
    analyze_vessels()
