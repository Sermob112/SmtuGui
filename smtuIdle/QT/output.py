# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LoginWindow.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextEdit,
    QWidget)

class Ui_LoginWindow(object):
    def setupUi(self, LoginWindow):
        if not LoginWindow.objectName():
            LoginWindow.setObjectName(u"LoginWindow")
        LoginWindow.resize(800, 600)
        self.centralwidget = QWidget(LoginWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.Login = QPushButton(self.centralwidget)
        self.Login.setObjectName(u"Login")
        self.Login.setGeometry(QRect(310, 400, 141, 41))
        self.LoginEdit = QTextEdit(self.centralwidget)
        self.LoginEdit.setObjectName(u"LoginEdit")
        self.LoginEdit.setGeometry(QRect(250, 290, 281, 31))
        self.PasswordEdit = QTextEdit(self.centralwidget)
        self.PasswordEdit.setObjectName(u"PasswordEdit")
        self.PasswordEdit.setGeometry(QRect(250, 340, 281, 31))
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(130, 70, 511, 201))
        self.label.setSizeIncrement(QSize(0, 0))
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(14)
        font.setKerning(False)
        self.label.setFont(font)
        self.label.setTextFormat(Qt.AutoText)
        self.label.setWordWrap(True)
        LoginWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(LoginWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        LoginWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(LoginWindow)
        self.statusbar.setObjectName(u"statusbar")
        LoginWindow.setStatusBar(self.statusbar)

        self.retranslateUi(LoginWindow)

        QMetaObject.connectSlotsByName(LoginWindow)
    # setupUi

    def retranslateUi(self, LoginWindow):
        LoginWindow.setWindowTitle(QCoreApplication.translate("LoginWindow", u"MainWindow", None))
        self.Login.setText(QCoreApplication.translate("LoginWindow", u"\u0412\u043e\u0439\u0442\u0438", None))
        self.label.setText(QCoreApplication.translate("LoginWindow", u"<html><head/><body><p align=\"center\">&quot;\u0411\u0410\u0417\u0410 \u0414\u0410\u041d\u041d\u042b\u0425 \u041e\u0411\u041e\u0421\u041d\u041e\u0412\u0410\u041d\u0418\u0419 \u041d\u0410\u0427\u0410\u041b\u042c\u041d\u042b\u0425 (\u041c\u0410\u041a\u0421\u0418\u041c\u0410\u041b\u042c\u041d\u042b\u0425) \u0426\u0415\u041d \u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u0418 \u0426\u0415\u041d \u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u041d\u0410 \u0421\u0422\u0420\u041e\u0418\u0422\u0415\u041b\u042c\u0421\u0422\u0412\u041e \u0421\u0423\u0414\u041e\u0412, \u0417\u0410\u041a\u041b\u042e\u0427\u0410\u0415\u041c\u042b\u0425 \u0421 \u0415\u0414\u0418\u041d\u0421\u0422\u0412\u0415\u041d\u041d\u042b\u041c \u041f\u041e\u0421\u0422\u0410\u0412\u0429\u0418\u041a\u041e\u041c, \u0410 \u0422\u0410\u041a\u0416\u0415 \u0426\u0415\u041d \u0417\u0410\u041a\u041b\u042e\u0427\u0415\u041d\u041d\u042b\u0425 \u0413\u041e\u0421\u0423\u0414\u0410\u0420\u0421\u0422\u0412\u0415\u041d\u041d\u042b\u0425 "
                        "\u041a\u041e\u041d\u0422\u0420\u0410\u041a\u0422\u041e\u0412 \u041d\u0410 \u0421\u0422\u0420\u041e\u0418\u0422\u0415\u041b\u042c\u0421\u0422\u0412\u041e \u0421\u0423\u0414\u041e\u0412&quot;</p></body></html>", None))
    # retranslateUi

