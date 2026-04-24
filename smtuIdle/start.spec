# pyinstaller start.spec --clean
from PyInstaller.utils.hooks import collect_submodules, collect_all
import sys

block_cipher = None

# Собираем ВСЕ подмодули smtuIdle
hidden_imports = (
    collect_submodules('smtuIdle')
    + collect_submodules('peewee')
    + [
        'smtuIdle',
        'smtuIdle.BD',
        'smtuIdle.BD.models',
        'smtuIdle.BD.initialize_db',
        'peewee',
        'openpyxl',
        'matplotlib',
        'matplotlib.backends.backend_qtagg',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCharts',
        'PySide6.QtSvg',         # ← ДОБАВИТЬ
        'PySide6.QtSvgWidgets',  # ← ДОБАВИТЬ
    ]
)
PROJECT_ROOT = 'C:\\Users\\Sergey\\Desktop\\Work\\SmtuGui'
SMTU_PACKAGE = os.path.join(PROJECT_ROOT, 'smtuIdle')
import os
from pathlib import Path

PROJECT_ROOT = 'C:\\Users\\Sergey\\Desktop\\Work\\SmtuGui'
SMTU_PACKAGE = os.path.join(PROJECT_ROOT, 'smtuIdle')

# Функция, которая собирает только .py файлы из указанной директории
def collect_only_py(src_dir, dest_prefix):
    result = []
    src_path = Path(src_dir)
    for py_file in src_path.rglob('*.py'):
        # Вычисляем относительный путь внутри пакета (куда класть файл в .exe)
        relative_dest = os.path.join(dest_prefix, py_file.parent.relative_to(src_path.parent))
        result.append((str(py_file), str(relative_dest)))
    return result

datas = (
    collect_only_py(SMTU_PACKAGE, 'smtuIdle')   # Только .py из smtuIdle
    + [(os.path.join(PROJECT_ROOT, 'Pics'), 'Pics')]  # Картинки — оставляем как есть
)

a = Analysis(
    ['start.py'],
    pathex=[PROJECT_ROOT],              # текущая папка в sys.path
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PyQt6'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='SmtuDB',
    debug=False,
    strip=False,
    upx=True,
    console=False,             # True пока отлаживаете!
    icon='C:\\Users\\Sergey\\Desktop\\work\\Иконки\\BD.ico',
)