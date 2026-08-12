import csv
import sqlite3
from pathlib import Path

INPUT_CSV = "result — копия.csv"          # укажите свой файл
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

KEY_COLUMN_INDEX = 0        # 1-я колонка: RegistryNumber с "№"
OKPD2_COLUMN_INDEX = 1      # 2-я колонка: ОКПД2


def normalize_registry_number(value):
    if not value:
        return ""
    return value.replace('№', '').strip()


def detect_delimiter(file_path, encoding='windows-1251'):
    with open(file_path, 'r', encoding=encoding, newline='') as f:
        sample = f.read(2048)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=';,')
        return dialect.delimiter
    except csv.Error:
        return ';'


def find_purchase_table(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    for t in tables:
        if t.lower() == "purchase":
            return t
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    table_name = find_purchase_table(cursor)
    if table_name is None:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("Таблица purchase не найдена. Доступные таблицы:", [r[0] for r in cursor.fetchall()])
        conn.close()
        return

    cursor.execute(f'SELECT RegistryNumber FROM "{table_name}"')
    db_map = {}
    for (value,) in cursor.fetchall():
        if value:
            db_map[normalize_registry_number(value)] = value

    print(f"Загружено записей из БД: {len(db_map)}")

    updated = 0
    not_found = 0
    not_found_list = []

    delim = detect_delimiter(INPUT_CSV)

    with open(INPUT_CSV, 'r', encoding='windows-1251', newline='') as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, None)  # пропускаем заголовок

        for row in reader:
            if len(row) <= max(KEY_COLUMN_INDEX, OKPD2_COLUMN_INDEX):
                continue

            raw_key = row[KEY_COLUMN_INDEX].strip()
            okpd2_value = row[OKPD2_COLUMN_INDEX].strip()

            if not raw_key:
                continue

            norm_key = normalize_registry_number(raw_key)

            if norm_key in db_map:
                cursor.execute(
                    f'UPDATE "{table_name}" SET OKPD2Classification = ? WHERE RegistryNumber = ?',
                    (okpd2_value if okpd2_value else "Нет данных", db_map[norm_key])
                )
                updated += 1
            else:
                not_found += 1
                not_found_list.append(raw_key)

    conn.commit()
    conn.close()

    print(f"Обновлено записей: {updated}")
    print(f"Не найдено в БД: {not_found}")
    if not_found_list:
        print("Примеры ненайденных номеров:", not_found_list[:10])


if __name__ == "__main__":
    main()