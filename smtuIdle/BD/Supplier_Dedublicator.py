import sys
sys.path.insert(0, r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle")

from smtuIdle.BD.models import db, Supplier, Contract
from peewee import fn, ForeignKeyField
import re

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
db.init(DB_PATH)
db.connect(reuse_if_open=True)

EMPTY_VALUES = (None, "Нет данных", "[]", "")



from peewee import Model
def normalize_inn(value: str) -> str:
    if not value:
        return value
    return re.sub(r"\D", "", value.strip())


def normalize_all_inn():
    updated = 0
    for s in Supplier.select():
        normalized = normalize_inn(s.inn)
        if normalized != s.inn:
            s.inn = normalized
            s.save()
            updated += 1
    print(f"Нормализовано ИНН: {updated}")


def check_inn_uniqueness():
    """Считает, сколько РАЗНЫХ строк Supplier существует на каждый ИНН.
       Это и есть 'дубли поставщика', возникшие из-за опечаток в названии."""
    rows = (Supplier
            .select(Supplier.inn, fn.COUNT(Supplier.id).alias('cnt'))
            .where(Supplier.inn.is_null(False), Supplier.inn != "")
            .group_by(Supplier.inn)
            .having(fn.COUNT(Supplier.id) > 1)
            .order_by(fn.COUNT(Supplier.id).desc())
            .tuples())

    rows = list(rows)
    total_extra_rows = sum(cnt - 1 for _, cnt in rows)

    print(f"{'ИНН':<20}{'строк Supplier'}")
    print("-" * 40)
    for inn, cnt in rows:
        print(f"{inn:<20}{cnt}")
    print("-" * 40)
    print(f"Уникальных ИНН с повторами: {len(rows)}")
    print(f"'Лишних' строк (будет удалено после объединения): {total_extra_rows}")
    return rows



def count_filled(s: Supplier) -> int:
    return sum(1 for v in s.__data__.values() if v not in EMPTY_VALUES)


def merge_by_inn():
    db.create_tables([SupplierContract])

    groups = {}
    for s in Supplier.select():
        if s.inn in EMPTY_VALUES:
            continue
        groups.setdefault(s.inn, []).append(s)
    groups = {inn: lst for inn, lst in groups.items() if len(lst) > 1}

    removed = 0
    with db.atomic():
        for inn, dupes in groups.items():
            dupes.sort(key=count_filled, reverse=True)
            main = dupes[0]

            # переносим ВСЕ контракты дублей на главную запись через связку
            for s in dupes:
                SupplierContract.get_or_create(supplier=main, contract=s.contract_id)

            # дозаполняем пустые поля главной записи данными из дублей
            for dupe in dupes[1:]:
                changed = False
                for field, value in dupe.__data__.items():
                    if field in ("id", "contract", "contract_id"):
                        continue
                    if getattr(main, field) in EMPTY_VALUES and value not in EMPTY_VALUES:
                        setattr(main, field, value)
                        changed = True
                if changed:
                    main.save()

                Supplier.delete().where(Supplier.id == dupe.id).execute()
                removed += 1

    print(f"Объединено ИНН: {len(groups)}")
    print(f"Удалено дублирующихся строк Supplier: {removed}")
    print("Все контракты сохранены в таблице supplier_contract")


if __name__ == "__main__":
    print("БД:", db.database)
    normalize_all_inn()
    print("\n=== Проверка уникальности ИНН ===")
    check_inn_uniqueness()

    answer = input("\nОбъединить дубли по ИНН? (да/нет): ").strip().lower()
    if answer == "да":
        merge_by_inn()
        print("\n=== Повторная проверка ===")
        check_inn_uniqueness()