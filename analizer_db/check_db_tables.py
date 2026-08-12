import sqlite3

DB_PATH = r"C:\\Users\\Sergey\\Desktop\\Work\\SmtuGui\\smtuIdle\\database.db"

print(f"DB_PATH: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA database_list;")
    print("\nPRAGMA database_list:")
    for row in cur.fetchall():
        print(row)

    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY type, name;")
    rows = cur.fetchall()
    print("\nobjects:")
    for row in rows:
        print(row)

    print(f"\nTOTAL OBJECTS: {len(rows)}")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)='purchase';")
    print("\nHas table 'purchase':", cur.fetchone())

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name) LIKE '%purch%';")
    print("\nTables похожие на purchase:")
    for row in cur.fetchall():
        print(row)

    conn.close()
except Exception as e:
    print("ERROR:", type(e).__name__, e)
