import csv
from peewee import SqliteDatabase, Model, AutoField, CharField

DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
OUTPUT_FILE = "registry_numbers_44fz.csv"
PURCHASE_ORDER_FILTER = "44-ФЗ"

db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Purchase(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")
    PurchaseOrder = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Закон")
    RegistryNumber = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Реестровый номер")


def export_registry_numbers(output_file=OUTPUT_FILE, purchase_order=PURCHASE_ORDER_FILTER):
    db.connect()
    try:
        query = Purchase.select(Purchase.RegistryNumber).where(Purchase.PurchaseOrder == purchase_order)

        with open(output_file, 'w', encoding='windows-1251', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["RegistryNumber"])

            exported_count = 0
            for record in query:
                writer.writerow([record.RegistryNumber])
                exported_count += 1

        print(f"Экспортировано записей: {exported_count}")
        print(f"Файл сохранён: {output_file}")

    except Exception as e:
        print("Ошибка при выгрузке данных:", e)

    finally:
        db.close()


if __name__ == "__main__":
    export_registry_numbers()