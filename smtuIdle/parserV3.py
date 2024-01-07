import psycopg2
import csv
import datetime
import pandas as pd
import os
import django
import sqlite3
from models import Purchase
# hostname = "localhost"
# # hostname = "db"
# username = "postgres"
# password = "sa"
# database = "test"
# port=5432
# port = connection.settings_dict.get('PORT', '')
# hostname = connection.settings_dict['HOST', '']




def connector():
    connection = sqlite3.connect('test.db')
    return connection
def insert_in_table(csv_file_path):
    errors = []
    inserted_rows = 0 
    try:
        connection = connector()
        print("Успешное подключение к базе данных")
        cursor = connection.cursor()
        with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter = ';')
            next(csv_reader)  # Пропустите заголовок, если он есть
       
            for row in csv_reader:
               
                # Обрезка слишком длинных строк
                max_length = 255  # Максимальная длина для строк
                purchase_date = row[0][:max_length] if row[0] else 'Нет данных'
                registry_number = row[1][:max_length] if row[1] else 'Нет данных'
                procurement_method = row[2][:max_length] if row[2] else 'Нет данных'
                purchase_name = row[3][:max_length] if row[3] else 'Нет данных'
                auction_subject = row[4][:max_length] if row[4] else 'Нет данных'
                purchase_identification_code = row[5][:max_length] if row[5] else 'Нет данных'
                
                try:
                    lot_number = int(row[6])
                except ValueError:
                    lot_number = 0  # Если не удалось преобразовать в int, устанавливаем значение по умолчанию
                
                lot_name = row[7][:max_length] if row[7] else 'Нет данных'
                
                try:
                    initial_max_contract_price = float(row[8])
                except ValueError:
                    initial_max_contract_price = 0.0  # Если не удалось преобразовать в float, устанавливаем значение по умолчанию
                Currency = row[9][:max_length] if row[9] else 'Нет данных'
                try:
                    InitialMaxContractPriceInCurrency = float(row[10])
                except ValueError:
                    InitialMaxContractPriceInCurrency = 0
                ContractCurrency = row[11][:max_length] if row[11] else 'Нет данных'
                OKDPClassification = row[12][:max_length] if row[12] else 'Нет данных'
                OKPDClassification = row[13][:max_length] if row[13] else 'Нет данных'
                OKPD2Classification = row[14][:max_length] if row[14] else 'Нет данных'
                PositionCode = row[15][:max_length] if row[15] else 'Нет данных'
                CustomerName = row[16][:max_length] if row[16] else 'Нет данных'
                ProcurementOrganization = row[17][:max_length] if row[17] else 'Нет данных'
                PlacementDate = row[18]
                try:
                    placementDate = datetime.datetime.strptime(PlacementDate, '%d.%m.%Y').date()
                except ValueError:
                    placementDate = None
                UpdateDate = row[19]
                try:
                    updateDate = datetime.datetime.strptime(UpdateDate, '%d.%m.%Y').date()
                except ValueError:
                    updateDate =None
                ProcurementStage = row[20][:max_length] if row[20] else 'Нет данных'
                ProcurementFeatures = row[21][:max_length] if row[21] else 'Нет данных'
                ApplicationStartDate = row[22]
                try:
                    applicationStartDate = datetime.datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationStartDate = None

                ApplicationEndDate = row[23]
                try:
                    applicationEndDate = datetime.datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationEndDate = None

                auctionDate = row[23]
                try:
                    AuctionDate = datetime.datetime.strptime(auctionDate, '%d.%m.%Y').date()
                except ValueError:
                    AuctionDate = None
                # Вставка данных в таблицу
                sql = """
     
                   
                    INSERT INTO purchase (
                            PurchaseOrder, RegistryNumber, ProcurementMethod, PurchaseName,
                            AuctionSubject, PurchaseIdentificationCode, LotNumber, LotName,
                            InitialMaxContractPrice, Currency, InitialMaxContractPriceInCurrency, 
                            ContractCurrency,OKDPClassification,OKPDClassification,
                            OKPD2Classification,PositionCode,CustomerName,ProcurementOrganization,PlacementDate,
                            UpdateDate,ProcurementStage,ProcurementFeatures,ApplicationStartDate,ApplicationEndDate,
                            AuctionDate
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
               
                data = (
                    purchase_date, registry_number, procurement_method, purchase_name,
                    auction_subject, purchase_identification_code, lot_number, lot_name,
                    initial_max_contract_price,Currency,InitialMaxContractPriceInCurrency,ContractCurrency,
                    OKDPClassification,OKPDClassification,
                    OKPD2Classification,PositionCode,CustomerName,ProcurementOrganization,placementDate,
                    updateDate,ProcurementStage,ProcurementFeatures,applicationStartDate, applicationEndDate,
                    datetime.datetime.strftime(AuctionDate, '%Y-%m-%d') if AuctionDate else None

                     )
                cursor.execute(sql, data)
                inserted_rows += cursor.rowcount

      
        connection.commit()
    
    
    except Exception as e:
        print("Ошибка подключения или вставки данных:", e)
        errors.append(str(e))  # Добавьте ошибку в список ошибок

    finally:
        connection.close()
    return inserted_rows, errors
# insert_in_table('C:/Users/Sergey/Desktop/Работа/SmtuGui/smtuIdle/OrderSearch(1-500)_20.11.2023.csv')


# Пример использования
# csv_file_path = 'C:/Users/Sergey/Desktop/Работа/SmtuGui/smtuIdle/OrderSearch(1-500)_20.11.2023.csv'
# inserted_rows_count, insert_errors = insert_in_table(csv_file_path)

# if not insert_errors:
#     print(f"Данные успешно вставлены в базу данных. Количество добавленных записей: {inserted_rows_count}")
# else:
#     print("Произошли ошибки при вставке данных:")
#     for error in insert_errors:
#         print(error)


def insert_in_table_for_users(csv_file_path):
    errors = []
    try:
        connection = connector()
        print("Успешное подключение к базе данных")
        cursor = connection.cursor()
        with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter = ';')
            next(csv_reader)  # Пропустите заголовок, если он есть
            row = next(csv_reader, None)
            if row is not None:
            # for row in csv_reader:
               
                # Обрезка слишком длинных строк
                max_length = 255  # Максимальная длина для строк
                purchase_date = row[0][:max_length] if row[0] else 'Нет данных'
                registry_number = row[1][:max_length] if row[1] else 'Нет данных'
                procurement_method = row[2][:max_length] if row[2] else 'Нет данных'
                purchase_name = row[3][:max_length] if row[3] else 'Нет данных'
                auction_subject = row[4][:max_length] if row[4] else 'Нет данных'
                purchase_identification_code = row[5][:max_length] if row[5] else 'Нет данных'
                
                try:
                    lot_number = int(row[6])
                except ValueError:
                    lot_number = 0  # Если не удалось преобразовать в int, устанавливаем значение по умолчанию
                
                lot_name = row[7][:max_length] if row[7] else 'Нет данных'
                
                try:
                    initial_max_contract_price = float(row[8])
                except ValueError:
                    initial_max_contract_price = 0.0  # Если не удалось преобразовать в float, устанавливаем значение по умолчанию
                Currency = row[9][:max_length] if row[9] else 'Нет данных'
                try:
                    InitialMaxContractPriceInCurrency = float(row[10])
                except ValueError:
                    InitialMaxContractPriceInCurrency = 0
                ContractCurrency = row[11][:max_length] if row[11] else 'Нет данных'
                OKDPClassification = row[12][:max_length] if row[12] else 'Нет данных'
                OKPDClassification = row[13][:max_length] if row[13] else 'Нет данных'
                OKPD2Classification = row[14][:max_length] if row[14] else 'Нет данных'
                PositionCode = row[15][:max_length] if row[15] else 'Нет данных'
                CustomerName = row[16][:max_length] if row[16] else 'Нет данных'
                ProcurementOrganization = row[17][:max_length] if row[17] else 'Нет данных'
                PlacementDate = row[18]
                try:
                    placementDate = datetime.datetime.strptime(PlacementDate, '%d.%m.%Y').date()
                except ValueError:
                    placementDate = None
                UpdateDate = row[19]
                try:
                    updateDate = datetime.datetime.strptime(UpdateDate, '%d.%m.%Y').date()
                except ValueError:
                    updateDate =None
                ProcurementStage = row[20][:max_length] if row[20] else 'Нет данных'
                ProcurementFeatures = row[21][:max_length] if row[21] else 'Нет данных'
                ApplicationStartDate = row[22]
                try:
                    applicationStartDate = datetime.datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationStartDate = None

                ApplicationEndDate = row[23]
                try:
                    applicationEndDate = datetime.datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationEndDate = None

                auctionDate = row[23]
                try:
                    AuctionDate = datetime.datetime.strptime(auctionDate, '%d.%m.%Y').date()
                except ValueError:
                    AuctionDate = None
                # Вставка данных в таблицу
                sql = """
     
                   INSERT INTO public."SBDsmtu_purchase" (
                        "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
                        "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
                        "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
                         "ContractCurrency","OKDPClassification","OKPDClassification",
                           "OKPD2Classification","PositionCode","CustomerName","ProcurementOrganization","PlacementDate",
                        "UpdateDate","ProcurementStage","ProcurementFeatures","ApplicationStartDate","ApplicationEndDate",
                        "AuctionDate"
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s,%s)
                        """
               
                data = (
                    purchase_date, registry_number, procurement_method, purchase_name,
                    auction_subject, purchase_identification_code, lot_number, lot_name,
                    initial_max_contract_price,Currency,InitialMaxContractPriceInCurrency,ContractCurrency,
                    OKDPClassification,OKPDClassification,
                    OKPD2Classification,PositionCode,CustomerName,ProcurementOrganization,placementDate,
                    updateDate,ProcurementStage,ProcurementFeatures,applicationStartDate, applicationEndDate,
                    AuctionDate

                )
                cursor.execute(sql, data)


        # Завершите транзакцию и закройте соединение
        connection.commit()
    
    
    except Exception as e:
        print("Ошибка подключения или вставки данных:", e)
        errors.append(str(e))  # Добавьте ошибку в список ошибок

    finally:
        connection.close()
    return errors

# def insert_in_table(csv_file_path):
#     errors = []
#     cont = True
#     registry_numbers = {} 
#     user_input = 0
#     try:
#         connection = psycopg2.connect(
#             dbname=database,
#             user=username,
#             password=password,
#             host=hostname,
#             port=port
#         )
#         cursor = connection.cursor()
#         with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
#             csv_reader = csv.reader(csv_file, delimiter = ';')
#             next(csv_reader)  # Пропустите заголовок, если он есть
#             for row in csv_reader:
#                 cont = True
#                 # Обрезка слишком длинных строк
#                 max_length = 255  # Максимальная длина для строк
#                 purchase_date = row[0][:max_length] if row[0] else 'Нет данных'
#                 registry_number = row[1][:max_length] if row[1] else 'Нет данных'
#                 procurement_method = row[2][:max_length] if row[2] else 'Нет данных'
#                 purchase_name = row[3][:max_length] if row[3] else 'Нет данных'
#                 auction_subject = row[4][:max_length] if row[4] else 'Нет данных'
#                 purchase_identification_code = row[5][:max_length] if row[5] else 'Нет данных'
                
#                 try:
#                     lot_number = int(row[6])
#                 except ValueError:
#                     lot_number = 0  # Если не удалось преобразовать в int, устанавливаем значение по умолчанию
                
#                 lot_name = row[7][:max_length] if row[7] else 'Нет данных'
                
#                 try:
#                     initial_max_contract_price = float(row[8])
#                 except ValueError:
#                     initial_max_contract_price = 0.0  # Если не удалось преобразовать в float, устанавливаем значение по умолчанию
#                 Currency = row[9][:max_length] if row[9] else 'Нет данных'
#                 try:
#                     InitialMaxContractPriceInCurrency = float(row[10])
#                 except ValueError:
#                     InitialMaxContractPriceInCurrency = 0
#                 ContractCurrency = row[11][:max_length] if row[11] else 'Нет данных'
#                 OKDPClassification = row[12][:max_length] if row[12] else 'Нет данных'
#                 OKPDClassification = row[13][:max_length] if row[13] else 'Нет данных'
#                 OKPD2Classification = row[14][:max_length] if row[14] else 'Нет данных'
#                 PositionCode = row[15][:max_length] if row[15] else 'Нет данных'
#                 CustomerName = row[16][:max_length] if row[16] else 'Нет данных'
#                 ProcurementOrganization = row[17][:max_length] if row[17] else 'Нет данных'
#                 PlacementDate = row[18]
#                 try:
#                     placementDate = datetime.datetime.strptime(PlacementDate, '%d.%m.%Y').date()
#                 except ValueError:
#                     placementDate = None
#                 UpdateDate = row[19]
#                 try:
#                     updateDate = datetime.datetime.strptime(UpdateDate, '%d.%m.%Y').date()
#                 except ValueError:
#                     updateDate =None
#                 ProcurementStage = row[20][:max_length] if row[20] else 'Нет данных'
#                 ProcurementFeatures = row[21][:max_length] if row[21] else 'Нет данных'
#                 ApplicationStartDate = row[22]
#                 try:
#                     applicationStartDate = datetime.datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
#                 except ValueError:
#                     applicationStartDate = None

#                 ApplicationEndDate = row[23]
#                 try:
#                     applicationEndDate = datetime.datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
#                 except ValueError:
#                     applicationEndDate = None

#                 auctionDate = row[23]
#                 try:
#                     AuctionDate = datetime.datetime.strptime(auctionDate, '%d.%m.%Y').date()
#                 except ValueError:
#                     applicationEndDate = None
#                 # Вставка данных в таблицу


#                 select_sql = """
#                 SELECT "RegistryNumber", "AuctionDate", "ApplicationStartDate", "ApplicationEndDate", "UpdateDate","PlacementDate"
#                 FROM public."SBDsmtu_purchase" 
#                 WHERE "RegistryNumber" = %s
#                 """
#                 data = (registry_number,)
#                 cursor.execute(select_sql, data)
#                 existing_records = cursor.fetchall()

