"""Генерация DOCX-отчёта по результатам analyze_purchases_peewee.py."""

from datetime import datetime
from pathlib import Path
import pandas as pd

import analyze_purchases_peewee_date as analysis
from docx_report_generator import DocxReportGenerator

OUTPUT_FILE = Path("purchases_analysis_report.docx")


def fmt_int(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}".replace(",", " ")


def fmt_money(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.0f}".replace(",", " ") + " руб."


def fmt_pct(value):
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.1f}%"


def safe_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Не указано"
    return str(value)


def normalize_law_value(value):
    if value is None or pd.isna(value):
        return "Неизвестно"
    value = str(value).lower().replace("ё", "е").strip()
    if "44" in value:
        return "44-ФЗ"
    if "223" in value:
        return "223-ФЗ"
    return value


def normalize_law(df):
    if df.empty or "law" not in df.columns:
        return df
    df = df.copy()
    df["law"] = df["law"].map(normalize_law_value)
    return df


def pivot_to_rows(p_cnt, p_sum, row_limit=None):
    rows = []
    data_index = [x for x in p_cnt.index if x != "Общий итог"]
    if row_limit:
        data_index = data_index[:row_limit]

    for category in data_index:
        rows.append([
            safe_text(category),
            f"{fmt_int(p_cnt.loc[category, 'Всего'])} / {fmt_money(p_sum.loc[category, 'Всего'])}",
            f"{fmt_int(p_cnt.loc[category, '44-ФЗ'])} / {fmt_money(p_sum.loc[category, '44-ФЗ'])}",
            f"{fmt_int(p_cnt.loc[category, '223-ФЗ'])} / {fmt_money(p_sum.loc[category, '223-ФЗ'])}",
        ])
    return rows


def add_pivot_section(gen, number, title, df, group_col, value_col="price", row_order=None, limit=None):
    if df.empty or group_col not in df.columns:
        return False

    try:
        p_cnt, p_sum = analysis.build_count_sum_pivots(
            df, group_col, value_col=value_col, row_order=row_order, limit=limit
        )
    except (KeyError, ValueError, TypeError) as exc:
        gen.add_technical_box(
            f"Раздел {number}: {title}",
            f"Раздел не сформирован из-за ошибки группировки: {exc}",
            level="warning",
        )
        return False

    gen.add_section(
        f"{number}. {title.upper()}",
        f"Показаны количество записей и сумма показателя по категориям. "
        f"Всего записей в выборке: {fmt_int(len(df))}.",
    )
    gen.add_summary_table(
        {
            "headers": ["Категория", "Всего", "44-ФЗ", "223-ФЗ"],
            "rows": pivot_to_rows(p_cnt, p_sum, row_limit=limit),
        },
        footnote="Формат ячейки: количество записей / сумма, руб.",
    )
    return True


def build_kpi_rows(df):
    result = [
        ("Всего закупок", f"{fmt_int(len(df))} ед.", "-", "-"),
        ("Общая НМЦК", fmt_money(df["price"].sum()), "-", "-"),
    ]
    for law in analysis.LAWS:
        result.append((
            f"Закупок по {law}",
            f"{fmt_int((df['law'] == law).sum())} ед.",
            f"{fmt_int((df['law'] == '44-ФЗ').sum())} ед." if law == "44-ФЗ" else "-",
            f"{fmt_int((df['law'] == '223-ФЗ').sum())} ед." if law == "223-ФЗ" else "-",
        ))
    return result


def add_kpi_section(gen, df):
    gen.add_section(
        "1. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ",
        f"Анализ закупок с НМЦК не менее {fmt_money(100_000_000)} за период "
        f"с {analysis.DATE_FROM_STR} по {analysis.DATE_TO.date()}. "
        f"В выборку вошло {fmt_int(len(df))} закупок.",
    )
    gen.add_kpi_table(build_kpi_rows(df))


def add_contract_status_section(gen):
    eligible = analysis._get_eligible_registry_numbers(100_000_000)
    if not eligible:
        return

    analysis.db.connect(reuse_if_open=True)
    try:
        purchases = list(
            analysis.Purchase.select(
                analysis.Purchase.RegistryNumber,
                analysis.Purchase.PurchaseOrder,
                analysis.Purchase.ProcurementStage,
            ).where(analysis.Purchase.RegistryNumber.in_(eligible)).dicts()
        )
        contracts = list(
            analysis.Contract.select(
                analysis.Contract.RegistryNumber,
                analysis.Contract.ContractPrice,
            ).where(analysis.Contract.RegistryNumber.in_(list(eligible))).dicts()
        )
    finally:
        analysis.db.close()

    contract_by_reg = {row["RegistryNumber"]: row for row in contracts}
    rows = []
    for purchase in purchases:
        contract = contract_by_reg.get(purchase["RegistryNumber"])
        rows.append({
            "law": purchase["PurchaseOrder"],
            "status": purchase["ProcurementStage"] if contract else "Нет контракта",
            "price": analysis.clean_price_value(contract["ContractPrice"]) if contract else 0,
        })

    df = normalize_law(pd.DataFrame(rows))
    if df.empty:
        return

    add_pivot_section(gen, 7, "Статусы закупок и наличие контракта", df, "status")

    conversion_rows = []
    for law in analysis.LAWS:
        law_df = df[df["law"] == law]
        contracts_count = int((law_df["status"] != "Нет контракта").sum())
        conversion_rows.append([
            law,
            fmt_int(len(law_df)),
            fmt_int(contracts_count),
            fmt_pct(contracts_count / len(law_df) * 100 if len(law_df) else 0),
        ])

    gen.add_section("8. КОНВЕРСИЯ ЗАКУПОК В КОНТРАКТЫ")
    gen.add_summary_table(
        {
            "headers": ["Закон", "Закупки", "С контрактом", "Конверсия"],
            "rows": conversion_rows,
        },
        footnote="Конверсия: доля закупок, для которых найден контракт в реестре.",
    )


