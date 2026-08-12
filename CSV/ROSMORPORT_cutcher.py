import json
import re

from peewee import SqliteDatabase, Model, AutoField, TextField, CharField

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Contract(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")
    common_info_json = TextField(null=True, verbose_name="Общая информация")
    ContractIdentifier = CharField(null=True, max_length=255, verbose_name="Идентификатор контракта")


PATTERNS = [
    re.compile(r'договор\s+от\s+.*?№\s*([\w\-/]+)', re.IGNORECASE),
    re.compile(r'номер\s+(?:контракта|договора)\s*[:\-]?\s*"?([\w\-/]+)', re.IGNORECASE),
]


def normalize_contract_number(value):
    if value is None:
        return None
    s = str(value).replace('\xa0', ' ').strip().strip('"').strip("'")
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[;,.]+$', '', s)
    return s or None


def extract_contract_numbers(value):
    found = []

    if value is None:
        return found

    if isinstance(value, str):
        s = value.replace('\xa0', ' ')
        for pat in PATTERNS:
            found.extend(pat.findall(s))

        try:
            parsed = json.loads(value)
        except Exception:
            parsed = None

        if parsed is not None:
            found.extend(extract_contract_numbers(parsed))

    elif isinstance(value, list):
        for item in value:
            found.extend(extract_contract_numbers(item))

    elif isinstance(value, dict):
        for k, v in value.items():
            key = str(k).lower()

            if key in ("text", "value") and isinstance(v, str):
                s = v.replace('\xa0', ' ')
                for pat in PATTERNS:
                    found.extend(pat.findall(s))

            found.extend(extract_contract_numbers(v))

        if "items" in value and isinstance(value["items"], list):
            for item in value["items"]:
                if isinstance(item, dict):
                    title = str(item.get("title", "")).lower()
                    text = item.get("text")
                    if text and ("номер договора" in title or "номер контракта" in title):
                        found.append(str(text).replace('\xa0', ' '))

    cleaned = []
    seen = set()
    for x in found:
        n = normalize_contract_number(x)
        if n and n not in seen:
            cleaned.append(n)
            seen.add(n)
    return cleaned


def update_contract_identifiers():
    updated = 0
    skipped = 0
    no_match = 0

    query = (
        Contract
        .select(Contract.Id, Contract.common_info_json, Contract.ContractIdentifier)
        .where(Contract.common_info_json.is_null(False))
    )

    for c in query:
        numbers = extract_contract_numbers(c.common_info_json)
        if not numbers:
            no_match += 1
            continue

        contract_number = numbers[0]

        if c.ContractIdentifier == contract_number:
            skipped += 1
            continue

        c.ContractIdentifier = contract_number
        c.save(only=[Contract.ContractIdentifier])
        updated += 1

    print(f"updated={updated}")
    print(f"skipped={skipped}")
    print(f"no_match={no_match}")


if __name__ == "__main__":
    db.connect(reuse_if_open=True)
    try:
        update_contract_identifiers()
    finally:
        if not db.is_closed():
            db.close()