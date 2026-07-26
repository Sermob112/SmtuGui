from datetime import datetime
import json
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, Customer, Supplier, ContractVersion, SupplierContract
import re
db = SqliteDatabase('database.db')
FIELD_MAP = {
    "reg_number":            "RegistryNumber",
    "law":                   "PurchaseOrder",
    "placing_way":           "ProcurementMethod",
    "object_name":           "PurchaseName",
    "customer_name":         "CustomerName",
    "customer_url":          "notification_link",
    "initial_price_amount":  "InitialMaxContractPrice",
    "initial_price_currency": "Currency",
    "published":             "PlacementDate",
    "updated":               "UpdateDate",
    "submission_end":        "ApplicationEndDate",
    "status":                "PurchaseStatus",
    "url_common_info":       "notification_link",
    # JSON-поля — имена совпадают, маппим напрямую
    "common_info_json":      "common_info_json",
    "documents_json":        "documents_json",
    "event_log_json":        "event_log_json",
    "supplier_result_json":  "supplier_result_json",
    "lots_json":             "lots_json",
    "protocols_json":        "protocols_json",
    "contracts_info_json":   "contracts_info_json",
    "changes_json":          "changes_json",
}

# JSON-поля — сериализуем обратно в строку для TextField
JSON_FIELDS = {
    "common_info_json", "documents_json", "event_log_json",
    "supplier_result_json", "lots_json", "protocols_json",
    "contracts_info_json", "changes_json",
}

# DateField — Peewee принимает строку формата YYYY-MM-DD
DATE_FIELDS = {"PlacementDate", "UpdateDate", "ApplicationEndDate", "ApplicationStartDate", "AuctionDate"}
CONTRACT_FIELD_MAP = {
    "reg_number":               "RegistryNumber",
    "number":                   "ContractNumber",
    "contract_price":           "ContractPrice",
    "date_contract_signed":     "StartDate",
    "date_execution_due":       "EndDate",
    "customer_name":            "ContractingAuthority",
    "object_name":              "WinnerExecutor",       # ближайшее по смыслу
    "status":                   "Applicant_satatus",
    # JSON-поля — имена совпадают
    "common_info_json":         "common_info_json",
    "payment_targets_json":     "payment_targets_json",
    "process_info_json":        "process_info_json",
    "documents_json":           "documents_json",
    "journal_versions_json":    "journal_versions_json",
    "event_log_json":           "event_log_json",
}

CONTRACT_JSON_FIELDS = {
    "common_info_json", "payment_targets_json", "process_info_json",
    "documents_json", "journal_versions_json", "event_log_json",
}

CONTRACT_DATE_FIELDS = {"StartDate", "EndDate"}
CUSTOMER_FIELD_MAP = {
    "name":                  "name",
    "law":                   "law",
    "ogrn":                  "ogrn",
    "inn":                   "inn",
    "kpp":                   "kpp",
    "country":               "country",
    "region":                "region",
    "city":                  "city",
    "address_full":          "address_full",
    "organization_url":      "organization_url",
    "organization_id":       "organization_id",
    "customer_code":         "customer_code",
    "purchases_url":         "purchases_url",
    "contracts_url":         "contracts_url",
    "account_card_url":      "account_card_url",
    "additional_info_url":   "additional_info_url",
    # JSON-поля
    "documents_card_json":   "documents_card_json",
    "additional_info_json":  "additional_info_json",
    "journal_versions_json": "journal_versions_json",
}

CUSTOMER_JSON_FIELDS = {
    "documents_card_json",
    "additional_info_json",
    "journal_versions_json",
}
SUPPLIER_FIELD_MAP = {
    "organization":  "organization",
    "Country":       "country",
    "adress":        "address",       # опечатка в PG — adress
    "index_adress":  "index_address",
    "phone":         "phone",
    "mail":          "mail",
    "status":        "status",
    "inn":           "inn",
    "kpp":           "kpp",
}
JSONB_FIELDS_CV = {
    "common_info_json", "payment_targets_json", "process_info_json",
    "documents_json", "journal_versions_json", "event_log_json",
}

