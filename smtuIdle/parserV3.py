
import csv
import sqlite3
from datetime import datetime, date
import pandas as pd
from smtuIdle.BD.models import *
from peewee import SqliteDatabase
# hostname = "localhost"
# # hostname = "db"
# username = "postgres"
# password = "sa"
# database = "test"
# port=5432
# port = connection.settings_dict.get('PORT', '')
# hostname = connection.settings_dict['HOST', '']
DB_PATH = r"C:\Users\Sergey\Desktop\Work\SmtuGui\smtuIdle\database.db"
db = sqlite3.connect(DB_PATH)



def connector():
    connection = sqlite3.connect('database.db')
    return connection
def insert_in_table(csv_file_path):
    errors = []
    inserted_rows = 0
    connection = None
    try:
        print("Успешное подключение к базе данных")
        connection = db
        cursor = db.cursor()

        with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            next(csv_reader)

            for row in csv_reader:

                max_length = 512
                purchase_date = row[0][:max_length] if row[0] else 'Нет данных'

                # Убираем '№' из значения CSV, так как в БД номера хранятся без него
                registry_number_raw = row[1][:max_length] if row[1] else 'Нет данных'
                registry_number = registry_number_raw.replace('№', '').strip()

                procurement_method = row[2][:max_length] if row[2] else 'Нет данных'
                purchase_name = row[3][:max_length] if row[3] else 'Нет данных'
                auction_subject = row[4][:max_length] if row[4] else 'Нет данных'
                purchase_identification_code = row[5][:max_length] if row[5] else 'Нет данных'

                try:
                    lot_number = int(row[6])
                except ValueError:
                    lot_number = 0

                lot_name = row[7][:max_length] if row[7] else 'Нет данных'

                try:
                    initial_max_contract_price = float(row[8])
                except ValueError:
                    initial_max_contract_price = 0.0

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
                    placementDate = datetime.strptime(PlacementDate, '%d.%m.%Y').date()
                except ValueError:
                    placementDate = None

                UpdateDate = row[19]
                try:
                    updateDate = datetime.strptime(UpdateDate, '%d.%m.%Y').date()
                except ValueError:
                    updateDate = None

                ProcurementStage = row[20][:max_length] if row[20] else 'Нет данных'
                ProcurementFeatures = row[21][:max_length] if row[21] else 'Нет данных'

                ApplicationStartDate = row[22]
                try:
                    applicationStartDate = datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationStartDate = None

                ApplicationEndDate = row[23]
                try:
                    applicationEndDate = datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationEndDate = None

                auctionDate = row[24]
                try:
                    AuctionDate = datetime.strptime(auctionDate, '%d.%m.%Y').date()
                except ValueError:
                    AuctionDate = None

                # Обновляем только те строки, где RegistryNumber совпадает
                updated_count = (
                    Purchase.update(
                        ProcurementMethod=procurement_method,
                        PurchaseName=purchase_name,
                        AuctionSubject=auction_subject,
                        PurchaseIdentificationCode=purchase_identification_code,
                        LotNumber=lot_number,
                        LotName=lot_name,
                        Currency=Currency,
                        ContractCurrency=ContractCurrency,
                        OKDPClassification=OKDPClassification,
                        OKPDClassification=OKPDClassification,
                        OKPD2Classification=OKPD2Classification,
                        PositionCode=PositionCode,
                        CustomerName=CustomerName,
                        ProcurementOrganization=ProcurementOrganization,
                    )
                    .where(Purchase.RegistryNumber == registry_number)
                    .execute()
                )

                if updated_count > 0:
                    inserted_rows += 1

        connection.commit()

    except Exception as e:
        print("Ошибка подключения или вставки данных:", e)
        errors.append(str(e))

    finally:
        if connection is not None:
            connection.close()
        print("done")

    return inserted_rows, errors

