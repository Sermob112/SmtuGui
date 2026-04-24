"""
Скрипт для заполнения тестовых данных в поля QueryCount и ResponseCount
таблицы purchase (модель Purchase, Peewee ORM, SQLite)
"""

import random
import sys
import os
from peewee import SqliteDatabase, Model, IntegerField, AutoField

# ──────────────────────────────────────────────
# Конфигурация — поменяй путь к БД если нужно
# ──────────────────────────────────────────────
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

# Диапазоны тестовых данных
QUERY_COUNT_RANGE  = (1, 3)   # QueryCount:  от 1 до 50
RESPONSE_COUNT_MAX_RATIO = 0.9  # ResponseCount <= QueryCount * 0.9 (ответов всегда меньше запросов)

# Режим: "all" — все записи, "null_only" — только где поля пустые, "range" — диапазон id
MODE = "all"   # << меняй здесь: "all" | "null_only" | "range"
ID_FROM = 1          # Только для MODE="range"
ID_TO   = 100        # Только для MODE="range"
# ──────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    print(f"[ОШИБКА] Файл базы данных не найден: {DB_PATH}")
    sys.exit(1)

db = SqliteDatabase(DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class Purchase(BaseModel):
    Id            = AutoField(primary_key=True)
    QueryCount    = IntegerField(null=True)
    ResponseCount = IntegerField(null=True)

    class Meta:
        table_name = "purchase"

db.connect(reuse_if_open=True)

# Выборка записей в зависимости от режима
if MODE == "all":
    records = Purchase.select()
    desc = "все записи"
elif MODE == "null_only":
    records = Purchase.select().where(
        (Purchase.QueryCount.is_null()) | (Purchase.ResponseCount.is_null())
    )
    desc = "записи с пустыми QueryCount / ResponseCount"
elif MODE == "range":
    records = Purchase.select().where(
        Purchase.Id.between(ID_FROM, ID_TO)
    )
    desc = f"записи с Id от {ID_FROM} до {ID_TO}"
else:
    print(f"[ОШИБКА] Неизвестный MODE: {MODE}")
    sys.exit(1)

total = records.count()
print(f"Режим: {MODE} | Найдено записей: {total} ({desc})")

if total == 0:
    print("Нечего обновлять. Скрипт завершён.")
    db.close()
    sys.exit(0)

updated = 0
for purchase in records:
    qc = random.randint(*QUERY_COUNT_RANGE)
    rc = random.randint(0, max(0, int(qc * RESPONSE_COUNT_MAX_RATIO)))

    purchase.QueryCount    = qc
    purchase.ResponseCount = rc
    purchase.save()
    updated += 1

    if updated % 100 == 0 or updated == total:
        print(f"  Обновлено: {updated}/{total} записей...")

db.close()
print(f"\n✅ Готово! Обновлено {updated} записей.")
print(f"   QueryCount  : случайные значения {QUERY_COUNT_RANGE[0]}–{QUERY_COUNT_RANGE[1]}")
print(f"   ResponseCount: случайные значения 0 – QueryCount×{RESPONSE_COUNT_MAX_RATIO}")
def clear_test_data(mode="all", id_from=1, id_to=100):
    """
    Сбрасывает тестовые данные в полях QueryCount и ResponseCount таблицы purchase.
    Устанавливает NULL во все затронутые записи.

    Параметры:
      mode    — "all" / "range"
      id_from — нижняя граница Id при mode="range"
      id_to   — верхняя граница Id при mode="range"
    """
    if not os.path.exists(DB_PATH):
        print(f"[ОШИБКА] Файл БД не найден: {DB_PATH}")
        return

    db.connect(reuse_if_open=True)

    if mode == "all":
        records = Purchase.select()
        desc = "все записи"
    elif mode == "range":
        records = Purchase.select().where(Purchase.Id.between(id_from, id_to))
        desc = f"записи Id {id_from}–{id_to}"
    else:
        print(f"[ОШИБКА] Неподдерживаемый режим: '{mode}'. Используйте 'all' или 'range'.")
        db.close()
        return

    total   = records.count()
    cleared = 0

    print(f"Очистка: {mode} | Найдено: {total} ({desc})")

    if total == 0:
        print("Нечего очищать.")
        db.close()
        return

    for purchase in records:
        purchase.QueryCount    = None
        purchase.ResponseCount = None
        purchase.save()
        cleared += 1

        if cleared % 100 == 0 or cleared == total:
            print(f"  Очищено: {cleared}/{total}...")

    db.close()
    print(f"\n✅ Готово! Очищено {cleared} записей.")
    print("   QueryCount    → NULL")
    print("   ResponseCount → NULL")


# ── Вызов ──────────────────────────────────────
if __name__ == "__main__":
    # Раскомментируйте нужный вариант и запустите скрипт:

    clear_test_data(mode="all")                          # Очистить все записи
    # clear_test_data(mode="range", id_from=1, id_to=50) # Только Id 1–50