CV_FIELD_MAP = {
    "reg_number":               "reg_number",
    "contract_url":             "contract_url",
    "law":                      "law",
    "number":                   "number",
    "status":                   "status",
    "object_name":              "object_name",
    "customer_name":            "customer_name",
    "customer_url":             "customer_url",
    "contract_price":           "contract_price",
    "date_contract_signed":     "date_contract_signed",
    "date_execution_due":       "date_execution_due",
    "date_registered":          "date_registered",
    "date_updated_in_registry": "date_updated_in_registry",
    "version":                  "version",
    "captured_at":              "captured_at",
    "common_info_json":         "common_info_json",
    "payment_targets_json":     "payment_targets_json",
    "process_info_json":        "process_info_json",
    "documents_json":           "documents_json",
    "journal_versions_json":    "journal_versions_json",
    "event_log_json":           "event_log_json",
}

def parse_date(value: str | None) -> str | None:
    if not value:
        return None

    # Пробуем формат DD.MM.YYYY (из CSV)
    try:
        return datetime.strptime(value, '%d.%m.%Y').strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    # Запасной вариант — ISO формат YYYY-MM-DD (из парсера)
    try:
        return datetime.fromisoformat(value).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    return None



def map_record(raw: dict) -> dict:
    """Преобразует запись из JSONL в словарь полей модели Purchase."""
    mapped = {}
    for pg_field, sqlite_field in FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is None:
            continue

        # JSON-поля → сериализуем в строку
        if pg_field in JSON_FIELDS:
            mapped[sqlite_field] = (
                json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )
        # Даты → нормализуем
        elif sqlite_field in DATE_FIELDS:
            mapped[sqlite_field] = parse_date(str(val))
        else:
            mapped[sqlite_field] = val

    return mapped


