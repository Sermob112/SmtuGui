from datetime import datetime
import json
from peewee import SqliteDatabase
from smtuIdle.BD.models import Purchase, Contract, Customer,Supplier
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
                reg    = raw.get("reg_number")
                number = raw.get("number")  # номер контракта для поиска дубля

                # Исправляем цену прямо здесь, поверх map_contract_record
                mapped["ContractPrice"] = parse_price(raw.get("contract_price"))

                if not reg:
                    errors.append(f"Строка {i}: нет reg_number, пропущено")
                    continue

                # Ищем связанную закупку
                purchase = Purchase.get_or_none(Purchase.RegistryNumber == reg)
                if purchase is None:
                    errors.append(f"Строка {i}: закупка {reg} не найдена в SQLite, пропущено")
                    continue

                # Ищем существующий контракт по номеру контракта
                existing = None
                if number:
                    existing = Contract.get_or_none(Contract.ContractNumber == number)
                # Запасной поиск — по purchase FK
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
                    # purchase всегда обновляем если не привязан
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