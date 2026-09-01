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

# Ключевые слова для поиска (штрафы по контракту)
SEARCH_KEYWORDS = [
    "Информация о начислении неустоек (штрафов, пеней)",
]


def find_in_value(value, path=""):
    """Рекурсивный поиск ключевых слов в структуре (dict/list/str)."""
    results = []

    if isinstance(value, dict):
        for key, val in value.items():
            results.extend(
                find_in_value(
                    val,
                    f"{path}.{key}" if path else key
                )
            )
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            results.extend(
                find_in_value(
                    item,
                    f"{path}[{idx}]"
                )
            )
    elif isinstance(value, str):
        value_lower = value.lower()
        for keyword in SEARCH_KEYWORDS:
            if keyword.lower() in value_lower:
                results.append({
                    "path": path,
                    "keyword": keyword,
                    "value": (
                        value[:200] + ("..." if len(value) > 200 else "")
                    ),
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
    where_clause = " OR ".join(
        [f"{field} IS NOT NULL AND {field} != ''" for field in JSON_FIELDS]
    )

    # Запрос к contract_versions
    query_versions = f"""
        SELECT
            id,
            contract_id,
            reg_number,
            number,
            customer_name,
            object_name,
            version,
            {fields_sql}
        FROM contract_versions
        WHERE {where_clause}
    """

    cur.execute(query_versions)
    version_rows = cur.fetchall()

    print(
        f"Found {len(version_rows)} rows in contract_versions "
        f"with non-empty JSON fields\n"
    )

    # Словарь для кэширования контрактов: {contract_id: (RegistryNumber, ...)}
    contracts_cache = {}

    total_matches = 0
    field_stats = {field: 0 for field in JSON_FIELDS}

    for v_row in version_rows:
        version_id = v_row[0]
        contract_id = v_row[1]
        version_reg_number = v_row[2]
        version_number = v_row[3]
        customer_name = v_row[4]
        object_name = v_row[5]
        version_str = v_row[6]
        json_values = v_row[7:]  # 6 JSON-полей

        # Получаем RegistryNumber из контракта
        if contract_id not in contracts_cache:
            cur.execute(
                """
                SELECT RegistryNumber
                FROM contract
                WHERE id = ?
                """,
                (contract_id,)
            )
            contract_row = cur.fetchone()
            if contract_row:
                contracts_cache[contract_id] = contract_row[0]
            else:
                contracts_cache[contract_id] = None

        contract_registry_number = contracts_cache[contract_id]

        row_matches = []

        for field_idx, field_name in enumerate(JSON_FIELDS):
            json_text = json_values[field_idx]
            if not json_text:
                continue

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(
                    f"Version row {version_id}: "
                    f"Invalid JSON in {field_name}: {e}"
                )
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

            print(f"Version ID: {version_id}")
            print(f"Contract ID: {contract_id}")
            print(
                f"Contract RegistryNumber: "
                f"{contract_registry_number or 'Нет данных'}"
            )
            print(f"Version RegNumber: {version_reg_number}")
            print(f"Version Number: {version_number}")
            print(f"CustomerName: {customer_name}")
            print(f"ObjectName: {object_name}")
            print(f"Version: {version_str}")
            print(f"Matches ({len(row_matches)}):")
            for m in row_matches:
                print(
                    f"  Field: {m['field']}, "
                    f"Path: {m['path']}, "
                    f"Keyword: {m['keyword']}"
                )
                print(f"    Value: {m['value']}")
            print()

    print("=" * 60)
    print("SUMMARY:")
    print(f"Total version rows scanned: {len(version_rows)}")
    print(f"Total matches found: {total_matches}")
    print("\nMatches by field:")
    for field, count in field_stats.items():
        print(f"  {field}: {count} rows with matches")

    conn.close()


if __name__ == "__main__":
    main()