import os

import pandas as pd
import json
from datetime import datetime
from peewee import SqliteDatabase, DoesNotExist

from smtuIdle.BD.models import Vessel, Purchase, db

# Подключаем вашу базу данных

# (Здесь должны быть определения ваших классов Purchase и Vessel)
# class Purchase(BaseModel): ...
# class Vessel(BaseModel): ...

def parse_date(date_val):
    """
    Функция для приведения разных форматов дат из Excel к объекту datetime.date.
    Понимает форматы 'YYYY-MM-DD' и 'DD.MM.YYYY'.
    """
    if pd.isna(date_val):
        return None

    # Приводим к строке и отсекаем возможное время, если оно прилипло (например, '2024-05-15 00:00:00')
    date_str = str(date_val).strip().split(' ')[0]

    # Пытаемся распарсить формат ГГГГ-ММ-ДД
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    # Пытаемся распарсить формат ДД.ММ.ГГГГ
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        print(f"Не удалось распознать формат даты: {date_val}")
        return None


def update_database_from_excel(file_path):
    """
    Чтение xlsx и обновление БД.
    """
    print(f"Чтение файла {file_path}...")
    # Читаем Excel, считая, что заголовки на первой строке
    df = pd.read_excel(file_path, dtype={'Реестровый Номер': str})

    # Оборачиваем в транзакцию для значительного ускорения работы (sqlite будет записывать пачкой)
    with db.atomic():
        updated_purchases = 0
        updated_vessels = 0

        for index, row in df.iterrows():
            # Получаем реестровый номер, который является нашим ключом
            registry_number = str(row.get('Реестровый Номер', '')).strip()
            if registry_number.endswith('.0'):
                registry_number = registry_number[:-2]
            # Если номера нет или он 'nan' (пустая ячейка), пропускаем строку
            if not registry_number or registry_number.lower() == 'nan':
                continue

            # 1. Собираем массив JSON для TKPData (Предложение 1 - 8)
            tkp_list = []
            for i in range(1, 9):
                col_name = f'Предложение {i}'
                # Проверяем, есть ли колонка в Excel и не пустая ли ячейка
                if col_name in row and pd.notna(row[col_name]):
                    # Приводим к float или int (в зависимости от данных), если это число
                    tkp_list.append(row[col_name])

            # Превращаем список в JSON строку
            tkp_json = json.dumps(tkp_list, ensure_ascii=False)

            # 2. Обновление модели Purchase
            try:
                # Пытаемся найти закупку по реестровому номеру
                purchase = Purchase.get(Purchase.RegistryNumber == registry_number)

                # Обновляем поля, если они есть в таблице и не пустые (pd.notna проверяет на NaN)
                if pd.notna(row.get('Закон')):
                    purchase.PurchaseOrder = str(row['Закон'])

                if pd.notna(row.get('Метод Закупки')):
                    purchase.ProcurementMethod = str(row['Метод Закупки'])

                if pd.notna(row.get('Название Закупки')):
                    purchase.PurchaseName = str(row['Название Закупки'])

                if pd.notna(row.get('Тема Аукциона')):
                    purchase.AuctionSubject = str(row['Тема Аукциона'])

                if pd.notna(row.get('Идентификационный Код Закупки')):
                    purchase.PurchaseIdentificationCode = str(row['Идентификационный Код Закупки'])

                if pd.notna(row.get('Номер Лота')):
                    purchase.LotNumber = int(row['Номер Лота'])

                # Название Лота берем из "Название Лота" ИЛИ "проект судна", согласно вашей логике
                # Если в документе есть оба, "проект судна" перезапишет, так как мы берем его.
                if pd.notna(row.get('Название Лота')):
                    purchase.LotName = str(row['Название Лота'])
                if pd.notna(row.get('проект судна')):
                    purchase.LotName = str(row['проект судна'])

                if pd.notna(row.get('Начальная Максимальная Цена Контракта')):
                    purchase.InitialMaxContractPrice = float(row['Начальная Максимальная Цена Контракта'])

                if pd.notna(row.get('Количество судов')):
                    purchase.quantity_units = safe_int(row['Количество судов'])

                if pd.notna(row.get('Количество запросов')):
                    purchase.QueryCount = safe_int(row['Количество запросов'])

                if pd.notna(row.get('Количество ответов')):
                    purchase.ResponseCount = safe_int(row['Количество ответов'])

                # Обновляем ТКП и дату НМЦК
                purchase.TKPData = tkp_json
                purchase.PlacementDate = parse_date(row.get('дата определения НМЦК'))

                # Сохраняем изменения
                purchase.save()
                updated_purchases += 1

            except DoesNotExist:
                print(f"ВНИМАНИЕ: Закупка с реестровым номером {registry_number} не найдена в базе.")
                continue

            # 3. Обновление модели Vessel
            # В модели Vessel есть поле registry_number. Обновляем все суда с таким номером.
            ship_project_value = None
            if pd.notna(row.get('проект судна')):
                ship_project_value = str(row['проект судна'])

            # get_or_create ищет судно по реестровому номеру.
            # Если не находит - создает новое, заполняя поля из defaults.
            # Метод возвращает сам объект (vessel) и флаг (created = True/False)
            vessel, created = Vessel.get_or_create(
                registry_number=registry_number,
                defaults={'ship_project': ship_project_value}
            )

            if created:
                # Судно было успешно создано (связано по registry_number)
                print(f"Создано новое судно для закупки {registry_number}")
                updated_vessels += 1
            else:
                # Судно уже существовало в базе.
                # Проверим, нужно ли обновить ему "проект судна".
                if ship_project_value and vessel.ship_project != ship_project_value:
                    vessel.ship_project = ship_project_value
                    vessel.save()
                    updated_vessels += 1

        print(f"Готово! Обновлено закупок (Purchase): {updated_purchases}")
        print(f"Обновлено записей о судах (Vessel): {updated_vessels}")


def safe_int(value):
    """
    Безопасное приведение значения к целому числу.
    Если значение '—', 'нет' или пустая строка, возвращает None.
    """
    if pd.isna(value):
        return None

    value_str = str(value).strip()

    # Если строка пустая или содержит прочерки/текст "нет"
    if not value_str or value_str in ['—', '-', 'нет', 'None']:
        return None

    try:
        # Пробуем перевести в float, а затем в int (защита от чисел вида '10.0')
        return int(float(value_str))
    except ValueError:
        print(f"Не удалось преобразовать в число: {value}")
        return None
# Запуск скрипта
# Запуск скрипта
if __name__ == "__main__":
    # 1. Указываем абсолютный путь
    db_path = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"

    # 2. ПЕРЕИНИЦИАЛИЗИРУЕМ импортированную базу правильным путем!
    db.init(db_path)

    # 3. Подключаемся
    db.connect(reuse_if_open=True)

    excel_path = r"..\..\НМЦК 2023.xlsx"
    update_database_from_excel(excel_path)

    db.close()