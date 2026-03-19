
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
db = SqliteDatabase('database.db')



def connector():
    connection = sqlite3.connect('database.db')
    return connection
def insert_in_table(csv_file_path, user,role):
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
                max_length = 512  # Максимальная длина для строк
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

                auctionDate = row[24]
                try:
                    AuctionDate = datetime.strptime(auctionDate, '%d.%m.%Y').date()
                except ValueError:
                    AuctionDate = None
                # Вставка данных в таблицу
                inserted_rows += 1
                
                Purchase.create(
                PurchaseOrder=purchase_date, 
                RegistryNumber=registry_number, 
                ProcurementMethod=procurement_method, 
                PurchaseName=purchase_name,
                AuctionSubject=auction_subject, 
                PurchaseIdentificationCode=purchase_identification_code, 
                LotNumber=lot_number, 
                LotName=lot_name,
                InitialMaxContractPrice=initial_max_contract_price,
                Currency=Currency, 
                InitialMaxContractPriceInCurrency=InitialMaxContractPriceInCurrency, 
                ContractCurrency=ContractCurrency,
                OKDPClassification=OKDPClassification,
                OKPDClassification=OKPDClassification,
                OKPD2Classification=OKPD2Classification,
                PositionCode=PositionCode,
                CustomerName=CustomerName,
                ProcurementOrganization=ProcurementOrganization,
                PlacementDate=placementDate,
                UpdateDate=updateDate,
                ProcurementStage=ProcurementStage,
                ProcurementFeatures=ProcurementFeatures,
                ApplicationStartDate=applicationStartDate, 
                ApplicationEndDate=applicationEndDate,
                AuctionDate=AuctionDate
            )
            
            changed_date = ChangedDate(
                RegistryNumber=registry_number,
                username=user,
                chenged_time=datetime.now(),
                PurchaseName=purchase_name,
                Role=role,
                Type='Добавлены новая запись'
            )
            changed_date.save()
            
            
        
        
        connection.commit()
    
    
    except Exception as e:
        print("Ошибка подключения или вставки данных:", e)
        errors.append(str(e))  # Добавьте ошибку в список ошибок

    finally:
        connection.close()
    return inserted_rows, errors

