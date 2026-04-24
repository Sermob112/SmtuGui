"""
Скрипт для заполнения тестовых данных в поля:
  - OKPD2Classification  (коды ОКПД2 группы 30.1 — Корабли, суда и лодки)
  - QueryCount           (случайные значения 1–5)
  - ResponseCount        (случайные значения 1–5, <= QueryCount)
в уже существующие записи таблицы purchase (Peewee ORM, SQLite)
"""

import random
import sys
import os
from peewee import SqliteDatabase, Model, IntegerField, AutoField, CharField

# ──────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"   # << путь к файлу БД

# Режим обновления:
#   "null_only" — только записи, где все три поля пустые (NULL / "Нет данных")
#   "all"       — все записи в таблице
#   "range"     — только записи с Id от ID_FROM до ID_TO
# MODE    = "all"
# ID_FROM = 1
# ID_TO   = 100
# # ──────────────────────────────────────────────
#
# # Полный список терминальных кодов ОКПД2 группы 30.1
# # Источник: ОК 034-2014 (КПЕС 2008), подкласс 30.1 «Корабли, суда и лодки»
# OKPD2_CODES = [
#     # 30.11.1 — Корабли военные
#     ("30.11.10.000", "Корабли военные"),
#
#     # 30.11.2 — Суда для перевозки людей и грузов
#     ("30.11.21.111", "Суда круизные морские"),
#     ("30.11.21.112", "Суда экскурсионные морские"),
#     ("30.11.21.113", "Суда для обслуживания регулярных пассажирских линий морские"),
#     ("30.11.21.114", "Паромы пассажирские морские"),
#     ("30.11.21.119", "Суда морские пассажирские прочие"),
#     ("30.11.21.120", "Суда речные пассажирские"),
#     ("30.11.21.130", "Суда пассажирские смешанного плавания «река-море»"),
#     ("30.11.22.111", "Танкеры морские для перевозки нефти и нефтепродуктов"),
#     ("30.11.22.112", "Суда морские для перевозки химических продуктов"),
#     ("30.11.22.113", "Суда морские для перевозки сжиженных газов (газовозы)"),
#     ("30.11.22.119", "Суда морские для перевозки прочих жидких грузов"),
#     ("30.11.22.120", "Суда наливные речные"),
#     ("30.11.22.130", "Суда наливные смешанного плавания «река-море»"),
#     ("30.11.23.110", "Суда рефрижераторные морские"),
#     ("30.11.23.120", "Суда рефрижераторные речные"),
#     ("30.11.23.130", "Суда рефрижераторные смешанного плавания «река-море»"),
#     ("30.11.24.111", "Суда сухогрузные морские общего назначения"),
#     ("30.11.24.112", "Суда контейнерные морские"),
#     ("30.11.24.113", "Суда трейлерные морские"),
#     ("30.11.24.114", "Суда для перевозки навалочных грузов морские"),
#     ("30.11.24.115", "Суда грузопассажирские морские"),
#     ("30.11.24.116", "Суда морские грузовые комбинированные"),
#     ("30.11.24.117", "Лесовозы морские"),
#     ("30.11.24.118", "Паромы морские самоходные железнодорожные, автомобильно-транспортные"),
#     ("30.11.24.119", "Суда сухогрузные морские прочие"),
#     ("30.11.24.121", "Суда сухогрузные речные самоходные"),
#     ("30.11.24.122", "Суда сухогрузные речные несамоходные"),
#     ("30.11.24.130", "Суда сухогрузные смешанного плавания «река-море»"),
#
#     # 30.11.3 — Суда рыболовные и специального назначения
#     ("30.11.31.111", "Траулеры"),
#     ("30.11.31.112", "Дрифтеры"),
#     ("30.11.31.113", "Сейнеры"),
#     ("30.11.31.114", "Ярусники"),
#     ("30.11.31.115", "Суда китобойные"),
#     ("30.11.31.116", "Суда зверобойные"),
#     ("30.11.31.119", "Суда рыболовные прочие"),
#     ("30.11.31.120", "Суда-рыбозаводы"),
#     ("30.11.32.111", "Буксиры морские"),
#     ("30.11.32.112", "Буксиры рейдовые"),
#     ("30.11.32.113", "Буксиры портовые"),
#     ("30.11.32.114", "Буксиры морские спасательные"),
#     ("30.11.32.115", "Суда-толкачи морские"),
#     ("30.11.32.121", "Буксиры речные"),
#     ("30.11.32.122", "Суда-толкачи речные, озёрные"),
#     ("30.11.32.130", "Катера судовые буксирные"),
#     ("30.11.33.110", "Земснаряды"),
#     ("30.11.33.120", "Маяки плавучие"),
#     ("30.11.33.130", "Суда пожарные"),
#     ("30.11.33.140", "Краны плавучие"),
#     ("30.11.33.190", "Суда прочие"),
#
#     # 30.11.4 — Платформы плавучие
#     ("30.11.40.000", "Платформы плавучие или погружные и инфраструктура"),
#
#     # 30.11.5 — Конструкции плавучие прочие
#     ("30.11.50.110", "Плоты"),
#     ("30.11.50.121", "Понтоны речные"),
#     ("30.11.50.129", "Понтоны прочие"),
#     ("30.11.50.130", "Кессоны"),
#     ("30.11.50.140", "Дебаркадеры"),
#     ("30.11.50.150", "Буи и бакены"),
#     ("30.11.50.160", "Платформы и конструкции морские плавучие для запуска ракет"),
#     ("30.11.50.170", "Причалы плавучие"),
#     ("30.11.50.190", "Конструкции плавучие прочие"),
#
#     # 30.11.9 — Услуги по переоборудованию и восстановлению
#     ("30.11.91.000", "Услуги по переоборудованию и восстановлению судов, платформ и конструкций"),
#     ("30.11.92.000", "Услуги по оснащению судов, плавучих платформ и конструкций"),
#
#     # 30.12 — Суда прогулочные и спортивные
#     ("30.12.11.110", "Суда парусные прогулочные со вспомогательным двигателем или без него"),
#     ("30.12.11.120", "Суда парусные спортивные со вспомогательным двигателем или без него"),
#     ("30.12.12.110", "Суда надувные прогулочные"),
#     ("30.12.12.120", "Суда надувные спортивные"),
#     ("30.12.19.110", "Суда прогулочные прочие"),
#     ("30.12.19.120", "Суда спортивные прочие"),
#     ("30.12.19.130", "Лодки гребные"),
#     ("30.12.19.140", "Шлюпки"),
#     ("30.12.19.150", "Каноэ"),
# ]
#
# # Форматирование записи: "КОД Наименование"
# OKPD2_VALUES = [f"{code} {name}" for code, name in OKPD2_CODES]
#
# # ──────────────────────────────────────────────
#
if not os.path.exists(DB_PATH):
    print(f"[ОШИБКА] Файл БД не найден: {DB_PATH}")
    sys.exit(1)