#                 for existing_record in existing_records:
#                     print(f"Различия для записи с {registry_number}:")
#                     if existing_record[1] != AuctionDate:
#                         print(f"  - Дата аукциона: Старое - {existing_record[1]}, Новое - {AuctionDate}")
#                     if existing_record[2] != applicationStartDate:
#                         print(f"  - Дата начала заявки: Старое - {existing_record[2]}, Новое - {applicationStartDate}")
#                     if existing_record[3] != applicationEndDate:
#                         print(f"  - Дата окончания заявки: Старое - {existing_record[3]}, Новое - {applicationEndDate}")
#                     if existing_record[4] != updateDate:
#                         print(f"  - Дата обновления: Старое - {existing_record[4]}, Новое - {updateDate}")
#                     if existing_record[5] != placementDate:
#                         print(f"  - Дата размещения: Старое - {existing_record[5]}, Новое - {placementDate}")

#                     user_input = input(f"Запись с таким {registry_number} уже существует и имеет отличия в датах. Хотите добавить эту запись? (да/нет): ")
#                     if user_input.lower() != "да":
#                             cont = False
#                             continue
#                     else:
#                         cont = True
#                 if cont != False:
                   
#                     sql = """
        
#                     INSERT INTO public."SBDsmtu_purchase" (
#                             "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
#                             "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
#                             "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
#                             "ContractCurrency","OKDPClassification","OKPDClassification",
#                             "OKPD2Classification","PositionCode","CustomerName","ProcurementOrganization","PlacementDate",
#                             "UpdateDate","ProcurementStage","ProcurementFeatures","ApplicationStartDate","ApplicationEndDate",
#                             "AuctionDate"
#                         )
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s,%s)
#                             """
                