# ── Основная функция загрузки ─────────────────────────────────────
def insert_in_table(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    """
    Загружает JSONL-файл в таблицу Purchase.
    Возвращает (количество вставленных, список ошибок).
    Логика:
      - Если записи нет (по RegistryNumber) — INSERT
      - Если запись есть — обновляем только пустые поля (старые данные не трогаем)
    """
    inserted = 0
    errors   = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_record(raw)

                reg = mapped.get("RegistryNumber")
                if not reg:
                    errors.append(f"Строка {i}: нет RegistryNumber, пропущено")
                    continue

                existing = Purchase.get_or_none(Purchase.RegistryNumber == reg)

                if existing is None:
                    Purchase.create(**mapped)
                    inserted += 1
                else:
                    # Обновляем только пустые / дефолтные поля
                    changed = False
                    for field, value in mapped.items():
                        current = getattr(existing, field)
                        if current in (None, "Нет данных", "[]", ""):
                            setattr(existing, field, value)
                            changed = True
                    if changed:
                        existing.save()
                        inserted += 1

            except json.JSONDecodeError as e:
                errors.append(f"Строка {i}: ошибка парсинга JSON — {e}")
            except Exception as e:
                errors.append(f"Строка {i}: {e}")

    return inserted, errors


def map_contract_record(raw: dict) -> dict:
    mapped = {}

    for pg_field, sqlite_field in CONTRACT_FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is None:
            continue

        if pg_field in CONTRACT_JSON_FIELDS:
            mapped[sqlite_field] = (
                json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )

        elif pg_field == "date_execution_due":
            start_from_range, end_from_range = parse_date_range(str(val))

            # EndDate всегда стараемся брать из конца диапазона
            if end_from_range:
                mapped["EndDate"] = end_from_range

            # Если StartDate ещё нет, можно взять начало диапазона
            if start_from_range and not mapped.get("StartDate"):
                mapped["StartDate"] = start_from_range

        elif sqlite_field in CONTRACT_DATE_FIELDS:
            mapped[sqlite_field] = parse_date(str(val))

        elif sqlite_field == "ContractPrice":
            try:
                mapped[sqlite_field] = float(str(val).replace(" ", "").replace(",", "."))
            except (ValueError, TypeError):
                mapped[sqlite_field] = None

        else:
            mapped[sqlite_field] = val

    return mapped

def parse_date_range(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None

    s = str(value).strip()

    # Нормализуем разные тире: —, –, -
    s = re.sub(r'\s*[—–-]\s*', ' - ', s)

    # Ищем все даты формата DD.MM.YYYY или YYYY-MM-DD
    dates = re.findall(r'\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2}', s)

    if len(dates) >= 2:
        start_date = parse_date(dates[0])
        end_date = parse_date(dates[1])
        return start_date, end_date

    if len(dates) == 1:
        single_date = parse_date(dates[0])
        return single_date, single_date

    return None, None
def parse_price(value) -> float | None:
    """Парсит цену вида '5 203 924 040,00 ₽' или '5203924040.00' в float."""
    if value is None:
        return None
    # Убираем всё кроме цифр, точки и запятой
    cleaned = re.sub(r'[^\d.,]', '', str(value))
    if not cleaned:
        return None
    # Если есть и запятая и точка — запятая это десятичный разделитель (европейский формат)
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None
def normalize_reg(value: str) -> str:
    if not value:
        return value
    return value.replace("№ ", "").strip()
def normalize_contract_number(raw: str | None) -> str | None:
    """
    Приводит номер контракта к единому виду — только цифры.
    '№ 1783939541915000006'  → '1783939541915000006'
    '№  17839394...'        → '17839394...'
    '3283939...'            → '3283939...'
    """
    if not raw:
        return None
    # Убираем №, знак #, пробелы, дефисы в начале
    cleaned = re.sub(r'^[№#\s\-]+', '', str(raw).strip())
    # Убираем внутренние двойные пробелы
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned if cleaned else None
def insert_contracts(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    inserted = 0
    errors = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw = json.loads(line)
                mapped = map_contract_record(raw)

                reg = normalize_reg(raw.get("reg_number"))
                number = normalize_contract_number(raw.get("number"))

                if reg:
                    mapped["RegistryNumber"] = reg
                if number:
                    mapped["ContractNumber"] = number

                mapped["ContractPrice"] = parse_price(raw.get("contract_price"))

                if not reg:
                    errors.append(f"Строка {i}: нет reg_number, пропущено")
                    continue

                purchase = (
                    Purchase.get_or_none(Purchase.RegistryNumber == reg)
                    or Purchase.get_or_none(Purchase.RegistryNumber == f"№{reg}")
                    or Purchase.get_or_none(Purchase.RegistryNumber.contains(reg))
                )

                existing = (
                    Contract.get_or_none(Contract.RegistryNumber == reg)
                    or (Contract.get_or_none(Contract.ContractNumber == number) if number else None)
                    or (Contract.get_or_none(Contract.purchase == purchase) if purchase else None)
                )

                if existing is None:
                    if purchase is None:
                        errors.append(f"Строка {i}: закупка {reg} не найдена, пропущено")
                        continue

                    mapped["purchase"] = purchase
                    Contract.create(**mapped)
                    inserted += 1
                else:
                    changed = False
                    for field, value in mapped.items():
                        if value is None:
                            continue
                        current = getattr(existing, field, None)
                        if current in (None, "", "Нет данных", "[]"):
                            setattr(existing, field, value)
                            changed = True

                    if purchase and existing.purchase_id is None:
                        existing.purchase = purchase
                        changed = True

                    if changed:
                        existing.save()
                        inserted += 1

            except json.JSONDecodeError as e:
                errors.append(f"Строка {i}: ошибка парсинга JSON — {e}")
            except Exception as e:
                errors.append(f"Строка {i}: {e}")

    return inserted, errors


def map_customer_record(raw: dict) -> dict:
    mapped = {}
    for pg_field, sqlite_field in CUSTOMER_FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is None:
            continue
        if pg_field in CUSTOMER_JSON_FIELDS:
            mapped[sqlite_field] = (
                json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )
        else:
            mapped[sqlite_field] = val
    return mapped


def insert_customers(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    """
    Загружает JSONL-файл заказчиков в таблицу Customer.
    Уникальность — по полю inn.
    """
    inserted = 0
    errors   = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_customer_record(raw)
                inn    = mapped.get("inn")

                if not mapped.get("name"):
                    errors.append(f"Строка {i}: нет name, пропущено")
                    continue

                # Ищем по ИНН, если есть — иначе по имени
                existing = None
                if inn:
                    existing = Customer.get_or_none(Customer.inn == inn)
                if existing is None:
                    existing = Customer.get_or_none(Customer.name == mapped["name"])

                if existing is None:
                    Customer.create(**mapped)
                    inserted += 1
                else:
                    changed = False
                    for field, value in mapped.items():
                        if value is None:
                            continue
                        current = getattr(existing, field)
                        if current in (None, ""):
                            setattr(existing, field, value)
                            changed = True
                    if changed:
                        existing.save()
                        inserted += 1

            except json.JSONDecodeError as e:
                errors.append(f"Строка {i}: ошибка парсинга JSON — {e}")
            except Exception as e:
                errors.append(f"Строка {i}: {e}")

    return inserted, errors

def map_supplier_record(raw: dict) -> dict:
    mapped = {}
    for pg_field, sqlite_field in SUPPLIER_FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is not None:
            mapped[sqlite_field] = val
    return mapped


def insert_suppliers(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    inserted = 0
    errors = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw = json.loads(line)
                mapped = map_supplier_record(raw)

                inn = (mapped.get("inn") or "").strip() or None
                organization = (mapped.get("organization") or "").strip() or None
                kpp = (mapped.get("kpp") or "").strip() or None

                contract = find_contract_by_reg(raw)
                if contract is None:
                    errors.append(
                        f"Строка {i}: контракт не найден по reg_number={raw.get('reg_number')!r}"
                    )
                    continue

                supplier = None

                if inn:
                    supplier = Supplier.get_or_none(Supplier.inn == inn)

                if supplier is None and organization and kpp:
                    supplier = Supplier.get_or_none(
                        (Supplier.organization == organization) &
                        (Supplier.kpp == kpp)
                    )

                if supplier is None and organization:
                    supplier = Supplier.get_or_none(Supplier.organization == organization)

                if supplier is None:
                    supplier = Supplier.create(**mapped)
                    inserted += 1
                else:
                    changed = False
                    for field, value in mapped.items():
                        if value is None:
                            continue
                        current = getattr(supplier, field, None)
                        if current in (None, "", "Нет данных", "[]"):
                            setattr(supplier, field, value)
                            changed = True
                    if changed:
                        supplier.save()

                SupplierContract.get_or_create(
                    supplier=supplier,
                    contract=contract
                )

            except json.JSONDecodeError as e:
                errors.append(f"Строка {i}: ошибка парсинга JSON — {e}")
            except Exception as e:
                errors.append(f"Строка {i}: {e}")

    return inserted, errors

def find_contract_for_supplier(raw: dict):
    contract_id = raw.get("contract_id")
    reg_raw = raw.get("reg_number")
    reg = normalize_reg(reg_raw) if reg_raw else None

    contract = None

    if contract_id:
        contract = Contract.get_or_none(Contract.id == contract_id)

    if contract is None and reg:
        contract = (
            Contract.get_or_none(Contract.RegistryNumber == reg)
            or Contract.get_or_none(Contract.RegistryNumber == f"№{reg}")
        )

    return contract
def map_cv_record(raw: dict) -> dict:
    mapped = {}
    for pg_field, sqlite_field in CV_FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is None:
            continue
        if pg_field in JSONB_FIELDS_CV:
            mapped[sqlite_field] = (
                json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )
        else:
            mapped[sqlite_field] = val
    return mapped

def normalize_reg(value: str) -> str:
    """Убирает '№', пробелы для сравнения."""
    if not value:
        return value
    return value.replace("№", "").strip()


def find_contract_by_reg(raw: dict):
    reg_raw = raw.get("reg_number")
    if not reg_raw:
        return None

    reg = normalize_reg(reg_raw)

    contract = (
        Contract.get_or_none(Contract.RegistryNumber == reg)
        or Contract.get_or_none(Contract.RegistryNumber == f"№{reg}")
        or Contract.get_or_none(Contract.RegistryNumber.contains(reg))
    )
    return contract


def find_contract_for_version(raw: dict) -> Contract | None:
    """
    Ищет контракт для версии по приоритету:
    1. ContractNumber (нормализованный)
    2. RegistryNumber (реестровый номер закупки)
    """
    # ── 1. Поиск по номеру контракта ──────────────────────────
    number_raw = raw.get("number") or raw.get("contract_number")
    number = normalize_contract_number(number_raw)

    if number:
        contract = (
            Contract.get_or_none(Contract.ContractNumber == number)
            # Иногда в БД хранится с №, ищем и такой вариант
            or Contract.get_or_none(Contract.ContractNumber == f"№ {number}")
            or Contract.get_or_none(Contract.ContractNumber == f"№{number}")
        )
        if contract:
            return contract

    # ── 2. Запасной: поиск через RegistryNumber закупки ───────
    reg = normalize_reg(raw.get("reg_number"))
    if reg:
        purchase = (
            Purchase.get_or_none(Purchase.RegistryNumber == reg)
            or Purchase.get_or_none(Purchase.RegistryNumber == f"№{reg}")
            or Purchase.get_or_none(Purchase.RegistryNumber.contains(reg))
        )
        if purchase:
            return Contract.get_or_none(Contract.purchase == purchase)

    return None
def insert_contract_versions(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    inserted = 0
    errors   = []
    # Счётчики для диагностики
    matched_by_number = 0
    matched_by_reg    = 0

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Строк для загрузки: {len(lines)}")

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_cv_record(raw)
                ver    = mapped.get("version")

                if not mapped.get("contract_url"):
                    mapped["contract_url"] = ""

                # ── captured_at: строка → datetime ────────────────────
                cap = mapped.get("captured_at")
                if cap and isinstance(cap, str):
                    try:
                        mapped["captured_at"] = datetime.fromisoformat(cap)
                    except ValueError:
                        mapped.pop("captured_at", None)

                # ── Ищем контракт: сначала по ContractNumber ──────────
                number_raw = raw.get("number") or raw.get("contract_number")
                number     = normalize_contract_number(number_raw)
                contract   = None

                if number:
                    contract = (
                        Contract.get_or_none(Contract.ContractNumber == number)
                        or Contract.get_or_none(Contract.ContractNumber == f"№ {number}")
                        or Contract.get_or_none(Contract.ContractNumber == f"№{number}")
                    )
                    if contract:
                        matched_by_number += 1

                # ── Запасной: ищем по RegistryNumber закупки ──────────
                if contract is None:
                    reg = normalize_reg(raw.get("reg_number"))
                    if reg:
                        purchase = (
                            Purchase.get_or_none(Purchase.RegistryNumber == reg)
                            or Purchase.get_or_none(Purchase.RegistryNumber == f"№{reg}")
                            or Purchase.get_or_none(Purchase.RegistryNumber.contains(reg))
                        )
                        if purchase:
                            contract = Contract.get_or_none(Contract.purchase == purchase)
                            if contract:
                                matched_by_reg += 1

                if contract is None:
                    errors.append(
                        f"Строка {i}: контракт не найден "
                        f"(number={number_raw!r}, reg={raw.get('reg_number')!r}), пропущено"
                    )
                    continue

                # ── Уникальность: contract + version ──────────────────
                existing = ContractVersion.get_or_none(
                    (ContractVersion.contract == contract) &
                    (ContractVersion.version  == ver)
                )

                if existing is None:
                    mapped["contract"] = contract
                    # Убираем поля которых нет в модели ContractVersion
                    mapped.pop("reg_number",       None)
                    mapped.pop("number",           None)
                    mapped.pop("contract_number",  None)
                    ContractVersion.create(**mapped)
                    inserted += 1
                else:
                    changed = False
                    for field, value in mapped.items():
                        if value is None:
                            continue
                        current = getattr(existing, field, None)
                        if current in (None, ""):
                            setattr(existing, field, value)
                            changed = True
                    if changed:
                        existing.save()
                        inserted += 1

            except json.JSONDecodeError as e:
                errors.append(f"Строка {i}: ошибка JSON — {e}")
            except Exception as e:
                errors.append(f"Строка {i}: {e}")

            if i % 500 == 0:
                print(f"  Обработано: {i}/{len(lines)}", end="\r")

    print(f"\nЗагружено версий : {inserted}")
    print(f"Найдено по ContractNumber : {matched_by_number}")
    print(f"Найдено по RegistryNumber : {matched_by_reg}")
    print(f"Ошибок              : {len(errors)}")
    return inserted, errors