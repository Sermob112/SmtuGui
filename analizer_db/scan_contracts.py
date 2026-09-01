import sqlite3
import json

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

# Поля для сканирования
JSON_FIELDS = [
    "common_info_json",
    "payment_targets_json",
    "process_info_json",
    "documents_json",
    "journal_versions_json",
    "event_log_json",
]

# Ключевые слова для поиска
# SEARCH_KEYWORDS = [
#     "лимит",
#     "финансирование",
#     "финансирования",
#     "finance",
#     "limit",
#     "funding",
#     "лимит финансирования",
#     "finance limit",
#     "funding limit",
# ]
SEARCH_KEYWORDS = [
    "аванс",
    "авансирование",

]

def find_in_value(value, path=""):
    """Рекурсивный поиск ключевых слов в структуре (dict/list/str)."""
    results = []

    if isinstance(value, dict):
        for key, val in value.items():
            results.extend(find_in_value(val, f"{path}.{key}" if path else key))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            results.extend(find_in_value(item, f"{path}[{idx}]"))
    elif isinstance(value, str):
        value_lower = value.lower()
        for keyword in SEARCH_KEYWORDS:
            if keyword.lower() in value_lower:
                results.append({
                    "path": path,
                    "keyword": keyword,
                    "value": value[:200] + ("..." if len(value) > 200 else ""),
                })
                break  # Одно совпадение на строку достаточно
    return results


def main():
    print(f"DB_PATH: {DB_PATH}")
    print(f"Scanning fields: {JSON_FIELDS}\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Построим SELECT для JSON-полей
    fields_sql = ", ".join(JSON_FIELDS)
    where_clause = " OR ".join([f"{field} IS NOT NULL AND {field} != ''" for field in JSON_FIELDS])

    query = f"""
        SELECT Id, ContractNumber, RegistryNumber, ContractingAuthority, WinnerExecutor, {fields_sql}
        FROM contract
        WHERE {where_clause}
    """

    cur.execute(query)
    rows = cur.fetchall()

    print(f"Found {len(rows)} rows with non-empty JSON fields\n")

    total_matches = 0
    field_stats = {field: 0 for field in JSON_FIELDS}

    for row in rows:
        row_id = row[0]
        contract_number = row[1]
        registry_number = row[2]
        contracting_authority = row[3]
        winner_executor = row[4]
        json_values = row[5:]  # 6 JSON-полей

        row_matches = []

        for field_idx, field_name in enumerate(JSON_FIELDS):
            json_text = json_values[field_idx]
            if not json_text:
                continue

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"Row {row_id}: Invalid JSON in {field_name}: {e}")
                continue

            matches = find_in_value(data)
            if matches:
                field_stats[field_name] += 1
                for match in matches:
                    row_matches.append({
                        "field": field_name,
                        **match,
                    })

        if row_matches:
            total_matches += len(row_matches)
            print(f"Row ID: {row_id}")
            print(f"ContractNumber: {contract_number}")
            print(f"RegistryNumber: {registry_number}")
            print(f"ContractingAuthority: {contracting_authority}")
            print(f"WinnerExecutor: {winner_executor}")
            print(f"Matches ({len(row_matches)}):")
            for m in row_matches:
                print(f"  Field: {m['field']}, Path: {m['path']}, Keyword: {m['keyword']}")
                print(f"    Value: {m['value']}")
            print()

    print("=" * 60)
    print("SUMMARY:")
    print(f"Total rows scanned: {len(rows)}")
    print(f"Total matches found: {total_matches}")
    print("\nMatches by field:")
    for field, count in field_stats.items():
        print(f"  {field}: {count} rows with matches")

    conn.close()


if __name__ == "__main__":
    main()