#                     data = (
#                         purchase_date, registry_number, procurement_method, purchase_name,
#                         auction_subject, purchase_identification_code, lot_number, lot_name,
#                         initial_max_contract_price,Currency,InitialMaxContractPriceInCurrency,ContractCurrency,
#                         OKDPClassification,OKPDClassification,
#                         OKPD2Classification,PositionCode,CustomerName,ProcurementOrganization,placementDate,
#                         updateDate,ProcurementStage,ProcurementFeatures,applicationStartDate, applicationEndDate,
#                         AuctionDate

#                     )
#                     cursor.execute(sql, data)

             

#         # Завершите транзакцию и закройте соединение
#         connection.commit()
    
    
#     except Exception as e:
#         print("Ошибка подключения или вставки данных:", e)
#         errors.append(str(e))  # Добавьте ошибку в список ошибок

#     finally:
#         connection.close()
#         os.remove(csv_file_path)

#     return errors





# insert_in_table("C:\\Users\\Sergey\\Desktop\\Работа\\ParserV2\\smtubase\\OrderSearch(1-261)_22.09.2023 строительство судна.csv")




# def get_differences_for_record(cursor, registry_number, AuctionDate, applicationStartDate, applicationEndDate, updateDate, placementDate):
#     select_sql = """
#     SELECT "RegistryNumber", "AuctionDate", "ApplicationStartDate", "ApplicationEndDate", "UpdateDate","PlacementDate"
#     FROM SBDsmtu_purchase 
#     WHERE "RegistryNumber" = %s
#     """
#     data = (registry_number,)
#     cursor.execute(select_sql, data)
#     existing_records = cursor.fetchall()

