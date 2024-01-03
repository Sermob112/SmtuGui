
from PySide6 import QtCore, QtGui, QtWidgets
from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from PySide6.QtWidgets import *
from PySide6 import QtCore
from DBtest import PurchasesWidget
from LoadCsv import CsvLoaderWidget
from InsertWidget import InsertWidget



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setLayout(self.setupMainLayout())

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setupMainLayout(self):
        verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        topLayout, bottomLayout = self.setupTopLayout(), self.setupBottomLayout()
        verticalLayout.addLayout(topLayout)
        verticalLayout.addLayout(bottomLayout)
        return verticalLayout

    def setupTopLayout(self):
        topLayout = QtWidgets.QHBoxLayout()

        topLayout.addWidget(self.setupLeftTopWidget())
        topLayout.addWidget(self.setupCenterWidget())
        topLayout.addWidget(self.setupRightTopWidget())

        return topLayout

    def setupLeftTopWidget(self):
        leftTopWidget = QtWidgets.QWidget(self.centralwidget)
        leftTopLayout = QtWidgets.QVBoxLayout(leftTopWidget)

        self.dbLabel = QtWidgets.QLabel(leftTopWidget)
        self.dbLabel.setText("БД НМЦК и ЦК")
        self.dbLabel.setAlignment(QtCore.Qt.AlignLeft)
        leftTopLayout.addWidget(self.dbLabel)

        return leftTopWidget

    def setupCenterWidget(self):
        return QtWidgets.QWidget(self.centralwidget)

    def setupRightTopWidget(self):
        rightTopWidget = QtWidgets.QWidget(self.centralwidget)
        rightTopLayout = QtWidgets.QVBoxLayout(rightTopWidget)

        self.userLabel = QtWidgets.QLabel(rightTopWidget)
        self.userLabel.setText("Пользователь: Заглушка")
        rightTopLayout.addWidget(self.userLabel)

        self.purchaseLabel = QtWidgets.QLabel(rightTopWidget)
        self.purchaseLabel.setText("Закупок в БД: _______. Дата: _______")
        rightTopLayout.addWidget(self.purchaseLabel)

        return rightTopWidget

    def setupBottomLayout(self):
        horizontalLayout = QtWidgets.QHBoxLayout()

        leftPanelLayout = self.setupLeftPanel()
        line, stackedWidget = self.setupLine(), self.setupStackedWidget()

        horizontalLayout.addLayout(leftPanelLayout)
        horizontalLayout.addWidget(line)
        horizontalLayout.addWidget(stackedWidget)

        return horizontalLayout

    def setupLeftPanel(self):
        leftPanelLayout = QtWidgets.QVBoxLayout()

        self.pushButton1 = self.createButton("Кнопка 1", lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton2 = self.createButton("Кнопка 2", lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton3 = self.createButton("Кнопка 3", lambda: self.stackedWidget.setCurrentIndex(2))
        self.pushButton4 = self.createButton("Кнопка 4", lambda: self.stackedWidget.setCurrentIndex(3))

        leftPanelLayout.addWidget(self.pushButton1)
        leftPanelLayout.addWidget(self.pushButton2)
        leftPanelLayout.addWidget(self.pushButton3)
        leftPanelLayout.addWidget(self.pushButton4)

        return leftPanelLayout

    def createButton(self, text, slot):
        button = QtWidgets.QPushButton(self.centralwidget)
        button.setText(text)
        button.clicked.connect(slot)
        return button

    def setupLine(self):
        line = QtWidgets.QFrame(self.centralwidget)
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    def setupStackedWidget(self):
        
        stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        stackedWidget.setObjectName("stackedWidget")

        pages = [self.setupPage(index) for index in range(1, 5)]

        for page in pages:
            stackedWidget.addWidget(page)

        self.stackedWidget = stackedWidget  # Сохраняем атрибут объекта
        return stackedWidget

    def setupPage(self, index):
        page = QtWidgets.QWidget()
        label = QtWidgets.QLabel(page)
        label.setGeometry(QtCore.QRect(100, 100, 200, 50))
        setattr(self, f"label{index}", label)  # Добавить атрибут, чтобы избежать утечек памяти
        return page

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton1.setText(_translate("MainWindow", "Кнопка 1"))
        self.pushButton2.setText(_translate("MainWindow", "Кнопка 2"))
        self.pushButton3.setText(_translate("MainWindow", "Кнопка 3"))
        self.pushButton4.setText(_translate("MainWindow", "Кнопка 4"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())