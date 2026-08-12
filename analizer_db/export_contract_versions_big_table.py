"""
Выгрузка большой таблицы по закупкам/контрактам/версиям в XLSX.

Что делает:
- соединяет Purchase -> Contract по RegistryNumber
- подтягивает исполнителей через SupplierContract -> Supplier
- считает число версий контракта
- определяет первую и последнюю версию по полю version
- извлекает КТРУ из payment_targets_json
- строит итоговую таблицу формата "контракт × КТРУ"
- сравнивает цену первой и последней версии контракта
- сохраняет в XLSX
"""

import json
import re
import sqlite3
from collections import defaultdict

import pandas as pd

from smtuIdle.BD.initialize_db import db
from smtuIdle.BD.models import Purchase, Contract, ContractVersion, SupplierContract, Supplier

OUTPUT_XLSX = "contract_versions_big_table.xlsx"
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"


def bind_models():
    for model in (Purchase, Contract, ContractVersion, SupplierContract, Supplier):
        model._meta.database = db

def extract_classification_from_version(version_row, purchase_row):
    code = None
    name = None

    items = extract_contract_items_new((version_row or {}).get("payment_targets_json"))
    for item in items:
        raw = item.get("ktru")
        if raw:
            c, n = parse_ktru_parts(raw)
            if c or n:
                code, name = c, n
                break

    if not code and not name and purchase_row:
        c, n = parse_okpd_parts(purchase_row.get("OKPD2Classification"))
        code, name = c, n

    return code, name
def _parse_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return None
    return None
def parse_okpd_parts(value):
    if value is None:
        return None, None

    s = re.sub(r"\s+", " ", str(value)).strip()
    if not s or s.lower() == "нет данных":
        return None, None

    m1 = re.match(r"^\s*([\d\.]{5,})\s*[:\-]\s*(.+?)\s*$", s)
    if m1:
        return m1.group(1).strip(), shorten_ktru(m1.group(2).strip())

    m2 = re.match(r"^\s*(.+?)\s*\(([\d\.]{5,})\)\s*$", s)
    if m2:
        return m2.group(2).strip(), shorten_ktru(m2.group(1).strip())

    m3 = re.search(r"([\d\.]{5,})", s)
    if m3:
        code = m3.group(1).strip()
        name = re.sub(r"\(?\b" + re.escape(code) + r"\b\)?", "", s).strip(" :-–—,;()")
        return code, shorten_ktru(name) if name else None

    return None, shorten_ktru(s)
def parse_ktru_parts(value):
    if value is None:
        return None, None

    s = re.sub(r"\s+", " ", str(value)).strip()
    if not s or s.lower() == "нет данных":
        return None, None

    m1 = re.match(r"^\s*([\d\.]{5,})\s*[:\-]\s*(.+?)\s*$", s)
    if m1:
        return m1.group(1).strip(), shorten_ktru(m1.group(2).strip())

    m2 = re.match(r"^\s*(.+?)\s*\(([\d\.]{5,})\)\s*$", s)
    if m2:
        return m2.group(2).strip(), shorten_ktru(m2.group(1).strip())

    return None, shorten_ktru(s)
def collect_ktru_values(purchase_row=None, version_row=None):
    result = []
    seen = set()

    def add(raw_val):
        if not raw_val:
            return
        code, name = parse_ktru_parts(raw_val)
        key = ((code or "").lower(), (name or "").lower())
        if key in seen:
            return
        seen.add(key)
        result.append({
            "ktru_code": code,
            "ktru_name": name,
        })

    if version_row:
        for item in extract_contract_items_new(version_row.get("payment_targets_json")):
            add(item.get("ktru"))

    if purchase_row:
        for val in split_ktru_sources(purchase_row.get("OKPD2Classification")):
            add(val)

    return result
def clean_price_value(value):
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        s = (
            str(value)
            .replace("\xa0", "")
            .replace("\u202f", "")
            .replace(" ", "")
            .replace(",", ".")
            .replace("₽", "")
            .strip()
        )
        return float(s) if s else None
    except Exception:
        return None


def normalize_law(law):
    s = str(law or "").strip()
    if "44" in s:
        return "44-ФЗ"
    if "223" in s:
        return "223-ФЗ"
    return s or None


