from pathlib import Path
import re
from typing import Optional

# ── Импортируем db и Purchase из ОДНОГО места (как в вашем рабочем коде) ──
from smtuIdle.BD.models import db, Purchase

# ── Пути ──────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\Sergey\Desktop\Work\SmtuGui")
DB_PATH = BASE_DIR / "smtuIdle" / "database.db"
FILES_DIR = BASE_DIR / "db_files"

# ── Инициализация БД ──────────────────────────────
db.init(DB_PATH)
db.connect(reuse_if_open=True)

# ── Функции ───────────────────────────────────────

def extract_number_from_path(path_str: str) -> Optional[str]:
    """
    Извлекает номер закупки из пути или имени файла.
    """
    path_obj = Path(path_str)
    name = path_obj.name

    # Ищем длинную последовательность цифр (номер закупки)
    match = re.search(r"(?:№\s*|No\s*|N\s*|№\.?\s*)?(\d{10,})", name, re.IGNORECASE)
    if match:
        return match.group(1)

    # Альтернатива: ищем любую длинную последовательность цифр
    all_digits = re.findall(r"\d{10,}", path_str)
    if all_digits:
        return all_digits[0]

    return None


def update_nmck_files_in_db():
    """
    Проходит по всем файлам в папке FILES_DIR,
    извлекает номер закупки и обновляет поле file_4 в БД.
    """
    updated_count = 0
    not_found_count = 0
    no_number_count = 0

    # 🔍 ОТЛАДКА
    print(f"📁 Путь к БД: {DB_PATH.absolute()}")
    print(f"📁 БД существует: {DB_PATH.exists()}")
    print(f"📁 Путь к файлам: {FILES_DIR.absolute()}")
    print(f"📁 Папка файлов существует: {FILES_DIR.exists()}")

    all_files = list(FILES_DIR.rglob("*"))
    print(f"📄 Всего файлов найдено: {len(all_files)}\n")

    for file_path in all_files:
        if not file_path.is_file():
            continue

        print(f"🔍 Файл: {file_path.name}")

        # Извлекаем номер закупки
        registry_number = extract_number_from_path(str(file_path))

        if not registry_number:
            no_number_count += 1
            print(f"   ⚠️  Не извлечён номер\n")
            continue

        print(f"   Номер: {registry_number}")

        # ⚠️ ВАЖНО: относительный путь от smtuGui (чтобы работало при переносе)
        relative_path = str(file_path.relative_to(BASE_DIR))
        print(f"   Путь: {relative_path}")

        # Ищем в БД
        purchase = Purchase.get_or_none(Purchase.RegistryNumber == registry_number)

        if purchase:
            purchase.file_4 = relative_path
            purchase.save()
            updated_count += 1
            print(f"   ✅ Обновлено\n")
        else:
            not_found_count += 1
            print(f"   ❌ Не найдено в БД\n")

    print(f"\n═══════════════════════════════════════")
    print(f"✅ Обновлено: {updated_count}")
    print(f"❌ Не найдено: {not_found_count}")
    print(f"⚠️  Без номера: {no_number_count}")
    print(f"═══════════════════════════════════════")


# ── Запуск ────────────────────────────────────────
if __name__ == "__main__":
    try:
        update_nmck_files_in_db()
    finally:
        db.close()