from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QCompleter, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QStringListModel
class AutoCompleteLineEdit(QWidget):
    def __init__(self,  parent=None):
        super(AutoCompleteLineEdit, self).__init__(parent)
        data = ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape']
        # Создаем элементы интерфейса
        self.label = QLabel("Поиск:")
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Введите текст")

        # Создаем модель данных и устанавливаем список данных
        completer = QCompleter(data)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.lineEdit.setCompleter(completer)

        # Создаем макет и добавляем элементы
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.lineEdit)

if __name__ == '__main__':
    app = QApplication([])

    # Ваш список данных
   

    # Создаем и отображаем окно
    window = AutoCompleteLineEdit()
    window.show()

    app.exec_()
