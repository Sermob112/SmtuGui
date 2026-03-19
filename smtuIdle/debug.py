import pandas as pd
from smtuIdle.BD.models import *

# def count_non_empty_values(dictionary):
#         count = 0
#         for key, value in dictionary.items():
#             if value != "Нет данных" :
#                 count += 1
#         return count
# coeff_range_order = [
#         'Ценовое предложение №1',
#         'Ценовое предложение №2',
#         'Ценовое предложение №3',
#         'Ценовое предложение №4',
#         'Ценовое предложение №5',
#         'Ценовое предложение №6',
# ]
# new_column_names = [
#     'Одно',
#     'Два',
#     'Три',
#     'Четыре',
#     'Пять',
#     'Более пяти'
# ]
# query = Purchase.select(Purchase.PurchaseOrder, Contract.PriceProposal).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase)).where(Contract.PriceProposal.is_null(False))
# data = list(query)
# df_data = []

# for purchase in data:
#     price_proposal_dict = json.loads(purchase.contract.PriceProposal)
  
#     row_data = [purchase.PurchaseOrder]
#     for key in coeff_range_order:
#         value = price_proposal_dict.get(key, "")
#         row_data.append(count_non_empty_values({key: value}))

#     # Переместите эту строку внутрь цикла for
#     df_data.append(row_data)  # Эта строка должна быть внутри цикла

# df_columns = ['PurchaseOrder'] + coeff_range_order
# df = pd.DataFrame(df_data, columns=df_columns)
# df.rename(columns=dict(zip(coeff_range_order, new_column_names)), inplace=True)

# # Создание сводной таблицы
# pivot_table = df.pivot_table(index='PurchaseOrder', aggfunc='sum', fill_value=0)
# # Суммы по строкам и столбцам

# transposed_table = pivot_table.T
# row_totals = transposed_table.sum(axis=1)
# transposed_table['Общий итог'] = row_totals
# column_sums = transposed_table.sum()
# total_counts = column_sums.sum()
# column_sums['Суммы'] = total_counts
# transposed_table = transposed_table.reindex(new_column_names, axis=0)
# print(transposed_table)



    # Статистический анализ количества записей по дате размещения
purchases = Purchase.select()
# Создаем DataFrame с полями PlacementDate и PurchaseOrder
df = pd.DataFrame([(purchase.PlacementDate, purchase.PurchaseOrder) for purchase in purchases], columns=['PlacementDate', 'PurchaseOrder'])

# Преобразуем PlacementDate в datetime, если это необходимо
df['PlacementDate'] = pd.to_datetime(df['PlacementDate'])

# Группируем по PlacementDate и считаем количество записей для каждой даты
grouped_df = df.groupby(df['PlacementDate'].dt.year).size().reset_index(name='Количество записей')

grouped_df.columns = ['PlacementDate', 'Количество записей']
grouped_df.set_index('PlacementDate', inplace=True)

print(grouped_df)
