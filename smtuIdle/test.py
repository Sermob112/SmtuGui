from PySide6 import QtCore, QtGui, QtWidgets

from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton
from PySide6 import QtCore
from DBtest import PurchasesWidget
from LoadCsv import CsvLoaderWidget



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        # Главный макет
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Общий макет
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        # Верхний макет
        self.topLayout = QtWidgets.QHBoxLayout()

        # Статический виджет в левой части
        self.leftTopWidget = QtWidgets.QWidget(self.centralwidget)
        self.leftTopLayout = QtWidgets.QVBoxLayout(self.leftTopWidget)

        self.dbLabel = QtWidgets.QLabel(self.leftTopWidget)
        self.dbLabel.setText("БД НМЦК и ЦК")
        self.dbLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.leftTopLayout.addWidget(self.dbLabel)
        self.topLayout.addWidget(self.leftTopWidget)

        # Пустой виджет в центре
        self.centerWidget = QtWidgets.QWidget(self.centralwidget)
        self.topLayout.addWidget(self.centerWidget)

        # Статический виджет в правой части
        self.rightTopWidget = QtWidgets.QWidget(self.centralwidget)
        self.rightTopLayout = QtWidgets.QVBoxLayout(self.rightTopWidget)

        self.userLabel = QtWidgets.QLabel(self.rightTopWidget)
        self.userLabel.setText("Пользователь: Заглушка")
        self.rightTopLayout.addWidget(self.userLabel)
        self.purchaseLabel = QtWidgets.QLabel(self.rightTopWidget)
        self.purchaseLabel.setText("Закупок в БД: _______. Дата: _______")
        self.rightTopLayout.addWidget(self.purchaseLabel)

        # Добавление виджета в верхний макет
    

        self.topLayout.addWidget(self.rightTopWidget)

        self.verticalLayout.addLayout(self.topLayout)

        # Общий макет
        self.horizontalLayout = QtWidgets.QHBoxLayout()

        # Левая панель с кнопками
        self.leftPanelLayout = QtWidgets.QVBoxLayout()

        self.pushButton1 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton1.setObjectName("pushButton1")
        self.leftPanelLayout.addWidget(self.pushButton1)

        self.pushButton2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton2.setObjectName("pushButton2")
        self.leftPanelLayout.addWidget(self.pushButton2)

        self.pushButton3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton3.setObjectName("pushButton3")
        self.leftPanelLayout.addWidget(self.pushButton3)

        # Добавление кнопок в левую часть
        self.horizontalLayout.addLayout(self.leftPanelLayout)

        # Линия-разделитель
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.horizontalLayout.addWidget(self.line)

        # Стек виджет для правой части
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName("stackedWidget")

        # Добавление страниц в стек виджет
        self.page1 = QtWidgets.QWidget()
        self.label1 = QtWidgets.QLabel(self.page1)
        self.label1.setGeometry(QtCore.QRect(100, 100, 200, 50))
        self.stackedWidget.addWidget(self.page1)

        self.page2 = QtWidgets.QWidget()
        self.label2 = QtWidgets.QLabel(self.page2)
        self.label2.setGeometry(QtCore.QRect(100, 100, 200, 50))
        self.stackedWidget.addWidget(self.page2)

        self.page3 = QtWidgets.QWidget()
        self.label3 = QtWidgets.QLabel(self.page3)
        self.stackedWidget.addWidget(self.page3)

    
        self.purchaseViewer = PurchasesWidget()
        layout = QVBoxLayout(self.page2)
        layout.addWidget(self.purchaseViewer)

        self.loadCsv = CsvLoaderWidget()
        layout = QVBoxLayout(self.page3)
        layout.addWidget(self.loadCsv)

        self.horizontalLayout.addWidget(self.stackedWidget)

        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.label1.setText("Окно 1")
        self.label2.setText("Окно 2")
        self.label3.setText("Окно 3")

        # Подключение сигналов к слотам
        self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton1.setText(_translate("MainWindow", "Кнопка 1"))
        self.pushButton2.setText(_translate("MainWindow", "Кнопка 2"))
        self.pushButton3.setText(_translate("MainWindow", "Кнопка 3"))

        # Добавление обработчиков событий для кнопок переключения страниц
        self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

        # Загрузка данных в таблицу при отображении каждой из страниц
        # self.stackedWidget.currentChanged.connect(self.load_data_into_table)


    # def load_data_into_table(self):
    #     # Очищаем таблицу перед добавлением новых данных
    #     self.stackedWidget.clearContents()

        # Получаем данные из базы данных
        # purchases = Purchase.select().limit(5)  # Пример: загружаем первые 5 записей

        # Заполняем таблицу данными из запроса к базе данных
        # for row, purchase in enumerate(purchases):
        #     self.tableWidget.setItem(row, 0, QTableWidgetItem(str(purchase.Id)))
        #     self.tableWidget.setItem(row, 1, QTableWidgetItem(purchase.PurchaseOrder))
        #     self.tableWidget.setItem(row, 2, QTableWidgetItem(purchase.AuctionSubject))

    
    

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
