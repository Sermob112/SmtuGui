from peewee import *
from datetime import date, datetime
import json
db = SqliteDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = db


# ─────────────────────────────────────────────
#  Purchase  —  Основная таблица закупок
# ─────────────────────────────────────────────
class Purchase(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")

    # ── Идентификация закупки ──────────────────
    PurchaseOrder              = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Закон")
    RegistryNumber             = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Реестровый номер")
    ProcurementMethod          = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Метод закупки")
    PurchaseName               = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Наименование закупки")
    AuctionSubject             = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Предмет аукциона")
    PurchaseIdentificationCode = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Код идентификации закупки")
    ProcurementOrganization    = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Организация закупки")
    ProcurementStage           = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Этап закупки")
    ProcurementFeatures        = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Особенности закупки")
    PurchaseStatus             = CharField(null=True, max_length=500, default="[]",         verbose_name="Статус закупки")
    notification_link          = CharField(null=True, max_length=512,                       verbose_name="Извещение о закупке")

    # ── Лот ───────────────────────────────────
    LotNumber = IntegerField(null=True, verbose_name="Номер лота")
    LotName   = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Наименование лота")

    # ── Ценовая информация ─────────────────────
    InitialMaxContractPrice           = FloatField(null=True, verbose_name="Начальная максимальная цена контракта")
    Currency                          = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Валюта")
    InitialMaxContractPriceInCurrency = FloatField(null=True, verbose_name="Начальная максимальная цена контракта в валюте")
    ContractCurrency                  = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Валюта контракта")
    InitialMaxContractPriceOld        = FloatField(null=True, verbose_name="Начальная максимальная цена контракта старая")
    FinancingLimit                    = FloatField(null=True, verbose_name="Лимит финансирования")

    # ── Классификаторы ────────────────────────
    OKDPClassification  = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Классификация ОКДП")
    OKPDClassification  = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Классификация ОКПД")
    OKPD2Classification = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Классификация ОКПД2")
    PositionCode        = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Код позиции")

    # ── Заказчик ──────────────────────────────
    CustomerName = CharField(null=True, max_length=512, default="Нет данных", verbose_name="Наименование заказчика")

    # ── Даты ──────────────────────────────────
    PlacementDate        = DateField(null=True, verbose_name="Дата размещения")
    UpdateDate           = DateField(null=True, verbose_name="Дата обновления")
    ApplicationStartDate = DateField(null=True, verbose_name="Дата начала заявки")
    ApplicationEndDate   = DateField(null=True, verbose_name="Дата окончания заявки")
    AuctionDate          = DateField(null=True, verbose_name="Дата аукциона")

    # ── Единицы и файлы ───────────────────────
    quantity_units = IntegerField(null=True, verbose_name="Количество единиц")
    nmck_per_unit  = FloatField(null=True,   verbose_name="НМЦК за единицу")
    nmck_file      = CharField(null=True, max_length=512, verbose_name="Файл НМЦК")
    protocol_file  = CharField(null=True, max_length=512, verbose_name="Файл Протокола")

    # ── ТКП / Статистика ──────────────────────
    TKPData                = CharField(null=True, max_length=500, default="[]", verbose_name="Данные по ТКП")
    QueryCount             = IntegerField(null=True, verbose_name="Количество запросов")
    ResponseCount          = IntegerField(null=True, verbose_name="Количество ответов")
    AveragePrice           = FloatField(null=True,   verbose_name="Среднее значение цены")
    MinPrice               = FloatField(null=True,   verbose_name="Минимальная цена")
    MaxPrice               = FloatField(null=True,   verbose_name="Максимальная цена")
    StandardDeviation      = FloatField(null=True,   verbose_name="Среднее квадратичное отклонение")
    CoefficientOfVariation = FloatField(null=True,   verbose_name="Коэффициент вариации")
    NMCKMarket             = FloatField(null=True,   verbose_name="НМЦК рыночная")

    # ── Мета определения НМЦК ─────────────────
    NMCK_1          = CharField(null=True, max_length=500, default="[]", verbose_name="Цена судна приведенная к уровню цен года его поставки")
    ContractCount   = IntegerField(null=True, verbose_name="Количество контрактов")
    NMCK_2          = CharField(null=True, max_length=500, default="[]", verbose_name="Цена судна приведенная к уровню цен первого года периода строительства судна")
    NMCK_3          = CharField(null=True, max_length=500, default="[]", verbose_name="Цена судна приведенная к уровню цен текущих лет на периода строительства судна")
    NMC_determ      = FloatField(null=True, verbose_name="Определение НМЦК")
    NMC_coef_determ = FloatField(null=True, verbose_name="Определение коэффициента НМЦК")

    # ── Организация расчёта ───────────────────
    organization_name      = CharField(null=True, max_length=255, verbose_name="Наименование организации")
    organization_price     = CharField(null=True, max_length=255, verbose_name="Цена")
    organization_name_date = CharField(null=True, max_length=255, verbose_name="Дата расчета")
    organization_name_file = CharField(null=True, max_length=255, verbose_name="Файл расчета")

    # ── Методы определения НМЦК ───────────────
    method_direction_requests = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Способ направления запросов о предоставлении ценовой информации потенциальным исполнителям")
    method_usage_information  = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Способ использования общедоступной информации при осуществлении поиска ценовой информации в реестре государственных контрактов")
    nmc_various_methods       = CharField(null=True, max_length=255, default="Нет данных", verbose_name="НМЦК, полученный различными способами в рамках метода сопоставимых рыночных цен")
    nmc_cost_method           = CharField(null=True, max_length=255, default="Нет данных", verbose_name="НМЦК на основе затратного метода")
    comparable_product_price  = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Цена сравнимой продукции, приведенная в соответствие к условиям закупки судна, НМЦК которого определяется")
    nmc_two_methods           = CharField(null=True, max_length=255, default="Нет данных", verbose_name="НМЦК, полученная с применением двух методов: метода сопоставимых рыночных цен и затратного метода")
    file_4                    = CharField(null=True, max_length=255, default="Нет данных", verbose_name="Файл НМЦК, полученный с применением двух методов")
    # ── JSON-поля (хранятся как TEXT) ─────────
    common_info_json      = TextField(null=True, verbose_name="Общая информация")
    documents_json        = TextField(null=True, verbose_name="Документы")
    event_log_json        = TextField(null=True, verbose_name="Журнал событий")
    supplier_result_json  = TextField(null=True, verbose_name="Результаты поставщика")
    lots_json             = TextField(null=True, verbose_name="Список лотов")
    protocols_json        = TextField(null=True, verbose_name="Протоколы")
    contracts_info_json   = TextField(null=True, verbose_name="Сведения о договорах")
    changes_json          = TextField(null=True, verbose_name="Изменения")

    # ── Служебное ─────────────────────────────
    isChanged = BooleanField(null=True, verbose_name="Был изменен")

    def delete_instance(self, *args, **kwargs):
        Contract.delete().where(Contract.purchase == self).execute()
        super(Purchase, self).delete_instance(*args, **kwargs)

    class Meta:
        table_name = 'purchase'


# ─────────────────────────────────────────────
#  Contract  —  Контракты по закупкам
# ─────────────────────────────────────────────
class Contract(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")

    TotalApplications    = CharField(null=True, verbose_name="Общее количество заявок")
    AdmittedApplications = CharField(null=True, verbose_name="Общее количество допущенных заявок")
    RejectedApplications = CharField(null=True, verbose_name="Общее количество отклоненных заявок")
    PriceProposal        = CharField(null=True, max_length=500, default="[]", verbose_name="Ценовое предложение")
    Applicant            = CharField(null=True, max_length=500, default="[]", verbose_name="Заявитель")
    Applicant_satatus    = CharField(null=True, max_length=500, default="[]", verbose_name="Статус заявителя")
    WinnerExecutor       = CharField(null=True, max_length=255, verbose_name="Победитель-исполнитель контракта")
    ContractingAuthority = CharField(null=True, max_length=255, verbose_name="Заказчик по контракту")
    ContractIdentifier   = CharField(null=True, max_length=255, verbose_name="Идентификатор договора")
    RegistryNumber       = CharField(null=True, max_length=255, verbose_name="Реестровый номер договора")
    ContractNumber       = CharField(null=True, max_length=255, verbose_name="№ договора")
    StartDate            = DateField(null=True,  verbose_name="Дата начала/подписания")
    EndDate              = DateField(null=True,  verbose_name="Дата окончания/исполнения")
    ContractPrice        = FloatField(null=True, verbose_name="Цена договора, руб.")
    AdvancePayment       = FloatField(null=True, verbose_name="Размер авансирования, руб./(%)")
    ReductionNMC         = FloatField(null=True, verbose_name="Снижение НМЦК, руб.")
    ReductionNMCPercent  = FloatField(null=True, verbose_name="Снижение НМЦК, %")
    SupplierProtocol     = CharField(null=True, max_length=255, verbose_name="Протоколы определения поставщика (выписка)")
    ContractFile         = CharField(null=True, max_length=255, verbose_name="Договор")
    purchase             = ForeignKeyField(Purchase, on_delete='CASCADE', backref='contracts', unique=True, verbose_name="Закупка")
    # ── JSON-поля (хранятся как TEXT) ─────────
    common_info_json        = TextField(null=True, verbose_name="Общая информация")
    payment_targets_json    = TextField(null=True, verbose_name="Платежи и объекты закупки")
    process_info_json       = TextField(null=True, verbose_name="Исполнение (расторжение) контракта")
    documents_json          = TextField(null=True, verbose_name="Вложения")
    journal_versions_json   = TextField(null=True, verbose_name="Журнал версий")
    event_log_json          = TextField(null=True, verbose_name="Журнал событий")

    class Meta:
        table_name = 'contract'


# ─────────────────────────────────────────────
#  FinalDetermination  —  Определение НМЦК
# ─────────────────────────────────────────────
class FinalDetermination(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")

    RequestMethod           = CharField(null=True, verbose_name="Способ направления запросов о предоставлении ценовой информации")
    PublicInformationMethod = CharField(null=True, verbose_name="Способ использования общедоступной информации")
    NMCObtainedMethods      = CharField(null=True, verbose_name="НМЦК, полученная различными способами")
    CostMethodNMC           = CharField(null=True, verbose_name="НМЦК на основе затратного метода, руб.")
    ComparablePrice         = CharField(null=True, verbose_name="Цена сравнимой продукции")
    NMCMethodsTwo           = CharField(null=True, verbose_name="НМЦК, полученная с применением двух методов")
    CEIComparablePrices     = CharField(null=True, verbose_name="ЦКЕИ на основе метода сопоставимых рыночных цен")
    CEICostMethod           = CharField(null=True, verbose_name="ЦКЕИ на основе затратного метода, руб.")
    CEIMethodsTwo           = CharField(null=True, verbose_name="ЦКЕИ, полученная с применением двух методов")
    purchase                = ForeignKeyField(Purchase, on_delete='CASCADE', backref='final_determinations', unique=True, verbose_name="Закупка")

    class Meta:
        table_name = 'finaldetermination'


# ─────────────────────────────────────────────
#  CurrencyRate  —  Курсы валют
# ─────────────────────────────────────────────
class CurrencyRate(BaseModel):
    Id = AutoField(primary_key=True, verbose_name="Идентификатор")

    CurrencyValue    = FloatField(verbose_name="Значение валюты")
    CurrentCurrency  = CharField(max_length=255, verbose_name="Текущая валюта")
    DateValueChanged = DateField(verbose_name="Дата изменения значения валюты")
    CurrencyRateDate = DateField(verbose_name="Дата курса валюты")
    PreviousCurrency = CharField(max_length=255, verbose_name="Предыдущая валюта")
    purchase         = ForeignKeyField(Purchase, on_delete='CASCADE', backref='currency_rates', unique=True, verbose_name="Закупка")
    isChanged        = BooleanField(null=True, verbose_name="Был изменен")

    class Meta:
        table_name = 'currencyrate'


# ─────────────────────────────────────────────
#  User / Role / UserRole  —  Пользователи
# ─────────────────────────────────────────────
class User(BaseModel):
    id       = AutoField(primary_key=True, verbose_name="Идентификатор")
    username = CharField(max_length=100)
    password = CharField(max_length=100)

    def __str__(self):
        return self.username

    class Meta:
        table_name = 'user'


class Role(BaseModel):
    id   = AutoField(primary_key=True, verbose_name="Идентификатор")
    name = CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        table_name = 'role'


class UserRole(BaseModel):
    id   = AutoField(primary_key=True, verbose_name="Идентификатор")
    user = ForeignKeyField(User, backref='roles', on_delete='CASCADE')
    role = ForeignKeyField(Role, backref='users', on_delete='CASCADE')

    class Meta:
        table_name = 'userrole'


# ─────────────────────────────────────────────
#  UserLog  —  Журнал входов пользователей
# ─────────────────────────────────────────────
class UserLog(BaseModel):
    Id          = AutoField(primary_key=True, verbose_name="Идентификатор")
    username    = CharField()
    login_time  = DateTimeField()
    logout_time = DateTimeField(null=True)

    class Meta:
        table_name = 'userlog'
# ─────────────────────────────────────────────
#  Customer  —  Заказчики
# ─────────────────────────────────────────────
class Customer(BaseModel):
    id               = AutoField(primary_key=True, verbose_name="Идентификатор")

    name             = CharField(max_length=512, verbose_name="Наименование организации")
    law              = CharField(null=True, max_length=255, verbose_name="Закон")
    ogrn             = CharField(null=True, max_length=50,  verbose_name="ОГРН")
    inn              = CharField(null=True, max_length=50,  verbose_name="ИНН", unique=True)
    kpp              = CharField(null=True, max_length=50,  verbose_name="КПП")
    country          = CharField(null=True, max_length=255, verbose_name="Страна")
    region           = CharField(null=True, max_length=255, verbose_name="Регион")
    city             = CharField(null=True, max_length=255, verbose_name="Город")
    address_full     = CharField(null=True, max_length=512, verbose_name="Полный адрес")
    organization_url = CharField(null=True, max_length=512, verbose_name="Сайт организации")
    organization_id  = IntegerField(null=True,verbose_name="ID организации")
    customer_code    = CharField(null=True, max_length=100, verbose_name="Код заказчика")
    purchases_url    = CharField(null=True, max_length=512, verbose_name="Ссылка на закупки")
    contracts_url    = CharField(null=True, max_length=512, verbose_name="Ссылка на контракты")
    account_card_url     = CharField(null=True, max_length=512, verbose_name="Карточка аккаунта")
    additional_info_url  = CharField(null=True, max_length=512, verbose_name="Доп. информация")

    # ── JSON-поля ─────────────────────────────
    documents_card_json  = TextField(null=True, verbose_name="Вложения")
    additional_info_json = TextField(null=True, verbose_name="Дополнительная информация")
    journal_versions_json = TextField(null=True, verbose_name="Журнал версий")

    def __str__(self):
        return self.name

    class Meta:
        table_name = 'customer'
# ─────────────────────────────────────────────
#  ChangedDate  —  История изменений закупок
# ─────────────────────────────────────────────
class ChangedDate(BaseModel):
    id             = AutoField(primary_key=True, verbose_name="Идентификатор")
    RegistryNumber = CharField()
    username       = CharField()
    chenged_time   = DateTimeField()
    PurchaseName   = CharField(null=True)
    Role           = CharField(null=True)
    Type           = CharField(null=True)

    class Meta:
        table_name = 'changeddate'
# ─────────────────────────────────────────────
#  Supplier  —  Поставщики (исполнители контракта)
# ─────────────────────────────────────────────
class Supplier(BaseModel):
    id           = AutoField(primary_key=True, verbose_name="Идентификатор")

    organization  = CharField(null=True, max_length=512, verbose_name="Организация")
    country       = CharField(null=True, max_length=255, verbose_name="Страна")
    address       = CharField(null=True, max_length=512, verbose_name="Адрес")
    index_address = CharField(null=True, max_length=50,  verbose_name="Почтовый индекс")
    phone         = CharField(null=True, max_length=100, verbose_name="Телефон")
    mail          = CharField(null=True, max_length=255, verbose_name="Email")
    status        = CharField(null=True, max_length=255, verbose_name="Статус")
    inn           = CharField(null=True, max_length=50,  verbose_name="ИНН")
    kpp           = CharField(null=True, max_length=50,  verbose_name="КПП")

    contract      = ForeignKeyField(Contract, on_delete='CASCADE', backref='suppliers', verbose_name="Контракт")

    class Meta:
        table_name = 'supplier'
# ─────────────────────────────────────────────
#  Vessel  —  Характеристики судна
# ─────────────────────────────────────────────
class Vessel(BaseModel):
    id = AutoField(primary_key=True, verbose_name="Идентификатор")

    # ── Идентификация ─────────────────────────
    # ── Идентификация ─────────────────────────
    imo_number = CharField(null=True, max_length=50, verbose_name="Номер ИМО")
    ship_project = CharField(null=True, max_length=255, verbose_name="Проект судна")
    registry_number = CharField(null=True, max_length=255, verbose_name="Реестровый номер")  # ← новое
    build_number = CharField(null=True, max_length=255, verbose_name="Строительный номер")  # ← новое

    # ── Классификация РМРС / РКО ──────────────
    ship_type_rmrs    = CharField(null=True, max_length=255, verbose_name="Тип судна (РМРС)")
    ship_type_rko     = CharField(null=True, max_length=255, verbose_name="Тип и назначение (РКО)")
    ship_class        = CharField(null=True, max_length=255, verbose_name="Класс")
    subclass          = CharField(null=True, max_length=255, verbose_name="Подкласс")
    ship_type         = CharField(null=True, max_length=255, verbose_name="Тип")
    subtype           = CharField(null=True, max_length=255, verbose_name="Подтип")
    group             = CharField(null=True, max_length=255, verbose_name="Группа")
    subgroup          = CharField(null=True, max_length=255, verbose_name="Подгруппа")

    # ── Даты постройки ────────────────────────
    year_built        = IntegerField(null=True, verbose_name="Год постройки")
    date_keel_laid    = DateField(null=True,    verbose_name="Дата закладки киля")
    date_launched     = DateField(null=True,    verbose_name="Дата спуска на воду")
    date_built        = DateField(null=True,    verbose_name="Дата постройки")
    country_built     = CharField(null=True, max_length=255, verbose_name="Страна постройки")

    # ── Размерения и вместимость ──────────────
    gross_tonnage     = FloatField(null=True, verbose_name="Валовая вместимость")
    net_tonnage       = FloatField(null=True, verbose_name="Чистая вместимость")
    deadweight        = FloatField(null=True, verbose_name="Дедвейт")
    displacement_max  = FloatField(null=True, verbose_name="Водоизмещение наибольшее")
    length_max        = FloatField(null=True, verbose_name="Длина наибольшая")
    width_max         = FloatField(null=True, verbose_name="Ширина наибольшая")
    height_max        = FloatField(null=True, verbose_name="Высота борта наибольшая")
    draft_max         = FloatField(null=True, verbose_name="Осадка наибольшая")
    cubic_module      = FloatField(null=True, verbose_name="Кубический модуль")
    length_width_ratio = FloatField(null=True, verbose_name="Отношение Длина/Ширина")
    speed_max         = FloatField(null=True, verbose_name="Скорость наибольшая")

    # ── Грузовые характеристики ───────────────
    cargo_holds_count    = IntegerField(null=True, verbose_name="Количество грузовых трюмов")
    liquid_tanks_count   = IntegerField(null=True, verbose_name="Наливные танки (количество)")
    teu_count            = IntegerField(null=True, verbose_name="Количество контейнеров TEU")
    decks_count          = IntegerField(null=True, verbose_name="Количество палуб")
    bulkheads_count      = IntegerField(null=True, verbose_name="Количество переборок")

    # ── Пассажиры ─────────────────────────────
    passengers_berth     = IntegerField(null=True, verbose_name="Число пассажиров коечных")
    passengers_no_berth  = IntegerField(null=True, verbose_name="Число пассажиров бескоечных")

    # ── Грузовое оборудование ─────────────────
    hatches_count     = IntegerField(null=True, verbose_name="Грузовые люки (количество)")
    booms_count       = IntegerField(null=True, verbose_name="Стрелы (количество)")
    cranes_count      = IntegerField(null=True, verbose_name="Краны (количество)")

    # ── Материалы и конструкция ───────────────
    hull_material          = CharField(null=True, max_length=255, verbose_name="Материал корпуса")
    superstructure_material = CharField(null=True, max_length=255, verbose_name="Материал надстройки")
    has_hydrofoil          = BooleanField(null=True, verbose_name="Наличие подводных крыльев")


    # ── Верфь постройки ───────────────────────
    city_built             = CharField(null=True, max_length=255, verbose_name="Город постройки судна")
    region_built           = CharField(null=True, max_length=255, verbose_name="Регион РФ")
    federal_district       = CharField(null=True, max_length=255, verbose_name="Федеральный округ")
    shipyard_name          = CharField(null=True, max_length=512, verbose_name="Верфь постройки судна")
    shipyard_inn           = CharField(null=True, max_length=50,  verbose_name="ИНН верфи")
    shipyard_kpp           = CharField(null=True, max_length=50,  verbose_name="КПП верфи")
    shipyard_ogrn          = CharField(null=True, max_length=50,  verbose_name="ОГРН верфи")

    # ── Связь с закупкой (FK, опционально) ────
    purchase  = ForeignKeyField(Purchase,  null=True, on_delete='SET NULL', backref='vessels', verbose_name="Закупка")

    class Meta:
        table_name = 'vessel'

# ─────────────────────────────────────────────
# VesselEngine — Силовые установки судна
# ─────────────────────────────────────────────
class VesselEngine(BaseModel):
    id = AutoField(primary_key=True, verbose_name="Идентификатор")

    # ── Тип и порядковый номер ────────────────
    engine_number = IntegerField(null=True, verbose_name="Порядковый номер двигателя")
    engine_role = CharField(null=True, max_length=100, verbose_name="Роль установки")
    # например: "Главный", "Вспомогательный", "Подруливающий"

    # ── Силовая установка ─────────────────────
    power_plant_type = CharField(null=True, max_length=255, verbose_name="Тип силовой установки")
    engine_type = CharField(null=True, max_length=255, verbose_name="Тип двигателя")
    engine_brand = CharField(null=True, max_length=255, verbose_name="Фирма")
    engine_model = CharField(null=True, max_length=255, verbose_name="Марка")
    engine_year = IntegerField(null=True, verbose_name="Год выпуска")
    engine_kw = FloatField(null=True, verbose_name="Мощность, кВт")
    engine_rpm = FloatField(null=True, verbose_name="Обороты, об/мин")
    battery_capacity = FloatField(null=True, verbose_name="Ёмкость АКБ")

    # ── Движитель ─────────────────────────────
    propeller_type = CharField(null=True, max_length=255, verbose_name="Движитель, тип")
    propeller_blades = IntegerField(null=True, verbose_name="Количество лопастей")

    # ── Связь с судном ────────────────────────
    vessel = ForeignKeyField(Vessel, on_delete='CASCADE', backref='engines', verbose_name="Судно")

    class Meta:
        table_name = 'vessel_engine'

# ─────────────────────────────────────────────
# ContractVersion — Версии контрактов (снимки)
# ─────────────────────────────────────────────
class ContractVersion(BaseModel):
    id = AutoField(primary_key=True, verbose_name="Идентификатор")

    # ── Связь с актуальным контрактом ─────────
    contract    = ForeignKeyField(Contract, on_delete='CASCADE',
                                  backref='versions', verbose_name="Контракт")
    reg_number  = CharField(max_length=512, verbose_name="Реестровый номер")  # денормализован для поиска
    contract_url = TextField(verbose_name="Ссылка на контракт")

    # ── Плоские поля — зеркало Contract ───────
    law                       = TextField(null=True, verbose_name="Закон")
    number                    = TextField(null=True, verbose_name="Номер контракта")
    status                    = TextField(null=True, verbose_name="Статус")
    object_name               = TextField(null=True, verbose_name="Наименование объекта")
    customer_name             = TextField(null=True, verbose_name="Заказчик")
    customer_url              = TextField(null=True, verbose_name="Ссылка на заказчика")
    contract_price            = TextField(null=True, verbose_name="Цена контракта")
    date_contract_signed      = TextField(null=True, verbose_name="Дата подписания")
    date_execution_due        = TextField(null=True, verbose_name="Дата исполнения")
    date_registered           = TextField(null=True, verbose_name="Дата регистрации")
    date_updated_in_registry  = TextField(null=True, verbose_name="Дата обновления в реестре")
    version                   = TextField(null=True, verbose_name="Версия из реестра")

    # ── JSON-поля — полный слепок ──────────────
    common_info_json       = TextField(null=True, verbose_name="Общая информация")
    payment_targets_json   = TextField(null=True, verbose_name="Платежи и объекты закупки")
    process_info_json      = TextField(null=True, verbose_name="Исполнение контракта")
    documents_json         = TextField(null=True, verbose_name="Вложения")
    journal_versions_json  = TextField(null=True, verbose_name="Журнал версий")
    event_log_json         = TextField(null=True, verbose_name="Журнал событий")

    # ── Метаданные снимка ─────────────────────
    captured_at = DateTimeField(default=datetime.now, verbose_name="Дата и время снимка")

    class Meta:
        table_name = 'contract_versions'
        indexes = (
            # UNIQUE: одна запись на (contract, version)
            (('contract', 'version'), True),
            # обычные индексы для поиска
            (('contract',), False),
            (('reg_number',), False),
        )

# ─────────────────────────────────────────────
#  Инициализация БД
# ─────────────────────────────────────────────
ALL_MODELS = [
    Purchase,
    Contract,
    FinalDetermination,
    CurrencyRate,
    User,
    Role,
    UserRole,
    UserLog,
    ChangedDate,
    Customer,
    Supplier,
Vessel,
ContractVersion,
VesselEngine
]



def init_db():
    """Создание всех таблиц (если не существуют)."""
    db.connect(reuse_if_open=True)
    db.create_tables(ALL_MODELS, safe=True)
    db.close()


def get_json_field(instance, field_name: str) -> dict | list | None:
    raw = getattr(instance, field_name)
    if raw:
        return json.loads(raw)
    return None

def set_json_field(instance, field_name: str, value: dict | list):
    setattr(instance, field_name, json.dumps(value, ensure_ascii=False))


if __name__ == '__main__':
    init_db()
    print("База данных успешно инициализирована.")
    print(f"Таблицы: {[m._meta.table_name for m in ALL_MODELS]}")