#     differences = []
#     for existing_record in existing_records:
#         difference = {
#             'registry_number': registry_number,
#             'AuctionDate': AuctionDate,
#             'applicationStartDate': applicationStartDate,
#             'applicationEndDate': applicationEndDate,
#             'updateDate': updateDate,
#             'placementDate': placementDate,
#             'existing_record': existing_record,
#         }

#         differences.append(difference)

#     return differences
#   sql = """
     
#                    INSERT INTO public."SBDsmtu_purchase" (
#                         "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
#                         "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
#                         "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
#                          "ContractCurrency","OKDPClassification","OKPDClassification",
#                            "OKPD2Classification","PositionCode","CustomerName","ProcurementOrganization","PlacementDate",
#                         "UpdateDate","ProcurementStage","ProcurementFeatures","ApplicationStartDate","ApplicationEndDate",
#                         "AuctionDate"
#                     )
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s,%s)

#                     ON CONFLICT ("RegistryNumber") DO UPDATE SET
#                     "RegistryNumber" = EXCLUDED."RegistryNumber",
#                     "ProcurementMethod" = EXCLUDED."ProcurementMethod",
#                     "PurchaseName" = EXCLUDED."PurchaseName",
#                     "AuctionSubject" = EXCLUDED."AuctionSubject",
#                     "PurchaseIdentificationCode" = EXCLUDED."PurchaseIdentificationCode",
#                     "LotNumber" = EXCLUDED."LotNumber",
#                     "LotName" = EXCLUDED."LotName",
#                     "InitialMaxContractPrice" = EXCLUDED."InitialMaxContractPrice",
#                     "Currency" = EXCLUDED."Currency",
#                     "InitialMaxContractPriceInCurrency" = EXCLUDED."InitialMaxContractPriceInCurrency",
#                     "ContractCurrency" = EXCLUDED."ContractCurrency",
#                     "OKDPClassification" = EXCLUDED."OKDPClassification",
#                     "OKPDClassification" = EXCLUDED."OKPDClassification",
#                     "OKPD2Classification" = EXCLUDED."OKPD2Classification",
#                     "PositionCode" = EXCLUDED."PositionCode",
#                     "CustomerName" = EXCLUDED."CustomerName",
#                     "ProcurementOrganization" = EXCLUDED."ProcurementOrganization",
#                     "PlacementDate" = EXCLUDED."PlacementDate",
#                     "UpdateDate" = EXCLUDED."UpdateDate",
#                     "ProcurementStage" = EXCLUDED."ProcurementStage",
#                     "ProcurementFeatures" = EXCLUDED."ProcurementFeatures",
#                     "ApplicationStartDate" = EXCLUDED."ApplicationStartDate",
#                     "ApplicationEndDate" = EXCLUDED."ApplicationEndDate",
#                     "AuctionDate" = EXCLUDED."AuctionDate";
#                         """
# def export_to_excel(output_excel_path):
#     try:
#         connection = psycopg2.connect(
#             dbname=database,
#             user=username,
#             password=password,
#             host=hostname,
#             port=port
#         )
#         print("Успешное подключение к базе данных")
#         cursor = connection.cursor()