def parse_version_label(label):
    if not label or not isinstance(label, str):
        return 999, None
    num_match = re.search(r"Версия\s*№\s*(\d+)", label, re.IGNORECASE)
    version_num = int(num_match.group(1)) if num_match else 999
    date_match = re.search(r"от\s+(\d{2}\.\d{2}\.\d{4})", label)
    version_date = None
    if date_match:
        try:
            version_date = pd.to_datetime(date_match.group(1), format="%d.%m.%Y")
        except Exception:
            pass
    return version_num, version_date


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


def shorten_ktru(text, max_len=160):
    if not text:
        return None
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def dt_to_str(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, str):
        s = v.strip()
        return s or None
    try:
        return pd.to_datetime(v).strftime("%d.%m.%Y")
    except Exception:
        return str(v)


def pick_first_nonempty(*vals):
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str):
            if v.strip():
                return v.strip()
        else:
            try:
                if pd.notna(v):
                    return v
            except Exception:
                return v
    return None


def load_purchase_map():
    bucket = defaultdict(list)
    query = (
        Purchase
        .select(
            Purchase.Id,
            Purchase.RegistryNumber,
            Purchase.PurchaseName,
            Purchase.CustomerName,
            Purchase.PurchaseOrder,
            Purchase.ProcurementOrganization,
            Purchase.PlacementDate,
            Purchase.OKPD2Classification,
        )
        .dicts()
    )
    for p in query:
        reg = normalize_reg_number(p.get("RegistryNumber"))
        if reg:
            bucket[reg].append(p)

    result = {}
    for reg, items in bucket.items():
        items.sort(key=lambda x: (
            parse_any_date(x.get("PlacementDate")) or pd.Timestamp.min,
            x.get("Id") or 0
        ))
        result[reg] = items[-1]
    return result


def load_contracts():
    return list(
        Contract
        .select(
            Contract.Id,
            Contract.RegistryNumber,
            Contract.ContractIdentifier,
            Contract.StartDate,
            Contract.EndDate,
            Contract.ContractPrice,
        )
        .dicts()
    )

def split_ktru_sources(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_parts = []
        for x in value:
            raw_parts.extend(split_ktru_sources(x))
        return raw_parts

    text = str(value).strip()
    if not text or text.lower() == "нет данных":
        return []

    parts = re.split(r"[;\n\r|]+", text)
    out = []
    for part in parts:
        s = re.sub(r"\s+", " ", str(part)).strip(" -–—,;")
        if s and s.lower() != "нет данных":
            out.append(s)
    return out

def parse_any_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, pd.Timestamp):
        return value

    s = str(value).strip()
    if not s:
        return None

    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return pd.to_datetime(s, format=fmt, errors="raise")
        except Exception:
            pass

    try:
        return pd.to_datetime(s, errors="coerce", dayfirst=True)
    except Exception:
        return None

def months_delta(date_from, date_to):
    d1 = parse_any_date(date_from)
    d2 = parse_any_date(date_to)
    if pd.isna(d1) or pd.isna(d2) or d1 is None or d2 is None:
        return None
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)
def load_supplier_map(contract_ids):
    supplier_names = defaultdict(list)
    query = (
        SupplierContract
        .select(SupplierContract.contract, Supplier.organization)
        .join(Supplier, on=(SupplierContract.supplier == Supplier.id))
        .where(SupplierContract.contract.in_(contract_ids))
        .dicts()
    )
    for row in query:
        name = row.get("organization")
        cid = row.get("contract")
        if name and cid is not None:
            supplier_names[cid].append(str(name).strip())

    out = {}
    for cid, names in supplier_names.items():
        uniq = []
        seen = set()
        for n in names:
            if n not in seen:
                uniq.append(n)
                seen.add(n)
        out[cid] = "; ".join(uniq)
    return out


def build_versions_map(contract_ids):
    versions = list(
        ContractVersion
        .select(
            ContractVersion.id,
            ContractVersion.contract,
            ContractVersion.version,
            ContractVersion.object_name,
            ContractVersion.customer_name,
            ContractVersion.law,
            ContractVersion.contract_price,
            ContractVersion.date_contract_signed,
            ContractVersion.date_execution_due,
            ContractVersion.payment_targets_json,
        )
        .where(ContractVersion.contract.in_(contract_ids))
        .dicts()
    )

    grouped = defaultdict(list)
    for v in versions:
        num, d = parse_version_label(v.get("version"))
        v["_version_num"] = num
        v["_version_date"] = d
        v["_price_num"] = clean_price_value(v.get("contract_price"))
        grouped[v.get("contract")].append(v)

    result = {}
    for cid, items in grouped.items():
        items_sorted = sorted(
            items,
            key=lambda x: (
                x["_version_num"] if x["_version_num"] is not None else 999999,
                x["_version_date"] if x["_version_date"] is not None else pd.Timestamp.max,
            )
        )
        result[cid] = {
            "count": len(items_sorted),
            "first_version": items_sorted[0] if items_sorted else None,
            "last_version": items_sorted[-1] if items_sorted else None,
            "all": items_sorted,
        }
    return result