def build_report():
    purchases = normalize_law(analysis._load_purchases(min_price=100_000_000))
    if purchases.empty:
        raise RuntimeError("По заданным фильтрам закупки не найдены.")

    gen = DocxReportGenerator()
    gen.add_header(
        "Аналитический отчёт по закупкам",
        f"44-ФЗ и 223-ФЗ | НМЦК от 100 млн руб. | "
        f"{analysis.DATE_FROM_STR} — {analysis.DATE_TO.date()}",
    )
    gen.add_metadata_table({
        "Дата формирования": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "Источник данных": "SQLite через Peewee-модели analyze_purchases_peewee",
        "Период публикации": f"{analysis.DATE_FROM_STR} — {analysis.DATE_TO.date()}",
        "Ценовой фильтр": "НМЦК не менее 100 000 000 руб.",
        "Место подготовки": "Санкт-Петербург, Российская Федерация",
    })

    add_kpi_section(gen, purchases)
    add_pivot_section(gen, 2, "Распределение по диапазонам НМЦК", purchases,
                      "price_category_simple", row_order=analysis.PRICE_ORDER)
    add_pivot_section(gen, 3, "Способы определения поставщика", purchases,
                      "placing_way_cat", row_order=analysis.PLACING_WAY_ORDER)
    add_pivot_section(gen, 4, "Распределение закупок по законам", purchases,
                      "law", row_order=list(analysis.LAWS))
    add_pivot_section(gen, 5, "Заказчики: топ-20", purchases,
                      "customer_name", limit=20)
    add_pivot_section(gen, 6, "Закупки по годам", purchases, "year")

    contracts = normalize_law(analysis._load_contracts(min_price=20_000_000))
    if not contracts.empty:
        gen.add_page_break()
        gen.add_section(
            "9. АНАЛИЗ КОНТРАКТОВ",
            f"Выборка по закупкам с НМЦК не менее 20 млн руб. "
            f"за тот же период. Загружено {fmt_int(len(contracts))} контрактов.",
        )
        add_pivot_section(gen, "9.1", "Контракты по законам", contracts, "law")
        add_pivot_section(gen, "9.2", "Контракты по заказчикам: топ-30", contracts,
                          "customer_name", limit=30)

    suppliers = normalize_law(analysis._load_suppliers(min_price=100_000_000))
    if not suppliers.empty:
        add_pivot_section(gen, 10, "Поставщики крупных контрактов: топ-30",
                          suppliers, "organization", limit=30)

    add_contract_status_section(gen)

    gen.add_legend([
        ("Перерасход > +100%", gen.COLOR_OVERSPEND_HIGH),
        ("Перерасход +50...+100%", gen.COLOR_OVERSPEND_MED),
        ("Перерасход до +50%", gen.COLOR_OVERSPEND_LOW),
        ("Экономия до −20%", gen.COLOR_ECONOMY_LOW),
        ("Экономия −20...−50%", gen.COLOR_ECONOMY_MED),
        ("Экономия < −50%", gen.COLOR_ECONOMY_HIGH),
    ])

    gen.add_technical_box(
        "Методика формирования отчёта",
        "Данные загружаются непосредственно из SQLite через функции _load_purchases, "
        "_load_contracts и _load_suppliers. Для сводных таблиц используется та же "
        "build_count_sum_pivots, что и в analyze_purchases_peewee.py.",
        level="info",
    )
    gen.add_conclusions([
        ("Отчёт сформирован автоматически",
         f"В документ выгружены результаты анализа {fmt_int(len(purchases))} закупок "
         "с НМЦК от 100 млн руб. в заданном диапазоне дат."),
        ("Сводные таблицы используют исходные агрегаты анализа",
         "Количество записей и суммы сгруппированы по законам 44-ФЗ и 223-ФЗ "
         "с сохранением общей строки итога."),
    ])
    gen.add_footer()
    gen.save(str(OUTPUT_FILE))


if __name__ == "__main__":
    build_report()
