from datetime import datetime
import json
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, Customer,Supplier,ContractVersion
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
    """Преобразует запись из JSONL в словарь полей модели Contract."""
    mapped = {}
    for pg_field, sqlite_field in CONTRACT_FIELD_MAP.items():
        val = raw.get(pg_field)
        if val is None:
            continue

        if pg_field in CONTRACT_JSON_FIELDS:
            mapped[sqlite_field] = (
                json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )
        elif sqlite_field in CONTRACT_DATE_FIELDS:
            mapped[sqlite_field] = parse_date(str(val))
        elif sqlite_field == "ContractPrice":
            # contract_price в PG хранится как Text — конвертируем в float
            try:
                mapped[sqlite_field] = float(str(val).replace(" ", "").replace(",", "."))
            except (ValueError, TypeError):
                mapped[sqlite_field] = None
        else:
            mapped[sqlite_field] = val

    return mapped


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
    return value.replace("№", "").strip()

def insert_contracts(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    inserted = 0
    errors   = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_contract_record(raw)
                reg    = normalize_reg(raw.get("reg_number"))   # ← нормализуем
                number = raw.get("number")

                mapped["ContractPrice"] = parse_price(raw.get("contract_price"))

                if not reg:
                    errors.append(f"Строка {i}: нет reg_number, пропущено")
                    continue

                # Ищем закупку перебирая форматы
                purchase = (
                    Purchase.get_or_none(Purchase.RegistryNumber == reg)
                    or Purchase.get_or_none(Purchase.RegistryNumber == f"№{reg}")
                    or Purchase.get_or_none(Purchase.RegistryNumber.contains(reg))
                )

                if purchase is None:
                    errors.append(f"Строка {i}: закупка {reg} не найдена в SQLite, пропущено")
                    continue

                # Ищем существующий контракт
                existing = None
                if number:
                    existing = Contract.get_or_none(Contract.ContractNumber == number)
                if existing is None:
                    existing = Contract.get_or_none(Contract.purchase == purchase)

                if existing is None:
                    mapped["purchase"] = purchase
                    Contract.create(**mapped)
                    inserted += 1
                else:
                    changed = False
                    for field, value in mapped.items():
                        if value is None:
                            continue
                        current = getattr(existing, field)
                        if current in (None, "Нет данных", "[]", ""):
                            setattr(existing, field, value)
                            changed = True
                    if existing.purchase_id is None:
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
    """
    Загружает JSONL-файл поставщиков в таблицу Supplier.
    Связь с Contract ищется по reg_number → Contract.RegistryNumber.
    Уникальность: один поставщик на контракт по ИНН.
    """
    inserted = 0
    errors   = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_supplier_record(raw)
                reg    = raw.get("reg_number")
                inn    = mapped.get("inn")

                if not reg:
                    errors.append(f"Строка {i}: нет reg_number, пропущено")
                    continue

                # Ищем контракт по reg_number
                contract = Contract.get_or_none(Contract.RegistryNumber == reg)
                if contract is None:
                    errors.append(f"Строка {i}: контракт {reg} не найден в SQLite, пропущено")
                    continue

                # Уникальность: ищем по контракту + ИНН
                existing = None
                if inn:
                    existing = Supplier.get_or_none(
                        (Supplier.contract == contract) & (Supplier.inn == inn)
                    )
                # Если ИНН нет — ищем просто по контракту
                if existing is None and not inn:
                    existing = Supplier.get_or_none(Supplier.contract == contract)

                if existing is None:
                    mapped["contract"] = contract
                    Supplier.create(**mapped)
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


def find_contract_by_reg(reg: str):
    """Ищет контракт перебирая возможные форматы."""
    reg_clean = normalize_reg(reg)

    # Вариант 1: точное совпадение
    c = Contract.get_or_none(Contract.RegistryNumber == reg_clean)
    if c:
        return c

    # Вариант 2: с префиксом №
    c = Contract.get_or_none(Contract.RegistryNumber == f"№{reg_clean}")
    if c:
        return c

    # Вариант 3: LIKE (на случай пробелов)
    c = Contract.get_or_none(Contract.RegistryNumber.contains(reg_clean))
    return c
def insert_contract_versions(filepath: str, user: str, role: str) -> tuple[int, list[str]]:
    inserted = 0
    errors   = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Строк для загрузки: {len(lines)}")

    with db.atomic():
        for i, line in enumerate(lines, start=1):
            try:
                raw    = json.loads(line)
                mapped = map_cv_record(raw)
                reg    = mapped.get("reg_number")
                ver    = mapped.get("version")

                if not reg:
                    errors.append(f"Строка {i}: нет reg_number, пропущено")
                    continue

                # ── contract_url: если пустой — ставим заглушку ───────
                if not mapped.get("contract_url"):
                    mapped["contract_url"] = ""

                # ── captured_at: строка → datetime ────────────────────
                cap = mapped.get("captured_at")
                if cap and isinstance(cap, str):
                    try:
                        mapped["captured_at"] = datetime.fromisoformat(cap)
                    except ValueError:
                        mapped.pop("captured_at", None)  # удаляем, модель подставит default

                # ── Ищем контракт по RegistryNumber ───────────────────
                contract = find_contract_by_reg(reg)
                if contract is None:
                    errors.append(f"Строка {i}: контракт {reg} не найден, пропущено")
                    continue

                # ── Уникальность: contract + version ──────────────────
                existing = ContractVersion.get_or_none(
                    (ContractVersion.contract == contract) &
                    (ContractVersion.version  == ver)
                )

                if existing is None:
                    mapped["contract"] = contract
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

    print(f"\nЗагружено версий: {inserted}")
    return inserted, errors