def normalize_reg_number(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    return re.sub(r"\s+", "", s)

def extract_first_ktru_from_version(version_row):
    if not version_row:
        return None
    items = extract_contract_items_new(version_row.get("payment_targets_json"))
    for item in items:
        val = item.get("ktru")
        if val and str(val).strip():
            return str(val).strip()
    return None
def make_rows():
    purchase_map = load_purchase_map()
    contracts = load_contracts()
    if not contracts:
        return pd.DataFrame()
    print("contracts:", len(contracts))
    print("unique purchase numbers:", len(purchase_map))
    contract_ids = [c["Id"] for c in contracts]
    supplier_map = load_supplier_map(contract_ids)
    versions_map = build_versions_map(contract_ids)

    rows = []
    for c in contracts:
        cid = c.get("Id")
        reg_contract = normalize_reg_number(c.get("RegistryNumber"))
        contract_identifier = pick_first_nonempty(
            c.get("ContractIdentifier"),
            c.get("RegistryNumber"),
        )
        p = purchase_map.get(reg_contract, {})
        vmeta = versions_map.get(cid, {})

        first_version = vmeta.get("first_version")
        last_version = vmeta.get("last_version")
        version_count = vmeta.get("count", 0)
        add_agreements = max(version_count - 1, 0)

        start_v1 = parse_any_date((first_version or {}).get("date_contract_signed"))
        end_v1 = parse_any_date((first_version or {}).get("date_execution_due"))

        start_current = parse_any_date(
            pick_first_nonempty(
                c.get("StartDate"),
                (last_version or {}).get("date_contract_signed"),
            )
        )
        end_current = parse_any_date(
            pick_first_nonempty(
                c.get("EndDate"),
                (last_version or {}).get("date_execution_due"),
            )
        )

        delta_term_months = months_delta(end_v1, end_current)

        name = pick_first_nonempty(
            p.get("PurchaseName"),
            (last_version or {}).get("object_name"),
            (first_version or {}).get("object_name"),
        )
        customer = pick_first_nonempty(
            p.get("CustomerName"),
            p.get("ProcurementOrganization"),
            (last_version or {}).get("customer_name"),
            (first_version or {}).get("customer_name"),
        )
        law = normalize_law(
            pick_first_nonempty(
                p.get("PurchaseOrder"),
                (last_version or {}).get("law"),
                (first_version or {}).get("law"),
            )
        )

        contract_price = clean_price_value(c.get("ContractPrice"))
        price_v1 = (first_version or {}).get("_price_num")
        price_vN = contract_price

        delta = None
        delta_pct = None
        if price_v1 is not None and price_vN is not None:
            delta = price_vN - price_v1
            if price_v1 != 0:
                delta_pct = delta / price_v1
        classification_code, classification_name = extract_classification_from_version(
            last_version or first_version,
            p,
        )
        base = {
            "Реестровый № закупки": reg_contract,
            "Наименование закупки": name,
            "Дата размещения закупки": to_excel_date(p.get("PlacementDate")),
            "ФЗ": law,
            "Заказчик закупки": customer,

            "Код КТРУ/ОКПД2": classification_code,
            "Наименование КТРУ/ОКПД2": classification_name,

            "Реестровый № контракта": contract_identifier,
            "Дата заключения v1": to_excel_date(start_v1),
            "Дата заключения контракта": to_excel_date(start_current),
            "Дата окончания v1": to_excel_date(end_v1),
            "Дата окончания контракта": to_excel_date(end_current),
            "Δ срока, мес.": delta_term_months,
            "Версий контракта": version_count,
            "Доп.соглашений": add_agreements,
            "Исполнитель контракта": supplier_map.get(cid),
            "Цена v1": price_v1,
            "Цена vN": price_vN,
            "Цена контракта": contract_price,
            "Δ руб.": delta,
            "Δ %": delta_pct,
        }
        rows.append(base)


    df = pd.DataFrame(rows)
    if df.empty:
        return df

    cols = [
        "Реестровый № закупки",
        "Наименование закупки",
        "Дата размещения закупки",
        "ФЗ",
        "Заказчик закупки",
        "Код КТРУ/ОКПД2",
        "Наименование КТРУ/ОКПД2",
        "Реестровый № контракта",
        "Дата заключения v1",
        "Дата заключения контракта",
        "Дата окончания v1",
        "Дата окончания контракта",
        "Δ срока, мес.",
        "Версий контракта",
        "Доп.соглашений",
        "Исполнитель контракта",
        "Цена v1",
        "Цена vN",
        "Цена контракта",
        "Δ руб.",
        "Δ %",
    ]
    df = df[cols]
    df["_dedup_key"] = df["Реестровый № контракта"].fillna(df["Реестровый № закупки"])
    df = df.drop_duplicates(subset=["Реестровый № закупки", "Исполнитель контракта", "Код КТРУ/ОКПД2", "Наименование КТРУ/ОКПД2"])
    df = df.sort_values([
        "Дата размещения закупки",
        "Реестровый № закупки",
        "Реестровый № контракта",
        "Код КТРУ/ОКПД2",
        "Наименование КТРУ/ОКПД2",
    ], na_position="last")
    return df
def to_excel_date(value):
    dt = parse_any_date(value)
    if dt is None or pd.isna(dt):
        return None
    return dt.to_pydatetime()

def save_xlsx(df, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.worksheet.table import Table, TableStyleInfo
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Данные"
    col_index = {name: i + 1 for i, name in enumerate(df.columns)}
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    base_font = Font(name="Calibri", size=11, color="000000")
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right = Alignment(horizontal="right", vertical="center")
    numeric_cols = [
        "Версий контракта",
        "Доп.соглашений",
        "Δ срока, мес.",
        "Цена v1",
        "Цена vN",
        "Цена контракта",
        "Δ руб.",
        "Δ %",
    ]

    date_cols = [
        "Дата размещения закупки",
        "Дата заключения v1",
        "Дата заключения контракта",
        "Дата окончания v1",
        "Дата окончания контракта",
    ]

    center_cols = ["ФЗ"] + date_cols
    right_cols = numeric_cols
    data = [list(df.columns)] + df.where(pd.notna(df), None).values.tolist()
    for r_idx, row in enumerate(data, start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = base_font
            cell.border = border
            if r_idx == 1:
                cell.font = hdr_font
                cell.fill = hdr_fill
                cell.alignment = center
            else:
                col_name = df.columns[c_idx - 1]
                if col_name in right_cols:
                    cell.alignment = right
                elif col_name in center_cols:
                    cell.alignment = center
                else:
                    cell.alignment = left

    last_row = ws.max_row
    last_col = ws.max_column
    ref = f"A1:{get_column_letter(last_col)}{last_row}"
    tab = Table(displayName="ContractsBigTable", ref=ref)
    tab.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tab)

    widths = {
        1: 22, 2: 42, 3: 16, 4: 12, 5: 28,
        6: 18, 7: 42, 8: 24, 9: 16, 10: 16,
        11: 16, 12: 16, 13: 14, 14: 14, 15: 16,
        16: 30, 17: 16, 18: 16, 19: 16, 20: 16,
        21: 12,
    }
    for col_idx, width in widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    for row in range(2, last_row + 1):
        for name in ("Дата размещения закупки", "Дата заключения v1", "Дата заключения контракта",
                     "Дата окончания v1", "Дата окончания контракта"):
            ws.cell(row=row, column=col_index[name]).number_format = 'DD.MM.YYYY'

        for name in ("Цена v1", "Цена vN", "Цена контракта", "Δ руб."):
            ws.cell(row=row, column=col_index[name]).number_format = '#,##0.00'

        ws.cell(row=row, column=col_index["Δ %"]).number_format = '0.0%'
        ws.cell(row=row, column=col_index["Δ срока, мес."]).number_format = '0'

    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 24
    wb.save(path)


if __name__ == "__main__":
    db.init(DB_PATH)
    bind_models()
    db.connect(reuse_if_open=True)
    try:
        df = make_rows()
        if df.empty:
            raise SystemExit("Нет данных для выгрузки")
        save_xlsx(df, OUTPUT_XLSX)
        print(f"OK: {OUTPUT_XLSX} | rows={len(df)}")
    finally:
        if not db.is_closed():
            db.close()