#         # Выполните SQL-запрос для извлечения данных из базы данных
#         query = """
#             SELECT
#                 "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
#                 "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
#                 "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
#                 "ContractCurrency", "OKDPClassification", "OKPDClassification",
#                 "OKPD2Classification", "PositionCode", "CustomerName", "ProcurementOrganization",
#                 "PlacementDate", "UpdateDate", "ProcurementStage", "ProcurementFeatures",
#                 "ApplicationStartDate", "ApplicationEndDate", "AuctionDate"
#             FROM public."SBDsmtu_purchase";
#         """
#         cursor.execute(query)

#         # Получите результаты запроса в виде списка кортежей
#         data = cursor.fetchall()

#         # Создайте DataFrame из данных
#         df = pd.DataFrame(data, columns=[
#              "НомерЗакупки", "РеестровыйНомер", "СпособЗакупки", "НаименованиеЗакупки",
#             "ПредметТоргов", "ИдентификационныйКодЗакупки", "НомерЛота", "НаименованиеЛота",
#             "НачальнаяМаксСтоимость", "Валюта", "НачальнаяМаксСтоимостьВВалюте",
#             "ВалютаКонтракта", "КлассификацияПоОКДП", "КлассификацияПоОКДП",
#             "КлассификацияПоОКДП2", "КодПозиции", "НаименованиеЗаказчика", "ОрганизацияЗакупки",
#             "ДатаРазмещения", "ДатаОбновления", "СтадияЗакупки", "ОсобенностиЗакупки",
#             "ДатаНачалаПриемаЗаявок", "ДатаОкончанияПриемаЗаявок", "ДатаТоргов"
#         ])

