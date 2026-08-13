"""
analyze_contract_versions_peewee.py
Анализ версий контрактов на основе Peewee-моделей (SQLite).
Все данные — без фильтров по дате и минимальной цене.
Во все таблицы, где есть разбивка по law, добавлена конверсия (доля, %)
внутри каждого закона и общий итог по обоим законам.
"""
import os
import re
import json
import sqlite3
from datetime import datetime
import pandas as pd
from smtuIdle.BD.initialize_db import db
from smtuIdle.BD.models import *
LAWS = ("44-ФЗ", "223-ФЗ")
DATE_FROM_STR = "15.04.2023"
MIN_PRICE = 100_000_000
DATE_FROM = pd.to_datetime(DATE_FROM_STR, format="%d.%m.%Y")
DATE_TO = pd.Timestamp.today().normalize()
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




def _date_in_range(value) -> bool:
    """
    Проверяет, попадает ли дата публикации закупки в диапазон
    [15.04.2023, сегодняшняя дата] включительно.

    Ожидаемый формат даты в БД: DD.MM.YYYY.
    """
    if value is None or pd.isna(value):
        return False

    parsed = pd.to_datetime(
        str(value).strip(),
        format="%d.%m.%Y",
        errors="coerce",
    )

    # Резервный вариант для нестандартных записей
    if pd.isna(parsed):
        parsed = pd.to_datetime(
            str(value).strip(),
            dayfirst=True,
            errors="coerce",
        )

    if pd.isna(parsed):
        return False

    return DATE_FROM <= parsed.normalize() <= DATE_TO
def clean_price_value(value):
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        s = (str(value)
             .replace("\xa0", "").replace("\u202f", "")
             .replace(" ", "").replace(",", ".").replace("₽", "").strip())
        return float(s) if s else None
    except (ValueError, TypeError):
        return None