def insert_in_table_full(csv_file_path):
    print("Start")
    errors = []
    updated_rows = 0
    skipped_rows = 0

    try:
        with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            next(csv_reader)

            for row in csv_reader:
                max_length = 512

                purchase_order      = row[2][:max_length] if row[2] else 'Нет данных'
                registry_number     = row[0].lstrip('№').strip()[:max_length] if row[0] else 'Нет данных'
                procurement_method  = row[3][:max_length] if row[3] else 'Нет данных'
                purchase_name       = row[4][:max_length] if row[4] else 'Нет данных'
                auction_subject     = row[7][:max_length] if row[7] else 'Нет данных'
                lot_name            = row[7][:max_length] if row[7] else 'Нет данных'
                customer_name       = row[5][:max_length] if row[5] else 'Нет данных'
                currency            = row[63] if row[63] else 'Нет данных'
                okpd2               = row[64] if row[64] else 'Нет данных'
                purchase_status     = row[31][:max_length] if row[31] else 'Нет данных'
                notification_link   = 'Нет данных'

                try:
                    lot_number = int(row[6])
                except (ValueError, IndexError):
                    lot_number = 0

                try:
                    initial_max_contract_price = float(row[8])
                except (ValueError, IndexError):
                    initial_max_contract_price = 0.0

                try:
                    initial_max_contract_price_in_currency = float(row[10])
                except (ValueError, IndexError):
                    initial_max_contract_price_in_currency = 0.0

                try:
                    quantity_units = int(row[6]) if row[6] else 0
                except (ValueError, IndexError):
                    quantity_units = 0

                try:
                    nmck_per_unit = float(row[9]) if row[9] else 0.0
                except (ValueError, IndexError):
                    nmck_per_unit = 0.0

                def parse_date(value):
                    try:
                        return datetime.strptime(value, '%d.%m.%Y').date()
                    except (ValueError, TypeError):
                        return None

                def safe_int(val, default=0):
                    try:
                        return int(val) if val else default
                    except ValueError:
                        return default

                def safe_float(val, default=0.0):
                    try:
                        return float(val) if val else default
                    except ValueError:
                        return default

                # placement_date         = parse_date(row[1])
                # application_end_date   = parse_date(row[1])
                # auction_date_val       = parse_date(row[1])
                # application_start_date = parse_date(row[10])

                tkp_data_dict = {}
                for i in range(10):
                    try:
                        val = int(row[13 + i])
                        tkp_data_dict[f"ТКП №{1 + i}"] = val
                    except (ValueError, IndexError):
                        pass
                tkp_data_json = json.dumps(tkp_data_dict, ensure_ascii=False)

                query_count              = safe_int(row[11])
                response_count           = safe_int(row[12])
                average_price            = safe_float(row[23])
                min_price                = safe_float(row[24])
                max_price                = safe_float(row[25])
                standard_deviation       = safe_float(row[26])
                coefficient_of_variation = safe_float(row[27])
                nmck_market              = safe_float(row[29])
                financing_limit          = safe_float(row[30])

                total_applications    = row[32] if row[32] else 0
                admitted_applications = row[33] if row[33] else 0
                rejected_applications = row[34] if row[34] else 0

                price_proposal_dict   = {}
                applicant_dict        = {}
                applicant_status_dict = {}
                k = 1
                for i in range(0, 17, 3):
                    try:
                        price_proposal_dict[f"Ценовое предложение №{k}"] = row[35 + i]
                    except IndexError:
                        pass
                    try:
                        applicant_dict[f"Заявитель №{k}"] = row[36 + i]
                    except IndexError:
                        pass
                    try:
                        applicant_status_dict[f"Статус заявителя №{k}"] = row[37 + i]
                    except IndexError:
                        pass
                    k += 1

                price_proposal_json   = json.dumps(price_proposal_dict, ensure_ascii=False)
                applicant_json        = json.dumps(applicant_dict, ensure_ascii=False)
                applicant_status_json = json.dumps(applicant_status_dict, ensure_ascii=False)

                contracting_authority = row[53] if row[53] else ''
                winner_executor       = row[54] if row[54] else ''
                contract_identifier   = row[55] if row[55] else ''
                contract_reg_number   = row[56].lstrip('№').strip() if row[56] else ''
                contract_number       = row[57] if row[57] else ''
                contract_price        = safe_float(row[58])
                start_date            = parse_date(row[59])
                end_date              = parse_date(row[60])
                advance_payment       = safe_float(row[61])
                reduction_nmc_percent = safe_float(row[62])
                reduction_nmc         = safe_float(row[68])

                # ── Только UPDATE, без INSERT ─────────────────
                try:
                    existing_purchase = Purchase.get(Purchase.RegistryNumber == registry_number)
                except Purchase.DoesNotExist:
                    print(f"[SKIP] Закупка не найдена в БД: {registry_number}")
                    skipped_rows += 1
                    continue  # ← пропускаем строку, ничего не создаём

                purchase_data = dict(
                    PurchaseOrder=purchase_order,
                    ProcurementMethod=procurement_method,
                    PurchaseName=purchase_name,
                    AuctionSubject=auction_subject,
                    PurchaseIdentificationCode='Нет данных',
                    LotNumber=lot_number,
                    LotName=lot_name,
                    InitialMaxContractPrice=initial_max_contract_price,
                    Currency=currency,
                    InitialMaxContractPriceInCurrency=initial_max_contract_price_in_currency,
                    ContractCurrency=currency,
                    OKDPClassification='Нет данных',
                    OKPDClassification='Нет данных',
                    OKPD2Classification=okpd2,
                    PositionCode='Нет данных',
                    CustomerName=customer_name,
                    ProcurementOrganization='Нет данных',
                    # PlacementDate=placement_date,
                    # UpdateDate=placement_date,
                    ProcurementStage='Нет данных',
                    ProcurementFeatures='Нет данных',
                    # ApplicationStartDate=application_start_date,
                    # ApplicationEndDate=application_end_date,
                    # AuctionDate=auction_date_val,
                    TKPData=tkp_data_json,
                    QueryCount=query_count,
                    ResponseCount=response_count,
                    AveragePrice=average_price,
                    MinPrice=min_price,
                    MaxPrice=max_price,
                    StandardDeviation=standard_deviation,
                    CoefficientOfVariation=coefficient_of_variation,
                    NMCKMarket=nmck_market,
                    FinancingLimit=financing_limit,
                    PurchaseStatus=purchase_status,
                    quantity_units=quantity_units,
                    nmck_per_unit=nmck_per_unit,
                    notification_link=notification_link,
                    isChanged=True,
                )

                Purchase.update(purchase_data).where(Purchase.RegistryNumber == registry_number).execute()

                contract_data = dict(
                    TotalApplications=total_applications,
                    AdmittedApplications=admitted_applications,
                    RejectedApplications=rejected_applications,
                    PriceProposal=price_proposal_json,
                    Applicant=applicant_json,
                    Applicant_satatus=applicant_status_json,
                    ContractingAuthority=contracting_authority,
                    WinnerExecutor=winner_executor,
                    ContractIdentifier=contract_identifier,
                    RegistryNumber=contract_reg_number,
                    ContractNumber=contract_number,
                    ContractPrice=contract_price,
                    StartDate=start_date,
                    EndDate=end_date,
                    AdvancePayment=advance_payment,
                    ReductionNMCPercent=reduction_nmc_percent,
                    ReductionNMC=reduction_nmc,
                    ContractFile='Нет данных',
                    SupplierProtocol='Нет данных',
                )

                updated_contract = (Contract
                                    .update(contract_data)
                                    .where(Contract.purchase == existing_purchase.Id)
                                    .execute())

                if updated_contract == 0:
                    print(f"[SKIP CONTRACT] Контракт не найден для закупки: {registry_number}")

                updated_rows += 1

    except Exception as e:
        print("Ошибка при обработке файла:", e)
        errors.append(str(e))

    print(f"End: обновлено {updated_rows}, пропущено {skipped_rows}")
    return updated_rows, skipped_rows, errors

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
                    placementDate = datetime.strptime(PlacementDate, '%d.%m.%Y').date()
                except ValueError:
                    placementDate = None
                UpdateDate = row[19]
                try:
                    updateDate = datetime.strptime(UpdateDate, '%d.%m.%Y').date()
                except ValueError:
                    updateDate =None
                ProcurementStage = row[20][:max_length] if row[20] else 'Нет данных'
                ProcurementFeatures = row[21][:max_length] if row[21] else 'Нет данных'
                ApplicationStartDate = row[22]
                try:
                    applicationStartDate = datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationStartDate = None

                ApplicationEndDate = row[23]
                try:
                    applicationEndDate = datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationEndDate = None

                auctionDate = row[23]
                try:
                    AuctionDate = datetime.strptime(auctionDate, '%d.%m.%Y').date()
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
        # selected_data = [tuple[:69] for tuple in data]
       
        selected_columns = ["Id",
             "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
                 "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
                 "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
                 "ContractCurrency", "OKDPClassification", "OKPDClassification",
                 "OKPD2Classification", "PositionCode", "CustomerName", "ProcurementOrganization",
                 "PlacementDate", "UpdateDate", "ProcurementStage", "ProcurementFeatures",
                "ApplicationStartDate", "ApplicationEndDate", "AuctionDate","QueryCount","ResponseCount",
                "AveragePrice","MinPrice","MaxPrice","StandardDeviation","CoefficientOfVariation","TKPData","NMCKMarket",
                "FinancingLimit", "InitialMaxContractPriceOld","notification_link","quantity_units",
                "nmck_per_unit",
                "TotalApplications", "AdmittedApplications", "RejectedApplications",
                "PriceProposal", "Applicant", "Applicant_satatus", "WinnerExecutor",
                "ContractingAuthority", "ContractIdentifier", "RegistryNumber_contract",
                "ContractNumber", "StartDate", "EndDate", "ContractPrice", "AdvancePayment",
                "ReductionNMC", "ReductionNMCPercent", "SupplierProtocol", "ContractFile",

                "RequestMethod","PublicInformationMethod","NMCObtainedMethods","CostMethodNMC",
                "ComparablePrice","NMCMethodsTwo","CEIComparablePrices","CEICostMethod","CEIMethodsTwo",
                
                "CurrencyValue","CurrentCurrency","DateValueChanged","CurrencyRateDate","PreviousCurrency", ]
        selected_data = [[t[selected_columns.index(col)] for col in selected_columns] for t in data]
        # print(selected_data[0])
        # Создайте DataFrame с данными
        data_df = pd.DataFrame(selected_data, columns=selected_columns)

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
        "InitialMaxContractPriceOld":"Прошлая цена",
        "TotalApplications": "Общее количество заявок",
        "AdmittedApplications": "Общее количество допущенных заявок",
        "RejectedApplications": "Общее количество отклоненных заявок",
        "PriceProposal": "Ценовое предложение",
        "Applicant": "Заявитель",
        "Applicant_satatus": "Статус заявителя",
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
        "RequestMethod":"Способ направления запросов о предоставлении ценовой информации",
        "PublicInformationMethod": "Способ использования общедоступной информации",
        "NMCObtainedMethods": "НМЦК, полученная различными способами", 
        "CostMethodNMC": "НМЦК на основе затратного метода, руб. (в случае его применения)",
        "ComparablePrice": "Цена сравнимой продукции",
        "NMCMethodsTwo": "НМЦК, полученная с применением двух методов",
        "CEIComparablePrices": "ЦКЕИ на основе метода сопоставимых рыночных цен",
        "CEICostMethod": "ЦКЕИ на основе затратного метода, руб. (в случае его применения)",
        "CEIMethodsTwo":"ЦКЕИ, полученная с применением двух методов",
        "CurrencyValue" :"Значение валюты",
        "CurrentCurrency" :"Текущая валюта",
        "DateValueChanged" :"Дата изменения значения валюты",
        "CurrencyRateDate" :"Дата курса валюты",
        "PreviousCurrency" :"Предыдущая валюта",
        "notification_link":"Извещение о закупке",
        "quantity_units":"Количество единиц",
        "nmck_per_unit":"НМЦК за единицу",

    }

        filter_df.rename(columns=filter_column_translation, inplace=True)

        data_df.rename(columns=column_translation, inplace=True)
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            filter_df.to_excel(writer, index=False)
            data_df.to_excel(writer, startrow=2, header=True, index=False)
        return True
    except Exception as e:
        print("Ошибка при экспорте данных в Excel:", e)

