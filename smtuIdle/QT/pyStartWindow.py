# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StartWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QStatusBar, QWidget)

class Ui_StartWindow(object):
    def setupUi(self, StartWindow):
        if not StartWindow.objectName():
            StartWindow.setObjectName(u"StartWindow")
        StartWindow.resize(800, 600)
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(16)
        font.setBold(False)
        StartWindow.setFont(font)
        self.centralwidget = QWidget(StartWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(80, 60, 671, 211))
        font1 = QFont()
        font1.setFamilies([u"Times New Roman"])
        font1.setPointSize(16)
        font1.setBold(False)
        font1.setHintingPreference(QFont.PreferDefaultHinting)
        self.label.setFont(font1)
        self.label.setMouseTracking(True)
        self.label.setTabletTracking(False)
        self.label.setAcceptDrops(False)
        self.label.setWordWrap(True)
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(290, 270, 161, 61))
        self.pushButton.setStyleSheet(u"font: 16pt \"Times New Roman\";\n"
"border-radius: 20px;               \n"
"background-color: rgb(0, 17, 255);\n"
"color: rgb(255, 255, 255);")
        self.pushButton.setAutoRepeat(False)
        StartWindow.setCentralWidget(self.centralwidget)
        self.pushButton.raise_()
        self.label.raise_()
        self.statusbar = QStatusBar(StartWindow)
        self.statusbar.setObjectName(u"statusbar")
        StartWindow.setStatusBar(self.statusbar)

        self.retranslateUi(StartWindow)

        QMetaObject.connectSlotsByName(StartWindow)
    # setupUi

    def retranslateUi(self, StartWindow):
        StartWindow.setWindowTitle(QCoreApplication.translate("StartWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("StartWindow", u"<html><head/><body><p align=\"center\">\u042d\u041b\u0415\u041a\u0422\u0420\u041e\u041d\u041d\u0410\u042f \u0411\u0410\u0417\u0410 \u0414\u0410\u041d\u041d\u042b\u0425 \u041e\u0411\u041e\u0421\u041d\u041e\u0412\u0410\u041d\u0418\u0419 \u041d\u0410\u0427\u0410\u041b\u042c\u041d\u042b\u0425 (\u041c\u0410\u041a\u0421\u0418\u041c\u0410\u041b\u042c\u041d\u042b\u0425) \u0426\u0415\u041d \u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u0418 \u0426\u0415\u041d \u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u041d\u0410 \u0421\u0422\u0420\u041e\u0418\u0422\u0415\u041b\u042c\u0421\u0422\u0412\u041e \u0421\u0423\u0414\u041e\u0412, \u0417\u0410\u041a\u041b\u042e\u0427\u0410\u0415\u041c\u042b\u0425 \u0421 \u0415\u0414\u0418\u041d\u0421\u0422\u0412\u0415\u041d\u041d\u042b\u041c \u041f\u041e\u0421\u0422\u0410\u0412\u0429\u0418\u041a\u041e\u041c, \u0410 \u0422\u0410\u041a\u0416\u0415 \u0426\u0415\u041d \u0417\u0410\u041a\u041b\u042e\u0427\u0415\u041d\u041d\u042b\u0425 \u0413\u041e\u0421\u0423\u0414"
                        "\u0410\u0420\u0421\u0422\u0412\u0415\u041d\u041d\u042b\u0425 \u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u041d\u0410 \u0421\u0422\u0420\u041e\u0418\u0422\u0415\u041b\u042c\u0421\u0422\u0412\u041e \u0421\u0423\u0414\u041e\u0412 \u0418 \u0421\u0418\u0421\u0422\u0415\u041c\u0410 \u0423\u041f\u0420\u0410\u0412\u041b\u0415\u041d\u0418\u042f \u0411\u0414</p></body></html>", None))
        self.pushButton.setText(QCoreApplication.translate("StartWindow", u"\u0412\u043e\u0439\u0442\u0438", None))
    # retranslateUi

