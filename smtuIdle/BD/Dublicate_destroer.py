import os
import sys
import re
sys.path.insert(0, r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle")

from smtuIdle.BD.models import db, Purchase, Contract, FinalDetermination, CurrencyRate
from peewee import fn

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
db.init(DB_PATH)
db.connect(reuse_if_open=True)


def normalize_reg(value: str) -> str:
    """Убирает '№', пробелы и приводит к нижнему регистру."""
    if not value:
        return value
    return value.replace("№", "").strip()


def restore_reg(value: str) -> str:
    """Добавляет '№' обратно если его нет."""
    if not value:
        return value
    value = value.strip()
    if not value.startswith("№"):
        return f"№{value}"
    return value


# ── Шаг 1: нормализуем все RegistryNumber в БД ────────────────────
def normalize_all_reg_numbers():
    """Убирает '№' у всех записей для корректного поиска дублей."""
    updated = 0
    for p in Purchase.select():
        normalized = normalize_reg(p.RegistryNumber)
        if normalized != p.RegistryNumber:
            p.RegistryNumber = normalized
            p.save()
            updated += 1
    print(f"Нормализовано записей: {updated}")


# ── Шаг 2: восстанавливаем '№' у всех записей ────────────────────
def restore_all_reg_numbers():
    """Добавляет '№' обратно всем записям."""
    updated = 0
    for p in Purchase.select():
        restored = restore_reg(p.RegistryNumber)
        if restored != p.RegistryNumber:
            p.RegistryNumber = restored
            p.save()
            updated += 1
    print(f"Восстановлено записей: {updated}")


# ── Шаг 3: дедупликация ───────────────────────────────────────────
def preview_duplicates():
    duplicate_regs = (Purchase
                      .select(Purchase.RegistryNumber, fn.COUNT(Purchase.Id).alias('cnt'))
                      .group_by(Purchase.RegistryNumber)
                      .having(fn.COUNT(Purchase.Id) > 1)
                      .tuples())

    print(f"{'RegistryNumber':<50} {'Кол-во дублей'}")
    print("-" * 65)
    total = 0
    for reg, cnt in duplicate_regs:
        print(f"{str(reg):<50} {cnt}")
        total += cnt - 1
    print("-" * 65)
    print(f"Итого будет удалено записей: {total}")


def merge_duplicate_purchases():
    duplicates_removed = 0
    errors = []

    duplicate_regs = (Purchase
                      .select(Purchase.RegistryNumber)
                      .group_by(Purchase.RegistryNumber)
                      .having(fn.COUNT(Purchase.Id) > 1)
                      .tuples())

    reg_numbers = [row[0] for row in duplicate_regs]
    print(f"Найдено дублирующихся реестровых номеров: {len(reg_numbers)}")

    with db.atomic():
        for reg in reg_numbers:
            try:
                dupes = list(Purchase.select().where(Purchase.RegistryNumber == reg))
                if len(dupes) < 2:
                    continue

                def count_filled(p):
                    return sum(
                        1 for v in p.__data__.values()
                        if v is not None and v not in ("Нет данных", "[]", "")
                    )

                dupes.sort(key=count_filled, reverse=True)
                main      = dupes[0]
                to_delete = dupes[1:]

                for dupe in to_delete:
                    # Сначала сливаем поля закупки
                    changed = False
                    for field, value in dupe.__data__.items():
                        if field == "Id":
                            continue
                        current = getattr(main, field)
                        if current in (None, "Нет данных", "[]", "") and \
                                value not in (None, "Нет данных", "[]", ""):
                            setattr(main, field, value)
                            changed = True
                    if changed:
                        main.save()

                    # Сливаем контракты (с учётом unique constraint)
                    merge_contracts(main, dupe)

                    # Переносим остальные FK (у них нет unique constraint)
                    CurrencyRate.update(purchase=main).where(CurrencyRate.purchase == dupe).execute()
                    FinalDetermination.update(purchase=main).where(FinalDetermination.purchase == dupe).execute()

                    # Теперь безопасно удаляем дубль
                    # delete_instance внутри тоже чистит контракты — но мы уже перенесли/слили их выше
                    Purchase.delete().where(Purchase.Id == dupe.Id).execute()
                    duplicates_removed += 1

            except Exception as e:
                errors.append(f"RegistryNumber={reg}: {e}")

    print(f"Удалено дублей: {duplicates_removed}")
    if errors:
        for err in errors:
            print(f"  {err}")

    return duplicates_removed, errors

def merge_contracts(main_purchase: Purchase, dupe_purchase: Purchase):
    """Переносит данные контракта дубля в контракт главной записи."""
    main_contract = Contract.get_or_none(Contract.purchase == main_purchase)
    dupe_contract = Contract.get_or_none(Contract.purchase == dupe_purchase)

    if dupe_contract is None:
        return  # у дубля нет контракта — ничего делать не надо

    if main_contract is None:
        # У главной нет контракта — просто переносим
        dupe_contract.purchase = main_purchase
        dupe_contract.save()
        return

    # У обоих есть контракты — сливаем данные дубля в главный
    changed = False
    for field, value in dupe_contract.__data__.items():
        if field in ("Id", "purchase_id"):
            continue
        current = getattr(main_contract, field)
        if current in (None, "Нет данных", "[]", "") and \
           value not in (None, "Нет данных", "[]", ""):
            setattr(main_contract, field, value)
            changed = True
    if changed:
        main_contract.save()

    # Переносим FinalDetermination и CurrencyRate с дубля-контракта
    # (они висят на purchase, не на contract — уже обработано выше)

    # Удаляем контракт дубля
    dupe_contract.delete_instance()

# ── Точка входа ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("БД:", db.database)

    print("\n=== Шаг 1: Нормализация RegistryNumber ===")
    normalize_all_reg_numbers()

    print("\n=== Шаг 2: Предварительный просмотр дублей ===")
    preview_duplicates()

    answer = input("\nПродолжить объединение? (да/нет): ").strip().lower()
    if answer == "да":
        merge_duplicate_purchases()

        print("\n=== Шаг 3: Восстановление '№' ===")
        restore_all_reg_numbers()
    else:
        print("\nОтмена. Восстанавливаем '№'...")
        restore_all_reg_numbers()
