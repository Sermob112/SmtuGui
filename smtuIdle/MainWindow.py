from PySide6 import QtCore, QtGui, QtWidgets

from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from PySide6.QtWidgets import *
from PySide6 import QtCore
from DBtest import PurchasesWidget
from LoadCsv import CsvLoaderWidget
from InsertWidget import InsertWidget
from statisticWidget import StatisticWidget


class Ui_MainWindow(object):
    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        
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

        self.pushButton4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton4.setObjectName("pushButton4")
        self.leftPanelLayout.addWidget(self.pushButton4)

        self.pushButton5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton5.setObjectName("pushButton4")
        self.leftPanelLayout.addWidget(self.pushButton5)
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

        self.page4 = QtWidgets.QWidget()
        self.label4 = QtWidgets.QLabel(self.page4)
        self.stackedWidget.addWidget(self.page4)

        self.page5 = QtWidgets.QWidget()
        self.label5 = QtWidgets.QLabel(self.page5)
        self.stackedWidget.addWidget(self.page5)

        #Загрузка виджета БД
        self.purchaseViewer = PurchasesWidget()
        layout = QVBoxLayout(self.page2)
        layout.addWidget(self.purchaseViewer)
         #Загрузка виджета CSV
        self.loadCsv = CsvLoaderWidget()
        layout = QVBoxLayout(self.page3)
        layout.addWidget(self.loadCsv)
        
        #Загрузка виджета ввод данных
        self.Insert = InsertWidget()
        layout = QVBoxLayout(self.page4)
        layout.addWidget(self.Insert)
          #Загрузка виджета статистического анализа
        self.Statistic = StatisticWidget()
        layout = QVBoxLayout(self.page5)
        layout.addWidget(self.Statistic)

        self.horizontalLayout.addWidget(self.stackedWidget)

        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)

        # Подключение сигналов к слотам
        self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.pushButton4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.pushButton5.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton1.setText(_translate("MainWindow", "Кнопка 1"))
        self.pushButton2.setText(_translate("MainWindow", "Кнопка 2"))
        self.pushButton3.setText(_translate("MainWindow", "Кнопка 3"))
        self.pushButton4.setText(_translate("MainWindow", "Кнопка 4"))
        self.pushButton5.setText(_translate("MainWindow", "Кнопка 5"))

        self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.pushButton4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.pushButton5.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))


# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     MainWindow = QtWidgets.QMainWindow()
#     ui = Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec())
