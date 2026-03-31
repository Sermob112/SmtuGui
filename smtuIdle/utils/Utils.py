from pathlib import Path

# Указываем нужную директорию (в вашем случае — на уровень выше)
current_dir = Path('..')

# rglob('*.py') рекурсивно ищет только файлы с расширением .py во всех подпапках
for item in current_dir.rglob('*.py'):
    if item.is_file():
        print(f"📄 Python файл: {item}")