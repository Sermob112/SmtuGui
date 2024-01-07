from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField, ForeignKeyField, ManyToManyField
from datetime import date
from random import randint, uniform
import sqlite3
import json
db = SqliteDatabase('test.db')

class BaseModel(Model):
    class Meta:
        database = db

class Purchase(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")
    PurchaseOrder = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Закон")
    RegistryNumber = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Реестровый номер")
    ProcurementMethod = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Метод закупки")
    PurchaseName = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Наименование закупки")
    AuctionSubject = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Предмет аукциона")
    PurchaseIdentificationCode = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Код идентификации закупки")
    LotNumber = IntegerField(null=True, default="Нет данных", verbose_name="Номер лота")
    LotName = CharField(null=True, max_length=255,  default="Нет данных", verbose_name="Наименование лота")
    InitialMaxContractPrice = FloatField(null=True,  default="Нет данных", verbose_name="Начальная максимальная цена контракта")
    Currency = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Валюта")
    InitialMaxContractPriceInCurrency = FloatField(null=True,  default="Нет данных", verbose_name="Начальная максимальная цена контракта в валюте")
    ContractCurrency = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Валюта контракта")
    OKDPClassification = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Классификация ОКДП")
    OKPDClassification = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Классификация ОКПД")
    OKPD2Classification = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Классификация ОКПД2")
    PositionCode = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Код позиции")
    CustomerName = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Наименование заказчика")
    ProcurementOrganization = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Организация закупки")
    PlacementDate = DateField(null=True,  default="Нет данных", verbose_name="Дата размещения")
    UpdateDate = DateField(null=True,  default="Нет данных", verbose_name="Дата обновления")
    ProcurementStage = CharField(null=True,  max_length=255, default="Нет данных", verbose_name="Этап закупки")
    ProcurementFeatures = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Особенности закупки")
    ApplicationStartDate = DateField(null=True, default="Нет данных", verbose_name="Дата начала заявки")
    ApplicationEndDate = DateField(null=True,  default="Нет данных", verbose_name="Дата окончания заявки")
    AuctionDate = DateField(null=True,  default="Нет данных", verbose_name="Дата аукциона")
    # Добавленные поля
    TKPData = CharField(null=True, max_length=500, default="[]", verbose_name="Данные по ТКП")
    QueryCount = IntegerField(null=True,  default="Нет данных", verbose_name="Количество запросов")
    ResponseCount = IntegerField(null=True,  default="Нет данных", verbose_name="Количество ответов") 
    AveragePrice = FloatField(null=True,  default="Нет данных", verbose_name="Среднее значение цены")
    MinPrice = FloatField(null=True,  default="Нет данных", verbose_name="Минимальная цена")
    MaxPrice = FloatField(null=True,  default="Нет данных", verbose_name="Максимальная цена")
    StandardDeviation = FloatField(null=True,  default="Нет данных", verbose_name="Среднее квадратичное отклонение")
    CoefficientOfVariation = FloatField(null=True,  default="Нет данных", verbose_name="Коэффициент вариации")
    NMCKMarket = FloatField(null=True,  default="Нет данных", verbose_name="НМЦК рыночная")
    FinancingLimit = FloatField(null=True, default="Нет данных", verbose_name="Лимит финансирования")
    def delete_instance(self, *args, **kwargs):
        # Добавьте каскадное удаление перед вызовом delete_instance
        Contract.delete().where(Contract.purchase == self).execute()
        super(Purchase, self).delete_instance(*args, **kwargs)


class Contract(Model):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")
    TotalApplications = IntegerField(verbose_name="Общее количество заявок", null=True)
    AdmittedApplications = IntegerField(verbose_name="Общее количество допущенных заявок", null=True)
    RejectedApplications = IntegerField(verbose_name="Общее количество отклоненных заявок", null=True)
    PriceProposal = CharField(null=True, max_length=500, default="[]", verbose_name="Ценовое предложение")
    Applicant = CharField(null=True, max_length=500, default="[]", verbose_name="Заявитель")
    Applicant_satatus = CharField(null=True, max_length=500, default="[]", verbose_name="Статус заявителя")
    WinnerExecutor = CharField(verbose_name="Победитель-исполнитель контракта", max_length=255, null=True)
    ContractingAuthority = CharField(verbose_name="Заказчик по контракту", max_length=255, null=True)
    ContractIdentifier = CharField(verbose_name="Идентификатор договора", max_length=255, null=True)
    RegistryNumber = CharField(verbose_name="Реестровый номер договора", max_length=255, null=True)
    ContractNumber = CharField(verbose_name="№ договора", max_length=255, null=True)
    StartDate = DateField(verbose_name="Дата начала/подписания", null=True)
    EndDate = DateField(verbose_name="Дата окончания/исполнения", null=True)
    ContractPrice = IntegerField(verbose_name="Цена договора, руб.", null=True)
    AdvancePayment = FloatField(verbose_name="Размер авансирования, руб./(%)", null=True)
    ReductionNMC = IntegerField(verbose_name="Снижение НМЦК, руб.", null=True)
    ReductionNMCPercent = FloatField(verbose_name="Снижение НМЦК, %", null=True)
    SupplierProtocol = CharField(verbose_name="Протоколы определения поставщика (выписка)", max_length=255, null=True)
    ContractFile = CharField(verbose_name="Договор", max_length=255, null=True)
    purchase = ForeignKeyField(Purchase,on_delete='CASCADE',  backref='contract', unique=True, verbose_name="Закупка")
    # purchase = ForeignKeyField(Purchase,on_delete='CASCADE', verbose_name="Закупка")
    class Meta:
        database = db  

class User(Model):
    id = AutoField(primary_key=True, verbose_name="Идентификатор")
    username = CharField(max_length=100, unique=True)
    password = CharField(max_length=100)

    class Meta:
        database = db

    def __str__(self):
        return self.username
    
class Role(BaseModel):
    id = AutoField(primary_key=True, verbose_name="Идентификатор")
    name = CharField(max_length=100)

    class Meta:
        database = db

    def __str__(self):
        return self.name


class UserRole(Model):
    user = ForeignKeyField(User, backref='roles')
    role = ForeignKeyField(Role, backref='users')

    class Meta:
        database = db


# db.connect()
# db.create_tables([Purchase])
# db.create_tables([Contract])
# tkp_data = [
#     {"ТКП1": 12000},
#     {"ТКП2": 13000},
#     {"ТКП3": 15000}
# ]
# tkp_data_json = json.dumps(tkp_data)
# purchase = Purchase(TKPData=tkp_data_json)
# purchase.save()
# def add_test_data():
#     for _ in range(10):  # Change this number as needed
#         Purchase.create(
#             PurchaseOrder=f"Order {_}",
#             RegistryNumber=f"Registry {_}",
#             ProcurementMethod=f"Method {_}",
#             PurchaseName=f"Purchase {_}",
#             AuctionSubject=f"Subject {_}",
#             PurchaseIdentificationCode=f"Code {_}",
#             LotNumber=randint(1, 10),
#             LotName=f"Lot {_}",
#             InitialMaxContractPrice=uniform(1000, 10000),
#             Currency="USD",
#             InitialMaxContractPriceInCurrency=uniform(1000, 10000),
#             ContractCurrency="USD",
#             OKDPClassification=f"OKDP {_}",
#             OKPDClassification=f"OKPD {_}",
#             OKPD2Classification=f"OKPD2 {_}",
#             PositionCode=f"Position {_}",
#             CustomerName=f"Customer {_}",
#             ProcurementOrganization=f"Organization {_}",
#             PlacementDate=date.today(),
#             UpdateDate=date.today(),
#             ProcurementStage=f"Stage {_}",
#             ProcurementFeatures=f"Features {_}",
#             ApplicationStartDate=date.today(),
#             ApplicationEndDate=date.today(),
#             AuctionDate=date.today(),
#             QueryCount=randint(1, 10),
#             ResponseCount=randint(1, 10),
#             AveragePrice=uniform(1000, 10000),
#             MinPrice=uniform(1000, 10000),
#             MaxPrice=uniform(1000, 10000),
#             StandardDeviation=uniform(1, 10),
#             CoefficientOfVariation=uniform(0.1, 1),
#             NMCKMarket=uniform(1000, 10000),
#             FinancingLimit=uniform(1000, 10000)
#         )

# Call the function to add test data
# add_test_data()

# Close the database connection
# db.close()