def export_to_excel_contract(data, output_excel_path, filters):
    try:
        filter_df = pd.DataFrame([filters], columns=[
            "filter_criteria", "start_date", "end_date", "min_price", "max_price"
        ])
        filter_column_translation = {
            "filter_criteria": "Критерии фильтра",
            "start_date":      "Дата начала",
            "end_date":        "Дата окончания",
            "min_price":       "Минимальная цена",
            "max_price":       "Максимальная цена",
        }
        filter_df.fillna('', inplace=True)
        filter_df.rename(columns=filter_column_translation, inplace=True)

        rows = []
        for t in data:
            rows.append({
                "Номер закупки":                                t.get("purchase_id", ''),
                "Реестровый номер контракта":                   t.get("RegistryNumber", ''),
                "№ договора":                                   t.get("ContractNumber", ''),
                "Дата начала / подписания":                     t.get("StartDate", ''),
                "Дата окончания / исполнения":                  t.get("EndDate", ''),
                "Цена договора, руб.":                          t.get("ContractPrice", ''),
                "Заказчик по контракту":                        t.get("ContractingAuthority", ''),
                "Победитель-исполнитель контракта":             t.get("WinnerExecutor", ''),
                "Общее кол-во заявок":                          t.get("TotalApplications", ''),
                "Допущенных заявок":                            t.get("AdmittedApplications", ''),
                "Отклонённых заявок":                           t.get("RejectedApplications", ''),
                "Ценовое предложение":                          t.get("PriceProposal", ''),
                "Заявитель":                                    t.get("Applicant", ''),
                "Статус заявителя":                             t.get("Applicant_satatus", ''),
                "Идентификатор договора":                       t.get("ContractIdentifier", ''),
                "Размер авансирования, руб. (%)":               t.get("AdvancePayment", ''),
                "Снижение НМЦК, руб.":                          t.get("ReductionNMC", ''),
                "Снижение НМЦК, %":                             t.get("ReductionNMCPercent", ''),
                "Протоколы определения поставщика (выписка)":   t.get("SupplierProtocol", ''),
                "Договор":                                      t.get("ContractFile", ''),
            })

        data_df = pd.DataFrame(rows)
        data_df.fillna('', inplace=True)

        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            filter_df.to_excel(writer, index=False)
            data_df.to_excel(writer, startrow=2, header=True, index=False)

        return True

    except Exception as e:
        print("Ошибка при экспорте данных в Excel:", e)
        return False


