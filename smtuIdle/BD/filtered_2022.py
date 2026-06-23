import sqlite3
import os
import sys

# ─── Настройки ────────────────────────────────────────────────────────────────
SOURCE_DB = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
TARGET_DB = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\filtered_2022.db"
DATE_FROM = "2025-01-01"
# ──────────────────────────────────────────────────────────────────────────────

CHUNK = 900


def chunked_in(column: str, values: list):
    """WHERE column IN (...) с поддержкой длинных списков."""
    if not values:
        return "1=0", []
    parts, params = [], []
    for i in range(0, len(values), CHUNK):
        chunk = values[i:i + CHUNK]
        ph = ",".join("?" * len(chunk))
        parts.append(f"{column} IN ({ph})")
        params.extend(chunk)
    return "(" + " OR ".join(parts) + ")", params


def fetch(src: sqlite3.Connection, table: str, column: str, values: list):
    """Выбирает строки из таблицы по column IN values."""
    if not values:
        return []
    where, params = chunked_in(column, values)
    return src.execute(f"SELECT * FROM {table} WHERE {where}", params).fetchall()


def fetch_all(src: sqlite3.Connection, table: str):
    """Копирует таблицу целиком."""
    return src.execute(f"SELECT * FROM {table}").fetchall()


def copy_table(src: sqlite3.Connection, dst: sqlite3.Connection,
               table: str, rows: list):
    """Копирует схему и вставляет строки в целевую БД."""
    schema_row = src.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not schema_row:
        print(f"  [WARN] '{table}' не найдена в исходной БД, пропуск.")
        return
    dst.execute(schema_row[0])
    if rows:
        ph = ",".join("?" * len(rows[0]))
        dst.executemany(
            f"INSERT INTO {table} VALUES ({ph})",
            [tuple(r) for r in rows]
        )
    print(f"  {table:22s}: {len(rows):>6} строк")


def run():
    if not os.path.exists(SOURCE_DB):
        sys.exit(f"[ERR] База не найдена: {SOURCE_DB}")

    src = sqlite3.connect(SOURCE_DB)
    src.row_factory = sqlite3.Row

    # ── 1. Закупки от 2022 ──────────────────────────────────────────────────
    purchases = src.execute(
        "SELECT * FROM purchase WHERE PlacementDate >= ?", (DATE_FROM,)
    ).fetchall()
    print(f"\n[1]  purchase        (PlacementDate >= {DATE_FROM}): {len(purchases)} строк")
    if not purchases:
        src.close()
        print("Нет данных — выходим.")
        return

    purchase_ids   = [r["Id"]             for r in purchases if r["Id"]]
    reg_numbers    = list({r["RegistryNumber"] for r in purchases if r["RegistryNumber"]})
    customer_names = list({r["CustomerName"]   for r in purchases if r["CustomerName"]})

    # ── 2. Контракты — по RegistryNumber ────────────────────────────────────
    contracts = fetch(src, "contract", "RegistryNumber", reg_numbers)
    print(f"[2]  contract        (по RegistryNumber):            {len(contracts)} строк")
    contract_ids = [r["Id"] for r in contracts]

    # ── 3. FinalDetermination — по purchase_id ───────────────────────────────
    final_dets = fetch(src, "finaldetermination", "purchase_id", purchase_ids)
    print(f"[3]  finaldetermination (по purchase_id):            {len(final_dets)} строк")

    # ── 4. CurrencyRate — по purchase_id ─────────────────────────────────────
    currency_rates = fetch(src, "currencyrate", "purchase_id", purchase_ids)
    print(f"[4]  currencyrate    (по purchase_id):               {len(currency_rates)} строк")

    # ── 5. Supplier — по contract_id ─────────────────────────────────────────
    suppliers = fetch(src, "supplier", "contract_id", contract_ids)
    print(f"[5]  supplier        (по contract_id):               {len(suppliers)} строк")

    # ── 6. contract_versions — по contract_id ─────────────────────────────────
    versions = fetch(src, "contract_versions", "contract_id", contract_ids)
    print(f"[6]  contract_versions (по contract_id):              {len(versions)} строк")

    # ── 7. Vessel — по contract_id ───────────────────────────────────────────
    vessels = fetch(src, "vessel", "contract_id", contract_ids)
    print(f"[7]  vessel          (по contract_id):               {len(vessels)} строк")
    vessel_ids = [r["id"] for r in vessels]

    # ── 8. vessel_engine — по vessel_id ───────────────────────────────────────
    vessel_engines = fetch(src, "vessel_engine", "vessel_id", vessel_ids)
    print(f"[8]  vessel_engine    (по vessel_id):                 {len(vessel_engines)} строк")

    # ── 9. Customer — по CustomerName из закупок ─────────────────────────────
    customers = fetch(src, "customer", "name", customer_names)
    print(f"[9]  customer        (по CustomerName):              {len(customers)} строк")

    # ── 10. ChangedDate — по RegistryNumber ──────────────────────────────────
    changed_dates = fetch(src, "changeddate", "RegistryNumber", reg_numbers)
    print(f"[10] changeddate     (по RegistryNumber):            {len(changed_dates)} строк")

    # ── 11-14. Системные таблицы — копируем целиком ──────────────────────────
    users      = fetch_all(src, "user")
    roles      = fetch_all(src, "role")
    user_roles = fetch_all(src, "userrole")
    user_logs  = fetch_all(src, "userlog")
    print(f"[11] user:           {len(users)} строк")
    print(f"[12] role:           {len(roles)} строк")
    print(f"[13] userrole:       {len(user_roles)} строк")
    print(f"[14] userlog:        {len(user_logs)} строк")

    # ── Запись в новую БД ────────────────────────────────────────────────────
    if os.path.exists(TARGET_DB):
        os.remove(TARGET_DB)

    dst = sqlite3.connect(TARGET_DB)
    dst.execute("PRAGMA foreign_keys = OFF")

    print(f"\nЗапись в {TARGET_DB}:")
    copy_table(src, dst, "purchase",           purchases)
    copy_table(src, dst, "contract",           contracts)
    copy_table(src, dst, "finaldetermination", final_dets)
    copy_table(src, dst, "currencyrate",       currency_rates)
    copy_table(src, dst, "supplier",           suppliers)
    copy_table(src, dst, "contract_versions",   versions)
    copy_table(src, dst, "vessel",             vessels)
    copy_table(src, dst, "vessel_engine",       vessel_engines)
    copy_table(src, dst, "customer",           customers)
    copy_table(src, dst, "changeddate",        changed_dates)
    copy_table(src, dst, "user",               users)
    copy_table(src, dst, "role",               roles)
    copy_table(src, dst, "userrole",           user_roles)
    copy_table(src, dst, "userlog",            user_logs)

    dst.execute("PRAGMA foreign_keys = ON")
    dst.commit()
    dst.close()
    src.close()

    size_mb = os.path.getsize(TARGET_DB) / 1024 / 1024
    print(f"\nГотово! {TARGET_DB}  ({size_mb:.2f} МБ)")


if __name__ == "__main__":
    run()