db = SqliteDatabase(DB_PATH)
#
class BaseModel(Model):
    class Meta:
        database = db

class Purchase(BaseModel):
    Id                 = AutoField(primary_key=True)
    OKPD2Classification = CharField(null=True, max_length=512)
    QueryCount         = IntegerField(null=True)
    ResponseCount      = IntegerField(null=True)

    class Meta:
        table_name = "purchase"
#
# db.connect(reuse_if_open=True)
#
# DEFAULT_OKPD2 = "Нет данных"
#
# if MODE == "all":
#     records = Purchase.select()
#     desc = "все записи"
# elif MODE == "null_only":
#     records = Purchase.select().where(
#         (Purchase.OKPD2Classification.is_null()) |
#         (Purchase.OKPD2Classification == DEFAULT_OKPD2) |
#         (Purchase.QueryCount.is_null()) |
#         (Purchase.ResponseCount.is_null())
#     )
#     desc = "записи с незаполненными полями"
# elif MODE == "range":
#     records = Purchase.select().where(Purchase.Id.between(ID_FROM, ID_TO))
#     desc = f"записи Id {ID_FROM}–{ID_TO}"
# else:
#     print(f"[ОШИБКА] Неизвестный MODE: {MODE}")
#     sys.exit(1)
#
# total = records.count()
# print(f"Режим: {MODE} | Найдено: {total} ({desc})")
#
# if total == 0:
#     print("Нечего обновлять. Завершено.")
#     db.close()
#     sys.exit(0)
#
# updated = 0
# for purchase in records:
#     code_str = random.choice(OKPD2_VALUES)
#     qc = random.randint(1, 5)
#     rc = random.randint(1, qc)   # ответов не больше, чем запросов
#
#     purchase.OKPD2Classification = code_str
#     purchase.QueryCount          = qc
#     purchase.ResponseCount       = rc
#     purchase.save()
#     updated += 1
#
#     if updated % 100 == 0 or updated == total:
#         print(f"  Обновлено: {updated}/{total}...")
#
# db.close()
# print(f"\n✅ Готово! Обновлено {updated} записей.")
# print(f"   OKPD2Classification : случайный код из {len(OKPD2_VALUES)} вариантов группы 30.1")
# print(f"   QueryCount          : 1–5")
# print(f"   ResponseCount       : 1–QueryCount")
#
class Contract(BaseModel):
    Id                   = AutoField(primary_key=True)
    TotalApplications    = CharField(null=True)
    AdmittedApplications = CharField(null=True)
    RejectedApplications = CharField(null=True)

    class Meta:
        table_name = "contract"