def export_to_excel_all(data, output_excel_path):
    try:
        # Создайте DataFrame из данных

       
        selected_columns = ["Id",
             "PurchaseOrder", "RegistryNumber", "ProcurementMethod", "PurchaseName",
                 "AuctionSubject", "PurchaseIdentificationCode", "LotNumber", "LotName",
                 "InitialMaxContractPrice", "Currency", "InitialMaxContractPriceInCurrency", 
                 "ContractCurrency", "OKDPClassification", "OKPDClassification",
                 "OKPD2Classification", "PositionCode", "CustomerName", "ProcurementOrganization",
                 "PlacementDate", "UpdateDate", "ProcurementStage", "ProcurementFeatures",
                "ApplicationStartDate", "ApplicationEndDate", "AuctionDate","QueryCount","ResponseCount",
                "AveragePrice","MinPrice","MaxPrice","StandardDeviation","CoefficientOfVariation","TKPData","NMCKMarket",
                "FinancingLimit", "InitialMaxContractPriceOld","notification_link","quantity_units",
                "nmck_per_unit",
                "TotalApplications", "AdmittedApplications", "RejectedApplications",
                "PriceProposal", "Applicant", "Applicant_satatus", "WinnerExecutor",
                "ContractingAuthority", "ContractIdentifier", "RegistryNumber_contract",
                "ContractNumber", "StartDate", "EndDate", "ContractPrice", "AdvancePayment",
                "ReductionNMC", "ReductionNMCPercent", "SupplierProtocol", "ContractFile",

                "RequestMethod","PublicInformationMethod","NMCObtainedMethods","CostMethodNMC",
                "ComparablePrice","NMCMethodsTwo","CEIComparablePrices","CEICostMethod","CEIMethodsTwo",
                
                "CurrencyValue","CurrentCurrency","DateValueChanged","CurrencyRateDate","PreviousCurrency", ]
        selected_data = [[t[selected_columns.index(col)] for col in selected_columns] for t in data]
        # print(selected_data[0])
        # Создайте DataFrame с данными
        data_df = pd.DataFrame(selected_data, columns=selected_columns)

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
        "InitialMaxContractPriceOld":"Прошлая цена",
        "TotalApplications": "Общее количество заявок",
        "AdmittedApplications": "Общее количество допущенных заявок",
        "RejectedApplications": "Общее количество отклоненных заявок",
        "PriceProposal": "Ценовое предложение",
        "Applicant": "Заявитель",
        "Applicant_satatus": "Статус заявителя",
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
        "RequestMethod":"Способ направления запросов о предоставлении ценовой информации",
        "PublicInformationMethod": "Способ использования общедоступной информации",
        "NMCObtainedMethods": "НМЦК, полученная различными способами", 
        "CostMethodNMC": "НМЦК на основе затратного метода, руб. (в случае его применения)",
        "ComparablePrice": "Цена сравнимой продукции",
        "NMCMethodsTwo": "НМЦК, полученная с применением двух методов",
        "CEIComparablePrices": "ЦКЕИ на основе метода сопоставимых рыночных цен",
        "CEICostMethod": "ЦКЕИ на основе затратного метода, руб. (в случае его применения)",
        "CEIMethodsTwo":"ЦКЕИ, полученная с применением двух методов",
        "CurrencyValue" :"Значение валюты",
        "CurrentCurrency" :"Текущая валюта",
        "DateValueChanged" :"Дата изменения значения валюты",
        "CurrencyRateDate" :"Дата курса валюты",
        "PreviousCurrency" :"Предыдущая валюта",
         "notification_link":"Извещение о закупке",
        "quantity_units":"Количество единиц",
        "nmck_per_unit":"НМЦК за единицу",

    }
        data_df.rename(columns=column_translation, inplace=True)
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            data_df.to_excel(writer, startrow=0, header=True, index=False)
        return True
    except Exception as e:
        print("Ошибка при экспорте данных в Excel:", e)


