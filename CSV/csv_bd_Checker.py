import csv
import sqlite3
from pathlib import Path

SOURCES_DIR = "sources"
OUTPUT_CSV = "result.csv"
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

KEY_COLUMN_NAME = "Реестровый номер закупки"
KEY_COLUMN_INDEX = 1  # второй столбец (индексация с 0)

skipped_files = []
processed_files = []
seen_keys = set()
header_written = None
rows_to_write = []


def normalize_registry_number(value):
    """Убирает символ '№' и лишние пробелы для корректного сравнения с БД."""
    if not value:
        return ""
    return value.replace('№', '').strip()


def detect_delimiter(file_path, encoding='windows-1251'):
    """Автоматически определяет разделитель файла (';' или ',')."""
    with open(file_path, 'r', encoding=encoding, newline='') as f:
        sample = f.read(2048)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=';,')
        return dialect.delimiter
    except csv.Error:
        return ';'


def load_registry_numbers_from_db(db_path):
    """Читает все значения RegistryNumber из таблицы purchase."""
    registry_numbers = set()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        table_name = None
        for t in tables:
            if t.lower() == "purchase":
                table_name = t
                break

        if table_name is None:
            print(f"Таблица purchase не найдена. Доступные таблицы: {tables}")
            return registry_numbers

        cursor.execute(f'SELECT RegistryNumber FROM "{table_name}"')
        for (value,) in cursor.fetchall():
            if value:
                registry_numbers.add(normalize_registry_number(value))
    finally:
        conn.close()
    return registry_numbers


source_path = Path(SOURCES_DIR)
csv_files = sorted(source_path.glob("*.csv"))

print(f"Найдено файлов: {len(csv_files)}")

for file_path in csv_files:
    try:
        delim = detect_delimiter(file_path)
        with open(file_path, 'r', encoding='windows-1251', newline='') as f:
            reader = csv.reader(f, delimiter=delim)
            try:
                header = next(reader)
            except StopIteration:
                skipped_files.append((file_path.name, "пустой файл"))
                continue

            if len(header) <= KEY_COLUMN_INDEX:
                skipped_files.append((file_path.name, "нет второго столбца"))
                continue

            if header[KEY_COLUMN_INDEX].strip() != KEY_COLUMN_NAME:
                skipped_files.append(
                    (file_path.name, f"неверное имя столбца: '{header[KEY_COLUMN_INDEX]}'")
                )
                continue

            if header_written is None:
                header_written = header

            if len(header) != len(header_written):
                skipped_files.append((file_path.name, "иное количество столбцов"))
                continue

            file_row_count = 0
            for row in reader:
                if len(row) <= KEY_COLUMN_INDEX:
                    continue

                key = row[KEY_COLUMN_INDEX].strip()
                if not key or key in seen_keys:
                    continue

                seen_keys.add(key)
                rows_to_write.append(row)
                file_row_count += 1

            processed_files.append((file_path.name, file_row_count))

    except UnicodeDecodeError:
        skipped_files.append((file_path.name, "ошибка декодирования windows-1251"))
    except Exception as e:
        skipped_files.append((file_path.name, f"ошибка: {e}"))

db_registry_numbers = load_registry_numbers_from_db(DB_PATH)
print(f"Загружено записей из БД: {len(db_registry_numbers)}")

rows_in_db = [
    row for row in rows_to_write
    if normalize_registry_number(row[KEY_COLUMN_INDEX]) in db_registry_numbers
]

with open(OUTPUT_CSV, 'w', encoding='windows-1251', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    if header_written:
        writer.writerow(header_written)
    writer.writerows(rows_in_db)

print(f"\nОбработано файлов: {len(processed_files)}")
print(f"Пропущено файлов: {len(skipped_files)}")
print(f"Уникальных записей всего: {len(rows_to_write)}")
print(f"Найдено в базе данных (сохранено в результат): {len(rows_in_db)}")

if skipped_files:
    print("\nПропущенные файлы и причины:")
    for name, reason in skipped_files:
        print(f"  {name}: {reason}")