db.connect(reuse_if_open=True)
#
# if MODE == "all":
#     records = Contract.select()
#     desc = "все записи"
# elif MODE == "null_only":
#     records = Contract.select().where(
#         Contract.TotalApplications.is_null() |
#         Contract.AdmittedApplications.is_null() |
#         Contract.RejectedApplications.is_null()
#     )
#     desc = "записи с незаполненными полями"
# elif MODE == "range":
#     records = Contract.select().where(Contract.Id.between(ID_FROM, ID_TO))
#     desc = f"записи Id {ID_FROM}–{ID_TO}"
# else:
#     print(f"[ОШИБКА] Неизвестный MODE: {MODE}")
#     sys.exit(1)
#
# total = records.count()
# print(f"Режим: {MODE} | Найдено: {total} ({desc})")
#
# if total == 0:
#     print("Нечего обновлять. Завершено.")
#     db.close()
#     sys.exit(0)
#
# updated = 0
# for contract in records:
#     total_apps    = random.randint(1, 5)
#     admitted      = random.randint(0, total_apps)
#     rejected      = total_apps - admitted
#
#     contract.TotalApplications    = str(total_apps)
#     contract.AdmittedApplications = str(admitted)
#     contract.RejectedApplications = str(rejected)
#     contract.save()
#     updated += 1
#
#     if updated % 100 == 0 or updated == total:
#         print(f"  Обновлено: {updated}/{total}...")
#
# db.close()
#
#
# print(f"\n✅ Готово! Обновлено {updated} записей.")
# print("   TotalApplications    : 1–5")
# print("   AdmittedApplications : 0–TotalApplications")
# print("   RejectedApplications : TotalApplications − AdmittedApplications")


def clear_test_data(mode="all", id_from=1, id_to=100):
    """
    Сбрасывает тестовые данные, добавленные скриптом заполнения:
      Purchase : OKPD2Classification → None, QueryCount → None, ResponseCount → None
      Contract : TotalApplications → None, AdmittedApplications → None, RejectedApplications → None

    Параметры:
      mode    — "all" / "null_only" / "range"  (аналогично основному скрипту)
      id_from — нижняя граница Id при mode="range"
      id_to   — верхняя граница Id при mode="range"
    """
    if not os.path.exists(DB_PATH):
        print(f"[ОШИБКА] Файл БД не найден: {DB_PATH}")
        return

    db.connect(reuse_if_open=True)

    # ── Таблица purchase ──────────────────────────────────────────
    if mode == "all":
        purchase_query = Purchase.select()
    elif mode == "range":
        purchase_query = Purchase.select().where(Purchase.Id.between(id_from, id_to))
    else:
        print(f"[ПРЕДУПРЕЖДЕНИЕ] Для очистки режим 'null_only' не имеет смысла, используйте 'all' или 'range'.")
        db.close()
        return

    p_total   = purchase_query.count()
    p_updated = 0
    for purchase in purchase_query:
        purchase.OKPD2Classification = None
        purchase.QueryCount          = None
        purchase.ResponseCount       = None
        purchase.save()
        p_updated += 1
        if p_updated % 100 == 0 or p_updated == p_total:
            print(f"  [purchase] Очищено: {p_updated}/{p_total}...")

    print(f"\n✅ purchase: очищено {p_updated} записей.")

    # ── Таблица contract ──────────────────────────────────────────
    if mode == "all":
        contract_query = Contract.select()
    elif mode == "range":
        contract_query = Contract.select().where(Contract.Id.between(id_from, id_to))

    c_total   = contract_query.count()
    c_updated = 0
    for contract in contract_query:
        contract.TotalApplications    = None
        contract.AdmittedApplications = None
        contract.RejectedApplications = None
        contract.save()
        c_updated += 1
        if c_updated % 100 == 0 or c_updated == c_total:
            print(f"  [contract] Очищено: {c_updated}/{c_total}...")

    print(f"✅ contract: очищено {c_updated} записей.")
    db.close()

if __name__ == "__main__":
    # Раскомментируйте нужный вариант:

    clear_test_data(mode="all")               # Очистить все записи
    # clear_test_data(mode="range", id_from=1, id_to=50)  # Только Id 1–50