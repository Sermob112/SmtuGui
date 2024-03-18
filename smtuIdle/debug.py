from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QStringListModel,Signal
from PySide6.QtGui import *
from peewee import *
import pandas as pd
from models import *
import json
from functools import partial
system_db = PostgresqlDatabase('testGui', user='postgres', password='sa', host='localhost', port=5432)
system_db.create_tables([Purchase, User, Role, UserRole, Contract,FinalDetermination,CurrencyRate,UserLog,ChangedDate ])
system_db.close()
        #Статистический анализ методов, использованных для определения НМЦК и ЦКЕП
# contracts =  (
#     Contract.select(
#         Purchase.Id,
#         Contract.RegistryNumber,
#         Purchase.RegistryNumber,
#         Contract.ContractNumber,
#         Contract.StartDate,
#         Contract.ContractPrice,
#         Contract.ContractingAuthority,
#         Contract.WinnerExecutor,
#         Purchase.PurchaseName,
#         Contract.TotalApplications,
#         Contract.AdmittedApplications,
#         Contract.RejectedApplications,
#         Contract.PriceProposal,
#         Contract.Applicant,
#         Contract.Applicant_satatus,
#         Contract.ContractIdentifier,
#         Contract.EndDate,
#         Contract.AdvancePayment,
#         Contract.ReductionNMC,
#         Contract.ReductionNMCPercent,
#         Contract.SupplierProtocol,
#         Contract.ContractFile
#     )
#     .join(Purchase, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
#     .where(Contract.ContractNumber != "Нет данных"))

    
# df = pd.DataFrame([(contract.WinnerExecutor, 1) for contract in contracts], columns=['WinnerExecutor', 'Count'])

# # Создаем сводную таблицу по победителям
# pivot_table = df.pivot_table(index='WinnerExecutor', aggfunc='size', fill_value=0)

# pivot_table.columns = ['Победитель-исполнитель контракта', 'Единицы']

# column_sums = pivot_table.sum()
# total_purchase_counts = column_sums.sum()
# # row_totals = pivot_table.sum(axis=1)
# # pivot_table['Общий итог'] = row_totals
# total_counts = pd.DataFrame({'Суммы': [total_purchase_counts]})
# total_counts.index = ['Итого']

# # row_totals = pivot_table.sum(axis=1)
# # pivot_table['Общий итог'] = row_totals
# # total_purchase_counts = column_sums.sum()
# # column_sums['Суммы'] = total_purchase_counts
# print(pivot_table)
# print(total_counts)