# import os

# def list_files_in_current_directory():
#     # Получаем текущую рабочую папку
#     current_directory = os.getcwd()

#     # Получаем список файлов и папок в текущей рабочей папке
#     files_and_folders = os.listdir(current_directory)

#     # Фильтруем только файлы и выводим их на экран
#     files = [file for file in files_and_folders if os.path.isfile(os.path.join(current_directory, file))]
#     for file in files:
#         print(file)

# if __name__ == "__main__":
#     list_files_in_current_directory()
import sys
from PySide6.QtWidgets import *
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Collapsible Content")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        # Создаем кнопку для управления видимостью содержимого
        self.toggle_button = QPushButton("Показать меню")
        self.toggle_button.clicked.connect(self.toggle_menu)
        layout.addWidget(self.toggle_button)

        # Создаем виджет для размещения содержимого, которое будет скрываемым
        self.menu_content = QWidget()
        menu_layout = QVBoxLayout()
        menu_layout.addWidget(QPushButton("Элемент меню 1"))
        menu_layout.addWidget(QPushButton("Элемент меню 2"))
        menu_layout.addWidget(QPushButton("Элемент меню 3"))
        self.menu_content.setLayout(menu_layout)

        # Устанавливаем виджет содержимого в рамку для добавления стиля
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(QVBoxLayout())
        self.menu_frame.layout().addWidget(self.menu_content)

        # Скрываем содержимое по умолчанию
        self.menu_frame.setVisible(False)

        layout.addWidget(self.menu_frame)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def toggle_menu(self):
        # Изменяем видимость содержимого при нажатии на кнопку
        self.menu_frame.setVisible(not self.menu_frame.isVisible())
        if self.menu_frame.isVisible():
            self.toggle_button.setText("Скрыть меню")
        else:
            self.toggle_button.setText("Показать меню")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())