def insert_in_table_full(csv_file_path):
    errors = []
    inserted_rows = 0 
    try:
        connection = connector()
        print("Успешное подключение к базе данных")
        cursor = connection.cursor()
        with open(csv_file_path, 'r', encoding='windows-1251') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter = ';')
            next(csv_reader)  # Пропустите заголовок, если он есть
            j = 1
            for row in csv_reader:
                
                # Обрезка слишком длинных строк
                max_length = 512 # Максимальная длина для строк
                purchase_date = row[2][:max_length] if row[0] else 'Нет данных'
                registry_number = row[0][:max_length] if row[1] else 'Нет данных'
                procurement_method = row[3][:max_length] if row[2] else 'Нет данных'
                purchase_name = row[4][:max_length] if row[3] else 'Нет данных'
                auction_subject = row[7][:max_length] if row[4] else 'Нет данных'
                purchase_identification_code = 'Нет данных'
                
                try:
                    lot_number = int(row[6])
                except ValueError:
                    lot_number = 0  # Если не удалось преобразовать в int, устанавливаем значение по умолчанию
                
                lot_name = row[7][:max_length] if row[7] else 'Нет данных'
                
                try:
                    initial_max_contract_price = float(row[8])
                except ValueError:
                    initial_max_contract_price = 0.0  # Если не удалось преобразовать в float, устанавливаем значение по умолчанию
                Currency = row[63] if row[63]  else 'Нет данных'
                try:
                    InitialMaxContractPriceInCurrency = float(row[10])
                except ValueError:
                    InitialMaxContractPriceInCurrency = 0
                ContractCurrency =   row[63] if row[63]  else 'Нет данных'
                OKDPClassification =  'Нет данных'
                OKPDClassification =  'Нет данных'
                OKPD2Classification = row[64] if row[64]  else 'Нет данных'
                PositionCode = 'Нет данных'
                CustomerName = row[5][:max_length] if row[5] else 'Нет данных'
                ProcurementOrganization = 'Нет данных'
                PlacementDate = row[1]
                try:
                    placementDate = datetime.strptime(PlacementDate, '%d.%m.%Y').date()
                except ValueError:
                    placementDate = 'Нет данных'
                UpdateDate = row[1]
                try:
                    updateDate = datetime.strptime(UpdateDate, '%d.%m.%Y').date()
                except ValueError:
                    updateDate ='Нет данных'
                ProcurementStage = 'Нет данных'
                ProcurementFeatures = 'Нет данных'
                ApplicationStartDate = row[10] 
                try:
                    applicationStartDate = datetime.strptime(ApplicationStartDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationStartDate =  'Нет данных'

                ApplicationEndDate = row[1]
                try:
                    applicationEndDate = datetime.strptime(ApplicationEndDate, '%d.%m.%Y').date()
                except ValueError:
                    applicationEndDate = 'Нет данных'

                auctionDate = row[1]
                try:
                    AuctionDate = datetime.strptime(auctionDate, '%d.%m.%Y').date()
                except ValueError:
                    AuctionDate = 'Нет данных'

                tkp_data_dict = {}
                for i in range(10):
                    column_name = f"ТКП №{1 + i}"
                    try:
                        tkp_value = int(row[13 + i])
                        tkp_data_dict[column_name] = tkp_value
                    except (ValueError, IndexError):
                        # Handle errors or missing values as needed
                        pass
                tkp_data_json = json.dumps(tkp_data_dict, ensure_ascii=False)
                try:
                    QueryCount = int(row[11]) if row[11] else 0
                except ValueError:
                    QueryCount = 0

                try:
                    ResponseCount = int(row[12]) if row[12] else 0
                except ValueError:
                    ResponseCount = 0

                try:
                    AveragePrice = float(row[23]) if row[23] else 0
                except ValueError:
                    AveragePrice = 0

                try:
                    MinPrice = float(row[24]) if row[24] else 0
                except ValueError:
                    MinPrice = 0

                try:
                    MaxPrice = float(row[25]) if row[25] else 0
                except ValueError:
                    MaxPrice = 0

                try:
                    StandardDeviation = float(row[26]) if row[26] else 0
                except ValueError:
                    StandardDeviation = 0

                try:
                    CoefficientOfVariation = float(row[27]) if row[27] else 0
                except ValueError:
                    CoefficientOfVariation = 0

                try:
                    NMCKMarket = float(row[29]) if row[29] else 0
                except ValueError:
                    NMCKMarket = 0

                try:
                    FinancingLimit = float(row[30]) if row[30] else 0
                except ValueError:
                    FinancingLimit = 0
                PurchaseStatus = row[31][:max_length] if row[31] else 'Нет данных'
                ############## CONTRACTS###############
                TotalApplications = row[32] if row[32] else 0
                AdmittedApplications = row[33] if row[33] else 0
                RejectedApplications = row[34] if row[34] else 0
               
                

                price_proposal_dict = {}
                applicant_dict = {}
                applicant_status_dict = {}
                k = 1
                for i in range(0,17,3):  # Assuming there are 6 sets of columns for each field
                    price_proposal_key = f"Ценовое предложение №{k}"
                    applicant_key = f"Заявитель №{k}"
                    applicant_status_key = f"Статус заявителя №{k}"

                    try:
                        price_proposal_value = row[35 + i]
                        price_proposal_dict[price_proposal_key] = price_proposal_value
                    except (ValueError, IndexError):
                        pass

                    try:
                        applicant_value = row[36 + i]  # Adjust the index based on your CSV structure
                        applicant_dict[applicant_key] = applicant_value
                    except (IndexError):
                        pass

                    try:
                        applicant_status_value = row[37 + i]  # Adjust the index based on your CSV structure
                        applicant_status_dict[applicant_status_key] = applicant_status_value
                    except (IndexError):
                        pass
                    k = k + 1
                price_proposal_json = json.dumps(price_proposal_dict, ensure_ascii=False)
                applicant_json = json.dumps(applicant_dict, ensure_ascii=False)
                applicant_status_json = json.dumps(applicant_status_dict, ensure_ascii=False)
                purchase_id = j
                j = j + 1
                ContractingAuthority = row[53] if row[53] else 0
                WinnerExecutor = row[54] if row[54] else 0
                ContractIdentifier = row[55] if row[55] else 0
                RegistryNumber = row[56] if row[56] else 0
                ContractNumber = row[57] if row[57] else 0
                ContractPrice = float(row[58]) if row[58] else 0
                quantity_units = int(row[6]) if row[6] else 0
                nmck_per_unit = float(row[9]) if row[9] else 0
                notification_link =  "Нет данных"
                

                StartDate = row[59]
                try:
                    startDate = datetime.strptime(StartDate, '%d.%m.%Y').date()
                except ValueError:
                    startDate = 'Нет данных'

                EndDate = row[60]
                try:
                    endDate = datetime.strptime(EndDate, '%d.%m.%Y').date()
                except ValueError:
                    endDate = 'Нет данных'
                try:
                    AdvancePayment = float(row[61]) if row[61] else 0
                except ValueError:
                    AdvancePayment = 0

                try:
                    ReductionNMCPercent = float(row[62]) if row[62] else 0
                except ValueError:
                    ReductionNMCPercent = 0

                try:
                    ReductionNMC = float(row[68]) if row[68] else 0
                except ValueError:
                    ReductionNMC = 0
                ContractFile = 'Нет данных'
                SupplierProtocol = 'Нет данных'

                
                    
                Purchase.create(
                PurchaseOrder=purchase_date, 
                RegistryNumber=registry_number, 
                ProcurementMethod=procurement_method, 
                PurchaseName=purchase_name,
                AuctionSubject=auction_subject, 
                PurchaseIdentificationCode=purchase_identification_code, 
                LotNumber=lot_number, 
                LotName=lot_name,
                InitialMaxContractPrice=initial_max_contract_price,
                Currency=Currency, 
                InitialMaxContractPriceInCurrency=InitialMaxContractPriceInCurrency, 
                ContractCurrency=ContractCurrency,
                OKDPClassification=OKDPClassification,
                OKPDClassification=OKPDClassification,
                OKPD2Classification=OKPD2Classification,
                PositionCode=PositionCode,
                CustomerName=CustomerName,
                ProcurementOrganization=ProcurementOrganization,
                PlacementDate=placementDate,
                UpdateDate=updateDate,
                ProcurementStage=ProcurementStage,
                ProcurementFeatures=ProcurementFeatures,
                ApplicationStartDate=applicationStartDate, 
                ApplicationEndDate=applicationEndDate,
                AuctionDate=AuctionDate,
                TKPData=tkp_data_json,
                QueryCount=QueryCount,
                ResponseCount=ResponseCount,
                AveragePrice=AveragePrice,
                MinPrice=MinPrice,
                MaxPrice=MaxPrice,
                StandardDeviation=StandardDeviation,
                CoefficientOfVariation=CoefficientOfVariation,
                NMCKMarket=NMCKMarket,
                FinancingLimit=FinancingLimit,
                PurchaseStatus=PurchaseStatus,
                quantity_units=quantity_units,
                nmck_per_unit=nmck_per_unit,
                notification_link=notification_link
            )


                
                Contract.create(
                TotalApplications=TotalApplications,
                AdmittedApplications=AdmittedApplications,
                RejectedApplications=RejectedApplications,
                PriceProposal=price_proposal_json,
                Applicant=applicant_json,
                Applicant_satatus=applicant_status_json,
                purchase_id=purchase_id,
                ContractingAuthority=ContractingAuthority,
                WinnerExecutor=WinnerExecutor,
                ContractIdentifier=ContractIdentifier,
                RegistryNumber=RegistryNumber,
                ContractNumber=ContractNumber,
                ContractPrice=ContractPrice,
                StartDate=startDate,
                EndDate=endDate,
                AdvancePayment=AdvancePayment,
                ReductionNMCPercent=ReductionNMCPercent,
                ReductionNMC=ReductionNMC,
                ContractFile=ContractFile,
                SupplierProtocol=SupplierProtocol
            )

                inserted_rows += cursor.rowcount

        connection.commit()
    
    
    except Exception as e:
        print("Ошибка подключения или вставки данных:", e)
        errors.append(str(e))  # Добавьте ошибку в список ошибок

    finally:
        connection.close()
    return inserted_rows, errors


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
        # Создайте DataFrame из данных
        filter_df = pd.DataFrame([filters],columns=[
    "filter_criteria",  "start_date", "end_date", "min_price", "max_price"
])
        
        filter_column_translation = {
    "filter_criteria": "Критерии Фильтра",
    "start_date": "Дата Начала",
    "end_date": "Дата Окончания",
    "min_price": "Минимальная Цена",
    "max_price": "Максимальная Цена"
}
        # Замените пустые значения фильтров на пустые строки для правильного отображения в Excel
        filter_df.fillna('', inplace=True)
        # selected_data = [tuple[:69] for tuple in data]
       
        selected_columns = [ "Purchase.Id",
"Contract.RegistryNumber",
"Purchase.RegistryNumber",
"Contract.ContractNumber",
"Contract.StartDate",
"Contract.ContractPrice",
"Contract.ContractingAuthority",
"Contract.WinnerExecutor",
"Purchase.PurchaseName",
"Contract.TotalApplications",
"Contract.AdmittedApplications",
"Contract.RejectedApplications",
"Contract.PriceProposal",
"Contract.Applicant",
"Contract.Applicant_satatus",
"Contract.ContractIdentifier",
"Contract.EndDate",
"Contract.AdvancePayment",
"Contract.ReductionNMC",
"Contract.ReductionNMCPercent",
"Contract.SupplierProtocol",
"Contract.ContractFile"]
        selected_data = [[t[selected_columns.index(col)] for col in selected_columns] for t in data]
        # print(selected_data[0])
        # Создайте DataFrame с данными
        data_df = pd.DataFrame(selected_data, columns=selected_columns)

        # Создайте словарь для перевода названий столбцов
        column_translation = {
            "Purchase.Id":"Номер",
"Contract.RegistryNumber": "Реестровый Номер",
"Purchase.RegistryNumber": "Реестровый Номер закупки",
"Contract.ContractNumber": "№ договора",
"Contract.StartDate": "Дата начала/подписания",
"Contract.ContractPrice": "Цена договора, руб.",
"Contract.ContractingAuthority": "Заказчик по контракту",
"Contract.WinnerExecutor": "Победитель-исполнитель контракта",
"Purchase.PurchaseName": "Название Закупки",
"Contract.TotalApplications": "Общее количество заявок",
"Contract.AdmittedApplications": "Общее количество допущенных заявок",
"Contract.RejectedApplications": "Общее количество отклоненных заявок",
"Contract.PriceProposal": "Ценовое предложение",
"Contract.Applicant": "Заявитель",
"Contract.Applicant_satatus": "Статус заявителя",
"Contract.ContractIdentifier": "Идентификатор договора",
"Contract.EndDate": "Дата окончания/исполнения",
"Contract.AdvancePayment": "Размер авансирования, руб./(%)",
"Contract.ReductionNMC": "Снижение НМЦК, руб.",
"Contract.ReductionNMCPercent": "Снижение НМЦК, %",
"Contract.SupplierProtocol": "Протоколы определения поставщика (выписка)",
"Contract.ContractFile": "Договор"

    }

        filter_df.rename(columns=filter_column_translation, inplace=True)

        data_df.rename(columns=column_translation, inplace=True)
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            filter_df.to_excel(writer, index=False)
            data_df.to_excel(writer, startrow=2, header=True, index=False)
        return True
    except Exception as e:
        print("Ошибка при экспорте данных в Excel:", e)


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
