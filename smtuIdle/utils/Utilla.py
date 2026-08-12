import sqlite3

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row  # даёт доступ по именам колонок
cursor = conn.cursor()

cursor.execute("SELECT * FROM contract LIMIT 1")
row = cursor.fetchone()

if row:
    print(f"{'Поле':<40} {'Значение'}")
    print("-" * 80)
    for key in row.keys():
        print(f"{key:<40} {row[key]}")
else:
    print("Таблица contract пуста.")

conn.close()