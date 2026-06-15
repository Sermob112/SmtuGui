from smtuIdle.BD.models import Purchase, db  # Убедитесь, что импорт правильный

db_path = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

# 2. ПЕРЕИНИЦИАЛИЗИРУЕМ импортированную базу правильным путем!
db.init(db_path)

# 3. Подключаемся
db.connect(reuse_if_open=True)
# Находим все закупки, где common_info_json пустое (NULL или пустая строка)
empty_json_purchases = Purchase.select(Purchase.RegistryNumber).where(
    (Purchase.common_info_json.is_null()) |
    (Purchase.common_info_json == "") |
    (Purchase.common_info_json == "{}") |
    (Purchase.common_info_json == "[]")
)

# Выводим найденные реестровые номера
print(f"Найдено закупок с пустым common_info_json: {empty_json_purchases.count()}")

for purchase in empty_json_purchases:
    print(purchase.RegistryNumber)