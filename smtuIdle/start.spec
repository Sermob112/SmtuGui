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
    ]
)
PROJECT_ROOT = 'C:\\Users\\Sergey\\Desktop\\Work\\SmtuGui'
SMTU_PACKAGE = os.path.join(PROJECT_ROOT, 'smtuIdle')
datas = [
    (SMTU_PACKAGE, 'smtuIdle'),   # (откуда, куда внутри .exe)
    (os.path.join(PROJECT_ROOT, 'Pics'), 'Pics'),
]

a = Analysis(
    ['start.py'],
    pathex=['.'],               # текущая папка в sys.path
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
    console=True,             # True пока отлаживаете!
    icon='C:\\Users\\Sergey\\Desktop\\work\\Иконки\\BD.ico',
)