#         # Сохраните данные в файл Excel
#         df.to_excel(output_excel_path, index=False, engine='openpyxl')

#     except Exception as e:
#         print("Ошибка при извлечении данных:", e)

#     finally:
#         connection.close()

# export_to_excel('test.xlsx')


def export_to_excel(data, output_excel_path, filters):
    try:
        # Создайте DataFrame из данных
        filter_df = pd.DataFrame([filters],columns=[
    "search_input", "filter_criteria", "purchase_order", "start_date", "end_date", "min_price", "max_price"
])
        
        filter_column_translation = {
    "search_input": "Поисковый Запрос",
    "filter_criteria": "Критерии Фильтра",
    "purchase_order": "Заказ Закупки",
    "start_date": "Дата Начала",
    "end_date": "Дата Окончания",
    "min_price": "Минимальная Цена",
    "max_price": "Максимальная Цена"
}
        # Замените пустые значения фильтров на пустые строки для правильного отображения в Excel
        filter_df.fillna('', inplace=True)
        selected_data = [tuple[:56] for tuple in data]
        # Создайте DataFrame с данными
        data_df = pd.DataFrame(selected_data, columns=["Id",
             "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
                 "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
                 "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
                 "ContractCurrency", "OKDPClassification", "OKPDClassification",
                 "OKPD2Classification", "PositionCode", "CustomerName", "ProcurementOrganization",
                 "PlacementDate", "UpdateDate", "ProcurementStage", "ProcurementFeatures",
                "ApplicationStartDate", "ApplicationEndDate", "AuctionDate","QueryCount","ResponseCount",
                "AveragePrice","MinPrice","MaxPrice","StandardDeviation","CoefficientOfVariation","TKPData","NMCKMarket",
                "FinancingLimit","conId",
                 "TotalApplications", "AdmittedApplications", "RejectedApplications",
                "PriceProposal", "Applicant", "Applicant_satatus", "WinnerExecutor",
                "ContractingAuthority", "ContractIdentifier", "RegistryNumber_contract",
                "ContractNumber", "StartDate", "EndDate", "ContractPrice", "AdvancePayment",
                "ReductionNMC", "ReductionNMCPercent", "SupplierProtocol", "ContractFile",
        ])

        # Создайте словарь для перевода названий столбцов
        column_translation = {
            "Id":"Номер",
        "PurchaseOrder": "Закон",
        "RegistryNumber": "Реестровый Номер",
        "ProcurementMethod": "Метод Закупки",
        "PurchaseName": "Название Закупки",
        "AuctionSubject": "Тема Аукциона",
        "PurchaseIdentificationCode": "Идентификационный Код Закупки",
        "LotNumber": "Номер Лота",
        "LotName": "Название Лота",
        "InitialMaxContractPrice": "Начальная Максимальная Цена Контракта",
        "Currency": "Валюта",
        "InitialMaxContractPriceInCurrency": "Начальная Максимальная Цена Контракта в Валюте",
        "ContractCurrency": "Валюта Контракта",
        "OKDPClassification": "Классификация ОКДП",
        "OKPDClassification": "Классификация ОКПД",
        "OKPD2Classification": "Классификация ОКПД2",
        "PositionCode": "Код Позиции",
        "CustomerName": "Наименование Заказчика",
        "ProcurementOrganization": "Организация Закупки",
        "PlacementDate": "Дата Размещения",
        "UpdateDate": "Дата Обновления",
        "ProcurementStage": "Этап Закупки",
        "ProcurementFeatures": "Особенности Закупки",
        "ApplicationStartDate": "Дата Начала Подачи Заявок",
        "ApplicationEndDate": "Дата Окончания Подачи Заявок",
        "AuctionDate": "Дата Аукциона",
        "QueryCount":"Количество запросов",
        "ResponseCount":"Количество ответов",
        "AveragePrice":"Среднее значение цены",
        "MinPrice":"Минимальная цена",
        "MaxPrice":"Максимальная цена",
        "StandardDeviation":"Среднее квадратичное отклонение",
        "CoefficientOfVariation":"Коэффициент вариации",
        "TKPData":"ТКП",
        "NMCKMarket":"Цена рыночная",
        "FinancingLimit":"Лимит финансирования",
        "TotalApplications": "Общее количество заявок",
        "conId":"Номер контракта",
        "AdmittedApplications": "Общее количество допущенных заявок",
        "RejectedApplications": "Общее количество отклоненных заявок",
        "PriceProposal": "Ценовое предложение",
        "Applicant": "Заявитель",
        "Applicant_status": "Статус заявителя",
        "WinnerExecutor": "Победитель-исполнитель контракта",
        "ContractingAuthority": "Заказчик по контракту",
        "ContractIdentifier": "Идентификатор договора",
        "RegistryNumber_contract": "Реестровый номер договора",
        "ContractNumber": "№ договора",
        "StartDate": "Дата начала/подписания",
        "EndDate": "Дата окончания/исполнения",
        "ContractPrice": "Цена договора, руб.",
        "AdvancePayment": "Размер авансирования, руб./(%)",
        "ReductionNMC": "Снижение НМЦК, руб.",
        "ReductionNMCPercent": "Снижение НМЦК, %",
        "SupplierProtocol": "Протоколы определения поставщика (выписка)",
        "ContractFile": "Договор",
    }

        filter_df.rename(columns=filter_column_translation, inplace=True)

        data_df.rename(columns=column_translation, inplace=True)
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            filter_df.to_excel(writer, index=False)
            data_df.to_excel(writer, startrow=2, header=True, index=False)

    except Exception as e:
        print("Ошибка при экспорте данных в Excel:", e)