def find_records_with_differences():
    try:

        query = (Purchase
         .select(Purchase.Id, Purchase.RegistryNumber, Purchase.AuctionDate, 
                 Purchase.ApplicationEndDate, Purchase.ApplicationEndDate, 
                 Purchase.UpdateDate, Purchase.PlacementDate, Purchase.LotNumber)
         .where(Purchase.RegistryNumber.in_(
             Purchase
             .select(Purchase.RegistryNumber)
             .group_by(Purchase.RegistryNumber)
             .having(fn.COUNT(Purchase.Id) > 1)
         )))
        records_with_differences = [(
        purchase.Id, purchase.RegistryNumber, purchase.AuctionDate, purchase.ApplicationStartDate,
        purchase.ApplicationEndDate, purchase.UpdateDate, purchase.PlacementDate, purchase.LotNumber
            ) for purchase in query]

        query = (Purchase
        .select(fn.COUNT(Purchase.RegistryNumber))
        .group_by(Purchase.RegistryNumber)
        .having(fn.COUNT(Purchase.RegistryNumber) > 1))

        # Выполнение запроса и получение количества дубликатов
        count_of_duplicates = query.count()

        # Закрытие соединения
        # connection.close()

        return records_with_differences, count_of_duplicates

    except Exception as e:
        print("Ошибка при поиске записей с различиями:", e)
        return [], 0

