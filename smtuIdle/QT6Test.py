from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout

class MyWidget(QWidget):
    def __init__(self):
        super(MyWidget, self).__init__()

        layout = QVBoxLayout(self)

        # Создаем QGridLayout
        price_layout = QGridLayout()

        # Устанавливаем расстояние между элементами
        price_layout.setSpacing(5)  # Вы можете установить свою величину

        # Добавляем лейбл и поле для минимальной цены
        price_layout.addWidget(self.min_price_label, 0, 0)
        price_layout.addWidget(self.min_price_input, 0, 1)

        # Добавляем лейбл и поле для максимальной цены
        price_layout.addWidget(self.max_price_label, 1, 0)
        price_layout.addWidget(self.max_price_input, 1, 1)

        # Устанавливаем ширину столбцов
        price_layout.setColumnStretch(0, 0)  # Устанавливаем ширину первого столбца (лейбл) в 0
        price_layout.setColumnStretch(1, 1)  # Устанавливаем ширину второго столбца (поле ввода) в 1

        # Создаем горизонтальный лейаут для выравнивания сетки
        alignment_layout = QHBoxLayout()
        alignment_layout.addLayout(price_layout)

        # Устанавливаем выравнивание для горизонтального лейаута
        alignment_layout.setAlignment(Qt.AlignLeft)

        # Добавляем горизонтальный лейаут в основной вертикальный лейаут
        layout.addLayout(alignment_layout)

if __name__ == '__main__':
    app = QApplication([])
    widget = MyWidget()
    widget.show()
    app.exec_()