# import numpy as np
# import statistics
# tkp_values_all = [4650000000,4001165000,5500000000]
# standard_deviation = statistics.stdev(tkp_values_all)
# print(standard_deviation)

def find_records_with_differences():
    try:
        connection = connector()
        cursor = connection.cursor()

        # SQL-запрос для поиска записей с одинаковым "RegistryNumber", но различными значениями в полях "AuctionDate", "ApplicationStartDate", "ApplicationEndDate", "UpdateDate" и "PlacementDate"
        sql = """
        SELECT Id, RegistryNumber, AuctionDate, ApplicationStartDate, ApplicationEndDate, UpdateDate, PlacementDate,LotNumber
        FROM purchase
        WHERE RegistryNumber IN (
            SELECT RegistryNumber
            FROM purchase
            GROUP BY RegistryNumber
            HAVING COUNT(*) > 1
        )
    """
        cursor.execute(sql)
        records_with_differences = cursor.fetchall()

        # SQL-запрос для подсчета числа записей с повторами
        count_sql = """
        SELECT COUNT(*)
        FROM (
            SELECT RegistryNumber
            FROM purchase
            GROUP BY RegistryNumber
            HAVING COUNT(*) > 1
        ) AS DuplicateRegistryNumbers
        """

        cursor.execute(count_sql)
        count_of_duplicates = cursor.fetchone()[0]

        # Закрытие соединения
        connection.close()

        return records_with_differences, count_of_duplicates

    except Exception as e:
        print("Ошибка при поиске записей с различиями:", e)
        return [], 0