def count_total_records():
    try:
        connection = connector()
        cursor = connection.cursor()

        count_of_records = Purchase.select().count()

    except sqlite3.Error as e:
        print("Ошибка при подсчете общего количества записей:", e)
    
    finally:
        connection.close()
    return count_of_records



# print(count_total_records())
def delete_records_by_id(record_ids, user,role):
    try:
        # Подключение к базе данных
        connection = connector()
         
        # SQL-запрос для удаления записей по Id
        query = Purchase.delete().where(Purchase.Id.in_(record_ids))
        for record_id in record_ids:
            purchase = Purchase.get(Purchase.Id == record_id)

            changed_date = ChangedDate(
                    RegistryNumber=purchase.RegistryNumber,
                    username=user,
                    chenged_time=datetime.now(),
                    PurchaseName=purchase.PurchaseName,
                    Role=role,
                    Type='Удалена запись'
                )
            changed_date.save()
            purchase.delete_instance(recursive=True)
        query.execute()

        # Закрытие соединения
        connection.close()

        return True

    except Exception as e:
        print("Ошибка при удалении записей по Id:", e)
        return False    

def clear_user_log():
    """Удаляет все записи из таблицы UserLog"""
    UserLog.delete().execute()

def clear_changed_date():
    """Удаляет все записи из таблицы ChangedDate"""
    ChangedDate.delete().execute() 
