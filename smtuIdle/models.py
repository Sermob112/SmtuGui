from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField, ForeignKeyField, ManyToManyField

import sqlite3
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
    QueryCount = IntegerField(null=True,  default="Нет данных", verbose_name="Количество запросов")
    ResponseCount = IntegerField(null=True,  default="Нет данных", verbose_name="Количество ответов") 

    AveragePrice = FloatField(null=True,  default="Нет данных", verbose_name="Среднее значение цены")
    MinPrice = FloatField(null=True,  default="Нет данных", verbose_name="Минимальная цена")
    MaxPrice = FloatField(null=True,  default="Нет данных", verbose_name="Максимальная цена")
    StandardDeviation = FloatField(null=True,  default="Нет данных", verbose_name="Среднее квадратичное отклонение")
    CoefficientOfVariation = FloatField(null=True,  default="Нет данных", verbose_name="Коэффициент вариации")
    NMCKMarket = FloatField(null=True,  default="Нет данных", verbose_name="НМЦК рыночная")
    FinancingLimit = FloatField(null=True, default="Нет данных", verbose_name="Лимит финансирования")







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