# result, count = find_records_with_differences()
# print("Записи с различиями:", result)
# print("Количество записей с повторами:", count)
# Вызов функции для поиска записей с различиями
# records_with_differences = find_records_with_differences()

# if records_with_differences:
#     for record in records_with_differences:
#         record_id = record[0]
#         registry_number = record[1]
#         auction_date = record[2]
#         application_start_date = record[3]
#         application_end_date = record[4]
#         update_date = record[5]
#         placement_date = record[6]

#         print(f"Id: {record_id}, RegistryNumber: {registry_number}, AuctionDate: {auction_date}, ApplicationStartDate: {application_start_date}, ApplicationEndDate: {application_end_date}, UpdateDate: {update_date}, PlacementDate: {placement_date}")
# else:
#     print("Записей с различиями не найдено.")

def count_total_records():
    try:
        connection = connector()
        cursor = connection.cursor()

        # Выполнение запроса на подсчет общего количества записей
        cursor.execute("SELECT COUNT(*) FROM purchase")
        result = cursor.fetchone()

        # Если запрос вернул результат, выведите общее количество записей
        if result:
            total_records = result[0]
            print(f"Общее количество записей в таблице: {total_records}")
        else:
            print("Не удалось получить общее количество записей.")

    except sqlite3.Error as e:
        print("Ошибка при подсчете общего количества записей:", e)
    
    finally:
        connection.close()
    return total_records

# Пример использования

# print(count_total_records())
def delete_records_by_id(record_ids):
    try:
        # Подключение к базе данных
        connection = connector()
         
        # SQL-запрос для удаления записей по Id
        query = Purchase.delete().where(Purchase.Id.in_(record_ids))
        for record_id in record_ids:
            purchase = Purchase.get(Purchase.Id == record_id)
            purchase.delete_instance(recursive=True)
        query.execute()

        # Закрытие соединения
        connection.close()

        return True

    except Exception as e:
        print("Ошибка при удалении записей по Id:", e)
        return False     
# delete_records_by_id([3])
# def delete_records_by_id(record_ids):
#     try:
#         connection = connector()
#         cursor = connection.cursor()

#         # SQL-запрос для удаления записей по Id
#         sql = """
#             DELETE FROM public."SBDsmtu_purchase"
#             WHERE "Id" IN %s
#         """

#         cursor.execute(sql, (tuple(record_ids),))

#         # Закрытие соединения и сохранение изменений
#         connection.commit()
#         connection.close()

#         return True

#     except Exception as e:
#         print("Ошибка при удалении записей по Id:", e)
#         return False