def fmt(x) -> str:
    """0 / None → '−', иначе разряды через пробел."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "−"
    if x == 0:
        return "−"
    return "{:,.0f}".format(x).replace(",", " ")


def _pct(value, total):
    """Доля value от total в процентах, строкой вида '12.3%'. Безопасна при total==0/NaN."""
    try:
        if total is None or total == 0 or pd.isna(total):
            return "0.0%"
        return f"{(value / total) * 100:.1f}%"
    except Exception:
        return "0.0%"


def normalize_law(law: str) -> str:
    """Приводит произвольное значение law к каноничному '44-ФЗ' / '223-ФЗ' / 'Прочее'."""
    s = str(law or "").strip()
    if "44" in s:
        return "44-ФЗ"
    if "223" in s:
        return "223-ФЗ"
    return "Прочее"


def build_count_sum_pivots(df: pd.DataFrame, row_col: str, value_col: str,
                           row_order=None, limit=None):
    """
    Строит сводные таблицы кол-во/сумма по (row_col × law) с итогами.
    Универсальна для любой группирующей колонки:
      - если row_order задан — строки идут в этом порядке;
      - если row_order не задан — строки сортируются по убыванию общего
        количества, с возможностью обрезать топ-N через limit.
    Возвращает пару DataFrame (p_cnt, p_sum) с колонками 44-ФЗ / 223-ФЗ / Всего
    и строкой "Общий итог".
    """
    d = df.copy()
    d["_law_norm"] = d["law"].apply(normalize_law)
    grouped = d.groupby([row_col, "_law_norm"])[value_col].agg(["count", "sum"])
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
                          row_label_width=40):
    """
    Печатает сводную таблицу кол-во/сумма по законам.
    В каждой ячейке — абсолютное значение и доля (конверсия) относительно
    ОБЩЕГО ИТОГА по соответствующему закону/столбцу "Всего".
    """
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

        c44_s  = f"{int(c44):>6} ({_pct(c44, total_cnt['44-ФЗ'])})" if c44 else "−"
        c223_s = f"{int(c223):>6} ({_pct(c223, total_cnt['223-ФЗ'])})" if c223 else "−"
        ctot_s = f"{int(ctot):>6} ({_pct(ctot, total_cnt['Всего'])})" if ctot else "−"
        print(f"{str(row):<{W}} {'кол-во':<15} {c44_s:>22} {c223_s:>22} {ctot_s:>22}")

        s44_s  = f"{fmt(s44):>12} ({_pct(s44, total_sum['44-ФЗ'])})" if s44 else "−"
        s223_s = f"{fmt(s223):>12} ({_pct(s223, total_sum['223-ФЗ'])})" if s223 else "−"
        stot_s = f"{fmt(stot):>12} ({_pct(stot, total_sum['Всего'])})" if stot else "−"
        print(f"{'':^{W}} {'сумма, руб':<15} {s44_s:>22} {s223_s:>22} {stot_s:>22}")

    print("-" * 140)


def parse_version_label(label):
    """
    Извлекает номер и дату версии.

    Пример:
    '№ 123 (Версия № 3 от 15.04.2021, действующая версия)'
    →
    (3, Timestamp('2021-04-15'))
    """

    if not label:
        return None, None

    # На случай, если значение версии хранится числом.
    if isinstance(label, (int, float)) and not pd.isna(label):
        return int(label), None

    if not isinstance(label, str):
        return None, None

    num_match = re.search(
        r"Версия\s*№\s*(\d+)",
        label,
        re.IGNORECASE,
    )

    version_num = (
        int(num_match.group(1))
        if num_match
        else None
    )

    date_match = re.search(
        r"от\s+(\d{2}\.\d{2}\.\d{4})",
        label,
    )

    version_date = None

    if date_match:
        version_date = pd.to_datetime(
            date_match.group(1),
            format="%d.%m.%Y",
            errors="coerce",
        )

    return version_num, version_date

# ─────────────────────────────────────────────────────────────────────────────
# Извлечение данных из JSON
# ─────────────────────────────────────────────────────────────────────────────

def load_first_version_prices(
    contract_ids: list,
) -> pd.DataFrame:
    """
    Возвращает цену самой первой версии каждого контракта.

    Первая версия определяется по:
      1. номеру версии;
      2. дате версии;
      3. id версии.

    Контракты без версий возвращаются без строки
    и затем получат NaN после left merge.
    """

    result_columns = [
        "contract_id",
        "first_version_price_raw",
        "first_version_label",
        "first_version_id",
    ]

    if not contract_ids:
        return pd.DataFrame(
            columns=result_columns
        )

    db.connect(reuse_if_open=True)

    try:
        versions = list(
            ContractVersion
            .select(
                ContractVersion.id,
                ContractVersion.contract,
                ContractVersion.version,
                ContractVersion.contract_price.alias(
                    "first_version_price_raw"
                ),
            )
            .where(
                ContractVersion.contract.in_(contract_ids)
            )
            .dicts()
        )
    finally:
        db.close()

    if not versions:
        return pd.DataFrame(
            columns=result_columns
        )

    df = pd.DataFrame(versions)

    parsed = df["version"].apply(
        parse_version_label
    )

    df["version_num"] = parsed.apply(
        lambda value: value[0]
    )

    df["version_date"] = parsed.apply(
        lambda value: value[1]
    )

    # Версии с неизвестным номером отправляем
    # после нормально распознанных версий.
    df["version_num_sort"] = (
        pd.to_numeric(
            df["version_num"],
            errors="coerce",
        )
        .fillna(10**9)
    )

    # Дата нужна как второй критерий.
    # Если даты нет, ставим максимальную дату.
    df["version_date_sort"] = pd.to_datetime(
        df["version_date"],
        errors="coerce",
    ).fillna(pd.Timestamp.max)

    df["first_version_price_raw"] = (
        df["first_version_price_raw"]
        .apply(clean_price_value)
    )

    # Сначала версия № 1, затем № 2, № 3 и т. д.
    # При одинаковом номере используется дата,
    # затем id записи.
    df = df.sort_values(
        [
            "contract",
            "version_num_sort",
            "version_date_sort",
            "id",
        ],
        ascending=True,
    )

    first_versions = (
        df
        .drop_duplicates(
            subset=["contract"],
            keep="first",
        )
        .rename(
            columns={
                "contract": "contract_id",
                "version": "first_version_label",
                "id": "first_version_id",
            }
        )
    )

    return first_versions[
        result_columns
    ].reset_index(drop=True)
def extract_contract_items_new(json_data):
    data = _parse_json(json_data)
    if not isinstance(data, dict):
        return []
    extracted = []
    try:
        for item in data.get("объекты_закупки", {}).get("items", []):
            if item.get("kind") != "table":
                continue
            for row in item.get("table", {}).get("rows", []):
                ktru_raw = row.get("ktru")
                price = row.get("price")
                qty = row.get("quantity") or row.get("qty") or row.get("количество")
                ktru_clean = str(ktru_raw).replace("\n", " ").strip() if ktru_raw else None
                price_val = clean_price_value(price)
                if ktru_clean or price_val is not None:
                    extracted.append({
                        "ktru": ktru_clean,
                        "price": price_val,
                        "qty": clean_price_value(qty),
                    })
    except Exception:
        pass
    return extracted


def extract_execution_stages(process_json):
    data = _parse_json(process_json)
    if not isinstance(data, dict):
        return []
    records = []
    try:
        for item in data.get("исполнение_контракта", {}).get("items", []):
            if item.get("kind") != "table":
                continue
            for row in item.get("table", {}).get("rows", []):
                records.append({
                    "stage": row.get("ЭТАП КОНТРАКТА", ""),
                    "completed": row.get("ИСПОЛНЕНИЕ ЗАВЕРШЕНО", ""),
                    "paid_raw": row.get("ФАКТИЧЕСКИ ОПЛАЧЕНО, ₽"),
                    "obligated_raw": row.get("СТОИМОСТЬ ИСПОЛНЕННЫХ ОБЯЗАТЕЛЬСТВ, ₽"),
                    "has_penalty": row.get("НЕУСТОЙКИ (ШТРАФЫ, ПЕНИ)", "Нет"),
                })
    except Exception:
        pass
    return records


def extract_penalties(process_json):
    data = _parse_json(process_json)
    if not isinstance(data, dict):
        return []
    records = []
    try:
        section_key = "информация_о_начислении_неустоек_штрафов_пеней"
        for item in data.get(section_key, {}).get("items", []):
            if item.get("kind") != "table":
                continue
            for row in item.get("table", {}).get("rows", []):
                requirement_raw = row.get("ТРЕБОВАНИЕ", "") or ""
                code_match = re.match(r"^(\d+)", requirement_raw.strip())
                req_code = code_match.group(1) if code_match else "прочее"
                payer_raw = row.get("ПРИЧИНА НАЧИСЛЕНИЯ", "") or ""
                inn_match = re.search(r"ИНН[:\s]+(\d{10,12})", payer_raw)
                inn = inn_match.group(1) if inn_match else None
                nachisleno_raw = row.get("НАЧИСЛЕНО, ₽", "") or ""
                oplacheno_raw = row.get("ОПЛАЧЕНО, ₽", "") or ""
                records.append({
                    "requirement_code": req_code,
                    "requirement_text": requirement_raw,
                    "payer": payer_raw,
                    "inn": inn,
                    "charged_doc": nachisleno_raw,
                    "charged": clean_price_value(nachisleno_raw),
                    "paid": clean_price_value(oplacheno_raw),
                })
    except Exception:
        pass
    return records

# ─────────────────────────────────────────────────────────────────────────────
# Загрузка данных через Peewee (вся БД)
# ─────────────────────────────────────────────────────────────────────────────

def _purchases_map(
    min_price: float = MIN_PRICE,
) -> dict:
    result = {}

    purchases = (
        Purchase
        .select(
            Purchase.RegistryNumber,
            Purchase.PurchaseOrder,
            Purchase.InitialMaxContractPriceInCurrency,
            Purchase.PlacementDate,
        )
        .where(
            Purchase.InitialMaxContractPriceInCurrency >= min_price
        )
        .dicts()
    )

    for p in purchases:
        if not _date_in_range(p["PlacementDate"]):
            continue

        registry_number = (
            str(p["RegistryNumber"])
            .strip()
            if p["RegistryNumber"] is not None
            else ""
        )

        if not registry_number:
            continue

        result[registry_number] = {
            "law": p["PurchaseOrder"],
            "initial_price": p[
                "InitialMaxContractPriceInCurrency"
            ],
            "published": p["PlacementDate"],
        }

    return result
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

    df = _filter_by_date_range(
        df,
        "published",
    )

    return set(
        df["RegistryNumber"]
        .astype(str)
        .str.strip()
        .tolist()
    )

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
def load_versions_data() -> pd.DataFrame:
    """
    Загружает контракты через тот же SQL-фильтр, что и контрольный запрос.

    Фильтры:
      - НМЦК >= MIN_PRICE;
      - дата публикации от DATE_FROM до текущей даты;
      - TRIM для RegistryNumber;
      - один контракт — одна строка.
    """

    print(
        f"\n>>> Загрузка данных версий через SQL "
        f"(дата публикации: {DATE_FROM_STR} — "
        f"{DATE_TO.strftime('%d.%m.%Y')})..."
    )

    date_from_sql = DATE_FROM.strftime("%Y-%m-%d")

    sql = """
        WITH filtered_purchases AS (
            SELECT
                p."Id" AS purchase_id,
                TRIM(
                    CAST(p."RegistryNumber" AS TEXT)
                ) AS registry_number,
                p."PurchaseOrder" AS law,
                p."PlacementDate" AS published,
                p."InitialMaxContractPriceInCurrency"
                    AS initial_price
            FROM "purchase" AS p
            WHERE p."InitialMaxContractPriceInCurrency" >= ?
              AND date(p."PlacementDate")
                  BETWEEN date(?)
                      AND date('now', 'localtime')
        )
        SELECT
            c."Id" AS contract_id,
            TRIM(
                CAST(c."RegistryNumber" AS TEXT)
            ) AS reg_number,
            c."ContractPrice" AS contract_price_raw,
            fp.law AS law,
            fp.published AS published,
            fp.initial_price AS initial_price
        FROM filtered_purchases AS fp
        INNER JOIN "contract" AS c
            ON TRIM(
                CAST(c."RegistryNumber" AS TEXT)
            ) = fp.registry_number
        GROUP BY
            c."Id",
            reg_number,
            c."ContractPrice",
            fp.law,
            fp.published,
            fp.initial_price
        ORDER BY c."Id"
    """

    db.connect(reuse_if_open=True)

    try:
        cursor = db.execute_sql(
            sql,
            (
                MIN_PRICE,
                date_from_sql,
            ),
        )

        columns = [
            column[0]
            for column in cursor.description
        ]

        rows = cursor.fetchall()

    finally:
        db.close()

    if not rows:
        print("Нет контрактов по заданному фильтру.")
        return pd.DataFrame()

    df = pd.DataFrame(
        rows,
        columns=columns,
    )

    # Один contract_id — одна строка.
    df = (
        df
        .drop_duplicates(subset=["contract_id"])
        .reset_index(drop=True)
    )

    contract_ids = (
        df["contract_id"]
        .dropna()
        .tolist()
    )

    # Загружаем количество версий для уже выбранных контрактов.
    version_counts = {}

    db.connect(reuse_if_open=True)

    try:
        version_rows = list(
            ContractVersion
            .select(
                ContractVersion.contract,
            )
            .where(
                ContractVersion.contract.in_(contract_ids)
            )
            .dicts()
        )
    finally:
        db.close()

    for row in version_rows:
        contract_id = row["contract"]

        version_counts[contract_id] = (
            version_counts.get(contract_id, 0) + 1
        )

    df["version_count"] = (
        df["contract_id"]
        .map(version_counts)
        .fillna(0)
        .astype(int)
    )

    df["law"] = (
        df["law"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "Нет данных")
    )

    df["reg_number"] = (
        df["reg_number"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ВАЖНО:
    # здесь НЕ нужно повторно делать df = pd.DataFrame(rows)

    first_version_prices = load_first_version_prices(
        df["contract_id"].tolist()
    )

    df = df.merge(
        first_version_prices,
        on="contract_id",
        how="left",
    )

    print(f"✓ Строк после запроса: {len(df)}")
    print(
        f"✓ Уникальных contract_id: "
        f"{df['contract_id'].nunique()}"
    )
    print(
        f"✓ Контрактов с ценой первой версии: "
        f"{df['first_version_price_raw'].notna().sum()}"
    )
    print(
        f"✓ Контрактов без цены первой версии: "
        f"{df['first_version_price_raw'].isna().sum()}"
    )

    return df
def load_versions_payment() -> pd.DataFrame:
    """
    Загружает все версии контрактов с payment_targets_json.
    """
    print("\n>>> Загрузка версий с payment_targets_json (вся БД)...")

    versions = list(
        ContractVersion.select(
            ContractVersion.id,
            ContractVersion.contract,
            ContractVersion.version,
            ContractVersion.payment_targets_json,
        )
        .where(ContractVersion.payment_targets_json.is_null(False))
        .dicts()
    )

    if not versions:
        return pd.DataFrame()

    contract_ids = list({v["contract"] for v in versions})

    contracts = {
        c["Id"]: c["RegistryNumber"]
        for c in Contract.select(Contract.Id, Contract.RegistryNumber)
        .where(Contract.Id.in_(contract_ids))
        .dicts()
    }

    # Кол-во версий на контракт
    version_counts = {}
    for cv in (
        ContractVersion
        .select(ContractVersion.contract)
        .where(ContractVersion.contract.in_(contract_ids))
        .tuples()
    ):
        cid = cv[0]
        version_counts[cid] = version_counts.get(cid, 0) + 1

    pmap = _purchases_map()
    rows = []
    for v in versions:
        cid = v["contract"]
        reg = contracts.get(cid, "")
        pm = pmap.get(reg, {})
        rows.append({
            "version_id": v["id"],
            "contract_id": cid,
            "version_label": v["version"],
            "reg_number": reg,
            "law": pm.get("law", ""),
            "initial_price": pm.get("initial_price"),
            "published": pm.get("published"),
            "payment_targets_json": _parse_json(v["payment_targets_json"]),
            "version_total": version_counts.get(cid, 0),
        })

    df = pd.DataFrame(rows)
    print(f"✓ Загружено {len(df)} версий | контрактов: {df['reg_number'].nunique()}")
    return df
def load_process_info() -> pd.DataFrame:

    print(
        f"\n>>> Загрузка process_info_json "
        f"(дата публикации закупки: {DATE_FROM_STR} — {DATE_TO.strftime('%d.%m.%Y')})..."
    )

    pmap = _purchases_map()

    if not pmap:
        print("Нет закупок, попадающих в заданный диапазон дат.")
        return pd.DataFrame()

    eligible_registry_numbers = set(pmap.keys())

    contracts = {
        c["Id"]: c["RegistryNumber"]
        for c in (
            Contract
            .select(Contract.Id, Contract.RegistryNumber)
            .where(
                Contract.RegistryNumber.in_(eligible_registry_numbers)
            )
            .dicts()
        )
    }

    if not contracts:
        print("Нет контрактов в заданном диапазоне дат.")
        return pd.DataFrame()

    eligible_contract_ids = set(contracts.keys())

    versions = list(
        ContractVersion
        .select(
            ContractVersion.id,
            ContractVersion.contract,
            ContractVersion.version,
            ContractVersion.process_info_json,
        )
        .where(
            ContractVersion.contract.in_(eligible_contract_ids),
            ContractVersion.process_info_json.is_null(False),
        )
        .dicts()
    )

    if not versions:
        return pd.DataFrame()

    # Количество всех версий по каждому подходящему контракту
    version_counts = {}

    for cv in (
        ContractVersion
        .select(ContractVersion.contract)
        .where(
            ContractVersion.contract.in_(eligible_contract_ids)
        )
        .dicts()
    ):
        cid = cv["contract"]
        version_counts[cid] = version_counts.get(cid, 0) + 1

    rows = []

    for v in versions:
        cid = v["contract"]
        reg = contracts.get(cid, "")
        pm = pmap.get(reg, {})

        rows.append({
            "version_id": v["id"],
            "contract_id": cid,
            "version_label": v["version"],
            "reg_number": reg,
            "law": pm.get("law", ""),
            "initial_price": pm.get("initial_price"),
            "published": pm.get("published"),
            "process_info_json": _parse_json(
                v["process_info_json"]
            ),
            "version_total": version_counts.get(cid, 0),
        })

    df = pd.DataFrame(rows)

    df = keep_latest_process_version(df)

    print(
        f"✓ Загружено {len(df)} последних версий | "
        f"контрактов: {df['reg_number'].nunique()}"
    )

    return df


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Цена закупки / НМЦК.
    df["purchase_price"] = (
        pd.to_numeric(
            df["initial_price"],
            errors="coerce",
        )
        .replace(0.0, float("nan"))
    )

    # Цена контракта первой версии.
    df["first_version_price"] = (
        df["first_version_price_raw"]
        .apply(clean_price_value)
    )

    df["published_dt"] = pd.to_datetime(
        df["published"],
        format="%d.%m.%Y",
        errors="coerce",
    )

    df["year"] = df["published_dt"].dt.year

    df["law"] = (
        df["law"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "Нет данных")
    )

    df["reg_number"] = (
        df["reg_number"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["version_count"] = (
        pd.to_numeric(
            df["version_count"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    # Главная формула:
    # цена закупки - цена контракта первой версии.
    df["delta"] = (
        df["purchase_price"]
        - df["first_version_price"]
    )

    # Процент относительно цены закупки.
    df["delta_pct"] = (
        df["delta"]
        .div(df["purchase_price"])
        .mul(100)
        .round(2)
    )

    # Поля для отображения.
    df["purchase_price_display"] = (
        df["purchase_price"]
        .apply(
            lambda x: fmt(x)
            if pd.notna(x)
            else "Нет данных"
        )
    )

    df["first_version_price_display"] = (
        df["first_version_price"]
        .apply(
            lambda x: fmt(x)
            if pd.notna(x)
            else "Нет данных"
        )
    )

    df["delta_display"] = (
        df["delta"]
        .apply(
            lambda x: fmt(x)
            if pd.notna(x)
            else "Нет данных"
        )
    )

    df["delta_pct_display"] = (
        df["delta_pct"]
        .apply(
            lambda x: f"{x:.1f}%"
            if pd.notna(x)
            else "Нет данных"
        )
    )

    return df


def explode_items(df: pd.DataFrame) -> pd.DataFrame:
    parsed = df["version_label"].apply(parse_version_label)
    df = df.copy()
    df["version_num"] = parsed.apply(lambda x: x[0])
    df["version_date"] = parsed.apply(lambda x: x[1])
    df["version_sort"] = df["version_date"].apply(
        lambda d: d.timestamp() if pd.notna(d) else float("inf")
    )

    records = []
    for _, row in df.iterrows():
        items = extract_contract_items_new(row["payment_targets_json"])
        for it in items:
            records.append({
                "version_id": row["version_id"],
                "version_num": row["version_num"],
                "version_date": row["version_date"],
                "version_sort": row["version_sort"],
                "version_label": row["version_label"],
                "contract_id": row["contract_id"],
                "reg_number": row["reg_number"],
                "law": row["law"],
                "initial_price": row["initial_price"],
                "version_total": row["version_total"],
                "ktru": it["ktru"],
                "price": it["price"],
                "qty": it["qty"],
            })
    result = pd.DataFrame(records)
    if not result.empty:
        print(f"✓ Извлечено {len(result)} позиций | контрактов: {result['reg_number'].nunique()}")
    return result
def diagnose_json_structure():
    """Печатает ключи верхнего уровня common_info_json первых 3 версий."""
    versions = list(
        ContractVersion
        .select(ContractVersion.id, ContractVersion.common_info_json)
        .where(ContractVersion.common_info_json.is_null(False))
        .limit(3)
        .namedtuples()
    )
    for v in versions:
        j = _parse_json(v.common_info_json)
        if isinstance(j, dict):
            print(f"\n[version_id={v.id}] Ключи: {list(j.keys())}")
            for top_key, section in j.items():
                if isinstance(section, dict):
                    print(f"  [{top_key}] → items: {len(section.get('items', []))}")
                    for item in section.get("items", [])[:2]:
                        print(f"    kind={item.get('kind')} keys={list(item.keys())}")
                        if item.get("kind") == "field_list":
                            for f in item.get("fields", [])[:5]:
                                print(f"      label={f.get('label')!r} value={f.get('value')!r}")

def analyze_price_vs_nmck(df: pd.DataFrame):
    print(f"\n{'=' * 140}")
    print(
        "ТАБЛИЦА 1. Цена закупки в валюте "
        "vs цена контракта первой версии"
    )
    print(f"{'=' * 140}")

    df_all = (
        df
        .drop_duplicates(
            subset=["contract_id"]
        )
        .copy()
    )

    # Для расчёта нужны цена закупки
    # и цена первой версии.
    df_calc = df_all[
        df_all["purchase_price"].notna()
        & df_all["first_version_price"].notna()
        & (df_all["purchase_price"] != 0)
    ].copy()

    total_all = len(df_all)
    total_calc = len(df_calc)
    total_no_data = total_all - total_calc

    print(
        f"\n  Всего контрактов              : "
        f"{total_all}"
    )
    print(
        f"  С данными для сравнения       : "
        f"{total_calc}"
    )
    print(
        f"  Без данных для сравнения      : "
        f"{total_no_data}"
    )

    if not df_calc.empty:
        # delta > 0:
        # закупочная цена больше цены первой версии.
        economy = (
            df_calc["delta"] > 0
        ).sum()

        # delta < 0:
        # цена первой версии выше цены закупки.
        overpayment = (
            df_calc["delta"] < 0
        ).sum()

        equal = (
            df_calc["delta"] == 0
        ).sum()

        print(
            f"\n  Цена первой версии ниже закупки : "
            f"{economy} "
            f"({economy / total_calc * 100:.1f}%)"
        )
        print(
            f"  Цена первой версии выше закупки : "
            f"{overpayment} "
            f"({overpayment / total_calc * 100:.1f}%)"
        )
        print(
            f"  Цены равны                       : "
            f"{equal} "
            f"({equal / total_calc * 100:.1f}%)"
        )

        print(
            f"  Средняя дельта, %                : "
            f"{df_calc['delta_pct'].mean():.2f}%"
        )

        print(
            f"  Суммарная экономия               : "
            f"{fmt(df_calc.loc[
                df_calc['delta'] > 0,
                'delta'
            ].sum())} руб."
        )

        print(
            f"  Суммарный перерасход             : "
            f"{fmt(abs(df_calc.loc[
                df_calc['delta'] < 0,
                'delta'
            ].sum()))} руб."
        )

    print(
        f"\n{'Реестровый номер':<28} "
        f"{'Закон':<10} "
        f"{'Версий':>7} "
        f"{'Цена закупки':>20} "
        f"{'Цена первой версии':>24} "
        f"{'Δ руб.':>20} "
        f"{'Δ %':>10}"
    )
    print("-" * 140)

    for _, row in df_all.iterrows():
        purchase_price = (
            fmt(row["purchase_price"])
            if pd.notna(row["purchase_price"])
            else "Нет данных"
        )

        first_version_price = (
            fmt(row["first_version_price"])
            if pd.notna(row["first_version_price"])
            else "Нет данных"
        )

        delta = (
            fmt(row["delta"])
            if pd.notna(row["delta"])
            else "Нет данных"
        )

        delta_pct = (
            f"{row['delta_pct']:.1f}%"
            if pd.notna(row["delta_pct"])
            else "Нет данных"
        )

        print(
            f"{str(row['reg_number']):<28} "
            f"{str(row['law']):<10} "
            f"{int(row['version_count']):>7} "
            f"{purchase_price:>20} "
            f"{first_version_price:>24} "
            f"{delta:>20} "
            f"{delta_pct:>10}"
        )

    print("-" * 140)

    no_data = df_all[
        df_all["purchase_price"].isna()
        | df_all["first_version_price"].isna()
    ]

    if not no_data.empty:
        print("\nКонтракты без данных для сравнения:")

        for _, row in no_data.iterrows():
            print(
                f"  {row['reg_number']} | "
                f"закупка: "
                f"{row['purchase_price_display']} | "
                f"первая версия: "
                f"{row['first_version_price_display']}"
            )

    return df_all

def analyze_by_law(df_v: pd.DataFrame):
    print(f"\n{'=' * 90}")
    print("ТАБЛИЦА 2. Сводная по законам: contract_price vs НМЦК")
    print(f"{'=' * 90}")

    df_v = (
        df_v
        .drop_duplicates(subset=["contract_id"])
        .copy()
    )

    df_calc = df_v[
        df_v["purchase_price"].notna()
        & df_v["first_version_price"].notna()
        & (df_v["purchase_price"] != 0)
        ].copy()

    for law in LAWS:
        sub_all = df_v[
            df_v["law"].apply(normalize_law) == law
        ]

        sub = df_calc[
            df_calc["law"].apply(normalize_law) == law
        ]

        if sub_all.empty:
            print(f"\n  {law}: нет данных")
            continue

        print(f"\n  {law}")
        print(f"    Всего контрактов             : {len(sub_all)}")
        print(f"    С данными для сравнения      : {len(sub)}")
        print(
            f"    Без данных для сравнения     : "
            f"{len(sub_all) - len(sub)}"
        )

        if sub.empty:
            print("    Расчёт дельты невозможен.")
            continue

        total = len(sub)

        inc = (sub["delta"] > 0).sum()
        dec = (sub["delta"] < 0).sum()
        unch = (sub["delta"] == 0).sum()

        print(
            f"    Цена выросла (> НМЦК)        : "
            f"{inc} ({inc / total * 100:.1f}%)"
        )
        print(
            f"    Цена упала (< НМЦК)          : "
            f"{dec} ({dec / total * 100:.1f}%)"
        )
        print(
            f"    Цена равна НМЦК              : "
            f"{unch} ({unch / total * 100:.1f}%)"
        )
        print(
            f"    Средняя дельта %             : "
            f"{sub['delta_pct'].mean():.2f}%"
        )
        print(
            f"    Суммарный перерасход         : "
            f"{fmt(sub.loc[sub['delta'] > 0, 'delta'].sum())} руб."
        )
        print(
            f"    Суммарная экономия           : "
            f"{fmt(abs(sub.loc[sub['delta'] < 0, 'delta'].sum()))} руб."
        )

    # Для общей суммы контрактов используем все контракты,
    # а не только те, где рассчитана дельта.
    df_pivot = df_v.copy()
    df_pivot["_dummy_group"] = "Все контракты"
    df_pivot["purchase_price"] = (
        df_pivot["purchase_price"]
        .fillna(0)
    )

    p_cnt, p_sum = build_count_sum_pivots(
        df_pivot,
        "_dummy_group",
        "purchase_price",
    )

    print_count_sum_table(
        "ТАБЛИЦА 2а. Цена закупки по законам",
        p_cnt,
        p_sum,
        row_label_width=30,
    )

def analyze_delta_distribution(df_v: pd.DataFrame):
    print(f"\n{'=' * 70}")
    print("ТАБЛИЦА 3. Распределение по диапазонам Δ%")
    print(f"{'=' * 70}")

    bins = [
        -float("inf"),
        -50,
        -20,
        -5,
        0,
        5,
        20,
        50,
        float("inf"),
    ]

    labels = [
        "< -50%",
        "-50% … -20%",
        "-20% … -5%",
        "-5% … 0%",
        "0% … +5%",
        "+5% … +20%",
        "+20% … +50%",
        "> +50%",
        "Нет данных",
    ]

    df_v = (
        df_v
        .drop_duplicates(subset=["contract_id"])
        .copy()
    )

    has_delta = df_v["delta_pct"].notna()

    df_v["bin"] = "Нет данных"

    df_v.loc[has_delta, "bin"] = pd.cut(
        df_v.loc[has_delta, "delta_pct"],
        bins=bins,
        labels=labels[:-1],
        include_lowest=True,
    ).astype(str)

    # Чтобы контракты без delta тоже учитывались в количестве,
    # для них сумма устанавливается равной нулю.
    df_v["delta_for_sum"] = (
        df_v["delta"]
        .fillna(0)
    )

    p_cnt, p_sum = build_count_sum_pivots(
        df_v,
        "bin",
        "delta_for_sum",
        row_order=labels,
    )

    print_count_sum_table(
        "Диапазоны Δ% по законам "
        "(количество и Σ Δ, руб.)",
        p_cnt,
        p_sum,
        row_label_width=20,
    )

def analyze_by_year(df_v: pd.DataFrame):
    """ТАБЛИЦА 4: динамика по годам, с конверсией по законам."""
    print(f"\n{'=' * 70}")
    print("ТАБЛИЦА 4. Динамика по годам: среднее Δ%")
    print(f"{'=' * 70}")

    yearly = df_v.groupby("year").agg(
        контрактов=("reg_number", "count"),
        avg_pct=("delta_pct", "mean"),
        sum_delta=("delta", "sum"),
    ).reset_index()

    print(f"\n{'Год':<8} {'Контрактов':>12} {'Среднее Δ %':>14} {'Суммарная Δ, руб':>22}")
    print("-" * 60)
    for _, row in yearly.iterrows():
        print(f"{int(row['year']):<8} {int(row['контрактов']):>12} "
              f"{row['avg_pct']:>13.2f}% {fmt(row['sum_delta']):>22}")
    print("-" * 60)

    df_v = df_v.dropna(subset=["year"]).copy()
    years_order = sorted(df_v["year"].unique().tolist())
    p_cnt, p_sum = build_count_sum_pivots(df_v, "year", "delta", row_order=years_order)
    print_count_sum_table("Контракты по годам и законам (кол-во и Σ Δ, руб.)", p_cnt, p_sum, row_label_width=15)


def analyze_version_counts(df: pd.DataFrame):
    """ТАБЛИЦА 5: распределение по количеству версий, с конверсией по законам."""
    print(f"\n{'=' * 60}")
    print("ТАБЛИЦА 5. Распределение контрактов по количеству версий")
    print(f"{'=' * 60}")

    bins = [0, 1, 2, 3, 5, 10, float("inf")]
    labels = ["1", "2", "3", "4–5", "6–10", "> 10"]
    df = df.copy()
    df["bin"] = pd.cut(df["version_count"], bins=bins, labels=labels)
    summary = df.groupby("bin", observed=True)["reg_number"].count()

    print(f"\n{'Кол-во версий':<15} {'Контрактов':>12}")
    print("-" * 30)
    for label, cnt in summary.items():
        print(f"{label:<15} {cnt:>12}")
    print("-" * 30)
    print(f"{'Итого':<15} {summary.sum():>12}")
    print(f"\n  Среднее кол-во версий : {df['version_count'].mean():.2f}")
    print(f"  Максимум версий       : {int(df['version_count'].max())}")

    df["_dummy_price"] = df["version_count"]
    p_cnt, p_sum = build_count_sum_pivots(df, "bin", "_dummy_price", row_order=labels)
    print_count_sum_table("Версии по законам (кол-во контрактов и Σ версий)", p_cnt, p_sum, row_label_width=18)


def analyze_item_price_changes(items_df: pd.DataFrame):
    print(f"\n{'=' * 140}")
    print("ТАБЛИЦА 6. Изменение цены позиций КТРУ: первая → последняя версия контракта")
    print(f"{'=' * 140}")

    df = items_df[items_df["price"].notna() & items_df["ktru"].notna()].copy()
    if df.empty:
        print("Нет позиций с заполненными КТРУ и ценой.")
        return None

    key = ["reg_number", "ktru"]
    df = df.sort_values(["reg_number", "ktru", "version_sort"])
    min_sort = df.groupby(key)["version_sort"].transform("min")
    max_sort = df.groupby(key)["version_sort"].transform("max")

    price_v1 = (
        df[df["version_sort"] == min_sort].groupby(key)["price"]
        .mean().rename("price_v1")
    )

    last_rows = (
        df[df["version_sort"] == max_sort].groupby(key).last()
        [["price", "version_total", "law", "initial_price", "version_label"]]
        .rename(columns={"price": "price_vN", "version_label": "version_last_label"})
    )

    first_label = (
        df[df["version_sort"] == min_sort].groupby(key)["version_label"]
        .first().rename("version_first_label")
    )

    merged = last_rows.join(price_v1).join(first_label).reset_index()
    merged = merged[merged["price_v1"] != merged["price_vN"]].copy()
    merged["delta"] = merged["price_vN"] - merged["price_v1"]
    merged["delta_pct"] = (merged["delta"] / merged["price_v1"] * 100).round(2)

    total_all = len(price_v1)
    total = len(merged)
    inc = (merged["delta"] > 0).sum()
    dec = (merged["delta"] < 0).sum()

    print(f"\n  Всего позиций (контракт × КТРУ)  : {total_all}")
    print(f"  Из них с изменением цены          : {total}")
    if total:
        print(f"    Цена выросла (vN > v1)          : {inc} ({inc/total*100:.1f}%)")
        print(f"    Цена упала (vN < v1)            : {dec} ({dec/total*100:.1f}%)")

    full = merged.reindex(merged["delta"].abs().sort_values(ascending=False).index)

    print(f"\n{'Реестровый номер':<28} {'КТРУ':<35} {'Версий':>6} "
          f"{'v1 (ранняя дата)':>16} {'vN (поздняя дата)':>17} "
          f"{'Цена v1':>18} {'Цена vN':>18} {'Δ руб.':>18} {'Δ %':>8}")
    print("-" * 170)

    def short_ver(label):
        if not label:
            return "?"
        m = re.search(r"Версия\s*№\s*(\d+)\s*от\s*(\d{2}\.\d{2}\.\d{4})", str(label), re.I)
        return f"v{m.group(1)} {m.group(2)}" if m else str(label)[:15]

    for _, row in full.iterrows():
        sign = "↑" if row["delta"] > 0 else "↓"
        ktru_s = (str(row["ktru"])[:33] + "..") if len(str(row["ktru"])) > 35 else row["ktru"]
        print(
            f"{row['reg_number']:<28} {str(ktru_s):<35} {int(row['version_total']):>6} "
            f"{short_ver(row['version_first_label']):>16} {short_ver(row['version_last_label']):>17} "
            f"{fmt(row['price_v1']):>18} {fmt(row['price_vN']):>18} "
            f"{sign}{fmt(abs(row['delta'])):>17} {row['delta_pct']:>7.1f}%"
        )
    print("-" * 170)
    print(f"  Строк выведено: {len(full)}")

    # Сводная по законам с конверсией
    p_cnt, p_sum = build_count_sum_pivots(merged, "law", "delta")
    print_count_sum_table("Изменение цены КТРУ по законам (кол-во позиций и Σ Δ, руб.)", p_cnt, p_sum, row_label_width=20)

    return merged
def analyze_top_ktru_by_delta(merged: pd.DataFrame):
    print(f"\n{'=' * 90}")
    print("ТАБЛИЦА 7. Топ-20 КТРУ по суммарному росту цены")
    print(f"{'=' * 90}")

    grp = (merged.groupby("ktru")["delta"]
           .agg(["count", "sum", "mean"])
           .sort_values("sum", ascending=False))

    print(f"\n{'КТРУ':<50} {'Контрактов':>10} {'Σ Δ руб.':>20} {'Avg Δ руб.':>18}")
    print("-" * 100)
    for label, row in grp.head(20).iterrows():
        ktru_s = (str(label)[:48] + "..") if len(str(label)) > 50 else str(label)
        sign = "↑" if row["sum"] > 0 else "↓"
        print(f"{ktru_s:<50} {int(row['count']):>10} "
              f"{sign}{fmt(abs(row['sum'])):>19} {fmt(row['mean']):>18}")
    print("-" * 100)

    print(f"\nТоп-20 КТРУ по суммарному СНИЖЕНИЮ цены:")
    print(f"{'КТРУ':<50} {'Контрактов':>10} {'Σ Δ руб.':>20} {'Avg Δ руб.':>18}")
    print("-" * 100)
    for label, row in grp.tail(20).sort_values("sum").iterrows():
        ktru_s = (str(label)[:48] + "..") if len(str(label)) > 50 else str(label)
        print(f"{ktru_s:<50} {int(row['count']):>10} "
              f"↓{fmt(abs(row['sum'])):>19} {fmt(abs(row['mean'])):>18}")
    print("-" * 100)

    p_cnt, p_sum = build_count_sum_pivots(merged, "ktru", "delta", limit=30)
    print_count_sum_table("Топ КТРУ по Δ, с разбивкой по законам", p_cnt, p_sum, row_label_width=45)


def analyze_item_delta_distribution(merged: pd.DataFrame):
    print(f"\n{'=' * 60}")
    print("ТАБЛИЦА 8. Распределение позиций по диапазонам Δ%")
    print(f"{'=' * 60}")

    bins = [-float("inf"), -50, -20, -5, 0, 5, 20, 50, float("inf")]
    labels = ["< -50%", "-50%…-20%", "-20%…-5%", "-5%…0%",
              "0%…+5%", "+5%…+20%", "+20%…+50%", "> +50%"]
    merged = merged.copy()
    merged["bin"] = pd.cut(merged["delta_pct"], bins=bins, labels=labels)
    summary = merged.groupby("bin", observed=True)["reg_number"].count()
    total = summary.sum()

    print(f"\n{'Диапазон':<15} {'Позиций':>10} {'%':>8}")
    print("-" * 36)
    for label, cnt in summary.items():
        print(f"{label:<15} {cnt:>10} {cnt/total*100:>7.1f}%")
    print("-" * 36)
    print(f"{'Итого':<15} {total:>10}")

    p_cnt, p_sum = build_count_sum_pivots(merged, "bin", "delta", row_order=labels)
    print_count_sum_table("Диапазоны Δ% позиций по законам", p_cnt, p_sum, row_label_width=18)


def analyze_execution_stages(df: pd.DataFrame):
    print(f"\n{'=' * 100}")
    print("ТАБЛИЦА 9. Исполнение контракта: оплачено vs обязательства по этапам")
    print(f"{'=' * 100}")

    records = []
    for _, row in df.iterrows():
        for stage in extract_execution_stages(row["process_info_json"]):
            stage["reg_number"] = row["reg_number"]
            stage["law"] = row["law"]
            records.append(stage)

    if not records:
        print("Нет данных об этапах исполнения.")
        return

    s = pd.DataFrame(records)
    s["paid"] = s["paid_raw"].apply(clean_price_value)
    s["obligated"] = s["obligated_raw"].apply(clean_price_value)
    s["completed"] = s["completed"].str.strip().str.lower().isin(["да", "yes"])
    s["has_penalty"] = s["has_penalty"].str.strip().str.lower().isin(["да", "yes"])

    total_stages = len(s)
    completed = int(s["completed"].sum())
    with_penalty = int(s["has_penalty"].sum())
    total_paid = s["paid"].sum()
    total_obligated = s["obligated"].sum()

    print(f"\n  Всего этапов                 : {total_stages}")
    print(f"  Завершено (ИСПОЛНЕНИЕ = Да)  : {completed} ({completed/total_stages*100:.1f}%)")
    print(f"  С неустойкой на этапе        : {with_penalty} ({with_penalty/total_stages*100:.1f}%)")
    print(f"  Суммарно обязательств        : {fmt(total_obligated)} руб.")
    print(f"  Суммарно оплачено            : {fmt(total_paid)} руб.")
    print(f"  Разница (оплачено − обяз.)   : {fmt(total_paid - total_obligated)} руб.")

    print(f"\n{'Закон':<10} {'Этапов':>8} {'Завершено':>10} {'С пенями':>10} "
          f"{'Σ обяз., руб.':>22} {'Σ оплачено, руб.':>22}")
    print("-" * 90)
    for law, g in s.groupby("law"):
        print(
            f"{law:<10} {len(g):>8} {int(g['completed'].sum()):>10} "
            f"{int(g['has_penalty'].sum()):>10} "
            f"{fmt(g['obligated'].sum()):>22} {fmt(g['paid'].sum()):>22}"
        )
    print("-" * 90)

    s["_dummy_group"] = "Все этапы"
    p_cnt, p_sum = build_count_sum_pivots(s, "_dummy_group", "obligated")
    print_count_sum_table("Этапы исполнения: кол-во и Σ обязательств по законам", p_cnt, p_sum, row_label_width=20)

    p_cnt2, p_sum2 = build_count_sum_pivots(s, "_dummy_group", "paid")
    print_count_sum_table("Этапы исполнения: кол-во и Σ оплачено по законам", p_cnt2, p_sum2, row_label_width=20)
def analyze_penalties(df: pd.DataFrame):
    print(f"\n{'=' * 100}")
    print("ТАБЛИЦА 10. Неустойки (штрафы, пени): начислено vs оплачено")
    print(f"{'=' * 100}")

    records = []
    for _, row in df.iterrows():
        for p in extract_penalties(row["process_info_json"]):
            p["reg_number"] = row["reg_number"]
            p["law"] = row["law"]
            records.append(p)

    if not records:
        print("Нет данных о неустойках.")
        return

    p = pd.DataFrame(records)
    has_charged = p["charged"].notna().sum()
    total_charged = p["charged"].sum() if has_charged > 0 else None
    total_paid = p["paid"].sum()
    contracts_cnt = p["reg_number"].nunique()

    print(f"\n  Контрактов с неустойками       : {contracts_cnt}")
    print(f"  Всего записей неустоек         : {len(p)}")
    if has_charged > 0:
        print(f"  Суммарно начислено             : {fmt(total_charged)} руб.")
        print(f"  Суммарно оплачено              : {fmt(total_paid)} руб.")
        print(f"  Долг (начислено − оплачено)    : {fmt(total_charged - total_paid)} руб.")
    else:
        print(f"  [!] Поле НАЧИСЛЕНО содержит тексты документов, числа не найдены")
        print(f"  Суммарно оплачено пеней        : {fmt(total_paid)} руб.")

    req_grp = (
        p.groupby("requirement_text")["paid"]
        .agg(["count", "sum"])
        .sort_values("sum", ascending=False).head(10)
    )

    print(f"\n{'Причина':<85} {'Кол-во':>7} {'Σ оплачено':>18}")
    print("-" * 115)
    for label, row in req_grp.iterrows():
        short = (str(label)[:83] + "..") if len(str(label)) > 85 else str(label)
        print(f"{short:<85} {int(row['count']):>7} {fmt(row['sum']):>18}")

    pay_grp = (
        p[p["inn"].notna()]
        .groupby(["payer", "inn"])["paid"]
        .agg(["count", "sum"])
        .sort_values("sum", ascending=False).head(15)
    )

    print(f"\n{'Организация':<80} {'ИНН':>13} {'Записей':>7} {'Σ оплачено':>18}")
    print("-" * 125)
    for (payer, inn), row in pay_grp.iterrows():
        short = (str(payer)[:78] + "..") if len(str(payer)) > 80 else str(payer)
        print(f"{short:<80} {inn:>13} {int(row['count']):>7} {fmt(row['sum']):>18}")
    print("-" * 125)

    p_cnt, p_sum = build_count_sum_pivots(p, "requirement_code", "paid", limit=20)
    print_count_sum_table("Неустойки по кодам требования и законам (кол-во и Σ оплачено)", p_cnt, p_sum, row_label_width=25)

def analyze_payment_targets():
    df_raw = load_versions_payment()
    if df_raw.empty:
        return

    items_df = explode_items(df_raw)
    if items_df.empty:
        print("Нет позиций — проверьте структуру payment_targets_json")
        sample = df_raw["payment_targets_json"].dropna().iloc[0] if not df_raw.empty else {}
        if isinstance(sample, dict):
            print(f"  Ключи верхнего уровня JSON: {list(sample.keys())}")
        return

    merged = analyze_item_price_changes(items_df)
    if merged is not None and not merged.empty:
        analyze_top_ktru_by_delta(merged)
        analyze_item_delta_distribution(merged)
def months_diff_safe(start_date, end_date):
    """Разница в месяцах между двумя датами (грубо, по году и месяцу)."""
    if start_date is None or end_date is None:
        return None
    if pd.isna(start_date) or pd.isna(end_date):
        return None
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


def get_versions_for_contracts(contract_ids):
    """
    Загружает все версии контрактов и разбирает их метки
    (номер версии, дата версии) через parse_version_label.
    """
    versions = list(
        ContractVersion
        .select(
            ContractVersion.id,
            ContractVersion.contract,
            ContractVersion.version,
        )
        .where(ContractVersion.contract.in_(contract_ids))
        .dicts()
    )

    df = pd.DataFrame(versions)
    if df.empty:
        return df

    parsed = df["version"].apply(parse_version_label)
    df["version_num"] = parsed.apply(lambda x: x[0])
    df["version_date"] = parsed.apply(lambda x: x[1])
    df["is_initial_flag"] = df["version"].fillna("").str.contains(
        "Версия № 0", regex=False
    )

    return df


def compute_contract_durations(contract_ids):
    """
    Для каждого контракта определяет:
      - initial_version_date — дата "Версия № 0" (если есть), иначе самая ранняя по Id
      - latest_version_date  — дата самой последней по Id версии
      - months_diff          — разница в месяцах между ними
    """
    versions_df = get_versions_for_contracts(contract_ids)
    if versions_df.empty:
        return pd.DataFrame()

    rows = []

    for cid, group in versions_df.groupby("contract"):
        group_sorted = group.sort_values("id")

        initial_candidates = group_sorted[group_sorted["is_initial_flag"]]

        if not initial_candidates.empty:
            initial_date = initial_candidates.iloc[0]["version_date"]
        else:
            initial_date = group_sorted.iloc[0]["version_date"]

        latest_date = group_sorted.iloc[-1]["version_date"]

        rows.append({
            "contract_id": cid,
            "initial_version_date": initial_date,
            "latest_version_date": latest_date,
            "months_diff": months_diff_safe(initial_date, latest_date),
            "version_count": len(group_sorted),
        })

    return pd.DataFrame(rows)
def keep_latest_process_version(df: pd.DataFrame) -> pd.DataFrame:
    """
    Оставляет последнюю версию каждого контракта.
    Используется для process_info_json, если JSON содержит
    полный снимок текущего состояния контракта.
    """
    if df.empty:
        return df

    result = df.copy()

    parsed = result["version_label"].apply(parse_version_label)

    result["_version_num"] = parsed.apply(lambda x: x[0])
    result["_version_date"] = parsed.apply(lambda x: x[1])

    result["_version_date_sort"] = result["_version_date"].fillna(
        pd.Timestamp.min
    )

    result = result.sort_values(
        [
            "contract_id",
            "_version_num",
            "_version_date_sort",
            "version_id",
        ]
    )

    result = (
        result
        .drop_duplicates(subset=["contract_id"], keep="last")
        .drop(columns=[
            "_version_num",
            "_version_date",
            "_version_date_sort",
        ])
        .reset_index(drop=True)
    )

    return result
def load_contract_duration() -> pd.DataFrame:
    """
    Загружает контракты (по закупкам в диапазоне DATE_FROM–DATE_TO)
    и рассчитывает длительность жизни контракта в месяцах.
    """
    print("\n>>> Загрузка данных для анализа длительности контрактов...")

    pmap = _purchases_map()
    if not pmap:
        print("Нет закупок, попадающих в заданный диапазон дат.")
        return pd.DataFrame()

    eligible_registry_numbers = set(pmap.keys())

    contracts = list(
        Contract
        .select(
            Contract.Id,
            Contract.RegistryNumber,
        )
        .where(Contract.RegistryNumber.in_(eligible_registry_numbers))
        .dicts()
    )

    if not contracts:
        print("Нет контрактов по закупкам в заданном диапазоне дат.")
        return pd.DataFrame()

    contract_ids = [c["Id"] for c in contracts]
    contract_to_reg = {c["Id"]: c["RegistryNumber"] for c in contracts}

    durations_df = compute_contract_durations(contract_ids)
    if durations_df.empty:
        print("Нет версий для расчёта длительности.")
        return pd.DataFrame()

    durations_df["reg_number"] = durations_df["contract_id"].map(contract_to_reg)
    durations_df["law"] = durations_df["reg_number"].map(
        lambda r: pmap.get(r, {}).get("law", "")
    )

    print(f"✓ Рассчитана длительность для {len(durations_df)} контрактов")
    return durations_df

def analyze_contract_duration(df: pd.DataFrame):
    print(f"\n{'=' * 90}")
    print("ТАБЛИЦА 11. Длительность жизни контракта: от начальной до последней версии, мес.")
    print(f"{'=' * 90}")

    df_v = df[df["months_diff"].notna()].copy()
    if df_v.empty:
        print("Нет контрактов с рассчитанной длительностью.")
        return df_v

    print(f"\n  Всего контрактов с рассчитанной длительностью : {len(df_v)}")
    print(f"  Средняя длительность, мес.                     : {df_v['months_diff'].mean():.1f}")
    print(f"  Медианная длительность, мес.                   : {df_v['months_diff'].median():.1f}")
    print(f"  Максимальная длительность, мес.                : {int(df_v['months_diff'].max())}")

    bins = [-float("inf"), 0, 1, 3, 6, 12, 24, float("inf")]
    labels = ["0 мес.", "1 мес.", "2–3 мес.", "4–6 мес.", "7–12 мес.", "13–24 мес.", "> 24 мес."]
    df_v["bin"] = pd.cut(df_v["months_diff"], bins=bins, labels=labels)

    print(f"\n{'Диапазон':<15} {'Контрактов':>12} {'%':>8}")
    print("-" * 38)
    summary = df_v.groupby("bin", observed=True)["contract_id"].count()
    total = summary.sum()
    for label, cnt in summary.items():
        print(f"{label:<15} {cnt:>12} {cnt/total*100:>7.1f}%")
    print("-" * 38)
    print(f"{'Итого':<15} {total:>12}")

    p_cnt, p_sum = build_count_sum_pivots(df_v, "bin", "months_diff", row_order=labels)
    print_count_sum_table(
        "Длительность контрактов по законам (кол-во и Σ месяцев)",
        p_cnt, p_sum, row_label_width=18
    )

    print(f"\n{'Реестровый номер':<28} {'Закон':<8} {'Версий':>7} "
          f"{'Начальная версия':>18} {'Последняя версия':>18} {'Δ мес.':>8}")
    print("-" * 95)

    top = df_v.sort_values("months_diff", ascending=False).head(30)
    for _, row in top.iterrows():
        init_s = row["initial_version_date"].strftime("%d.%m.%Y") if pd.notna(row["initial_version_date"]) else "?"
        last_s = row["latest_version_date"].strftime("%d.%m.%Y") if pd.notna(row["latest_version_date"]) else "?"
        print(
            f"{row['reg_number']:<28} {row['law']:<8} {int(row['version_count']):>7} "
            f"{init_s:>18} {last_s:>18} {int(row['months_diff']):>8}"
        )
    print("-" * 95)

    return df_v
def analyze_process_info():
    df = load_process_info()
    if df.empty:
        return
    analyze_execution_stages(df)
    analyze_penalties(df)
if __name__ == "__main__":
    db_path = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

    db.init(db_path)
    db.connect(reuse_if_open=True)

    print("=" * 60)
    print("  АНАЛИЗ ВЕРСИЙ КОНТРАКТОВ (Peewee / SQLite) — вся БД")
    print(
        f"  Диапазон публикации закупок: "
        f"{DATE_FROM_STR} — {DATE_TO.strftime('%d.%m.%Y')}"
    )
    print("=" * 60)

    df_raw = load_versions_data()
    if not df_raw.empty:
        df = prepare_df(df_raw)
        df_v = analyze_price_vs_nmck(df)
        if df_v is not None and not df_v.empty:
            analyze_by_law(df_v)
            analyze_delta_distribution(df_v)
            analyze_by_year(df_v)
        analyze_version_counts(df)

    # analyze_payment_targets()
    # analyze_process_info()
    # df_duration = load_contract_duration()
    # if not df_duration.empty:
    #     analyze_contract_duration(df_duration)