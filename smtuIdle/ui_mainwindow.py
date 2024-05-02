# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'untitled.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QStatusBar,
    QTextBrowser, QTextEdit, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(760, 657)
        font = QFont()
        font.setPointSize(14)
        MainWindow.setFont(font)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.Parse_but = QPushButton(self.centralwidget)
        self.Parse_but.setObjectName(u"Parse_but")
        self.Parse_but.setGeometry(QRect(30, 240, 171, 61))
        self.Parse_but.setStyleSheet(u"font: 14pt \"Impact\";")
        self.Lab = QLabel(self.centralwidget)
        self.Lab.setObjectName(u"Lab")
        self.Lab.setGeometry(QRect(30, 440, 331, 51))
        self.Lab.setStyleSheet(u"\n"
"border-color: rgb(0, 0, 0);\n"
"border-color: rgb(0, 255, 0);\n"
"font: 14pt \"Times New Roman\";\n"
"")
        self.Insert_text = QTextEdit(self.centralwidget)
        self.Insert_text.setObjectName(u"Insert_text")
        self.Insert_text.setGeometry(QRect(30, 500, 331, 51))
        self.Insert_text.setStyleSheet(u"\n"
"font: 75 14pt \"Times New Roman\";")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(440, 270, 291, 281))
        self.textBrowser.setStyleSheet(u"font: 10pt \"Impact\";")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(450, 230, 31, 31))
        self.label.setStyleSheet(u"font: 14pt \"Impact\";")
        self.FilePathIn = QLineEdit(self.centralwidget)
        self.FilePathIn.setObjectName(u"FilePathIn")
        self.FilePathIn.setGeometry(QRect(150, 70, 581, 31))
        self.FilePathIn.setStyleSheet(u"font: 12pt \"Impact\";")
        self.InputFileBut = QPushButton(self.centralwidget)
        self.InputFileBut.setObjectName(u"InputFileBut")
        self.InputFileBut.setGeometry(QRect(20, 50, 121, 51))
        self.InputFileBut.setStyleSheet(u"font: 12pt \"Impact\";")
        self.OutPutFileBut = QPushButton(self.centralwidget)
        self.OutPutFileBut.setObjectName(u"OutPutFileBut")
        self.OutPutFileBut.setGeometry(QRect(20, 130, 121, 51))
        self.OutPutFileBut.setStyleSheet(u"font: 12pt \"Impact\";")
        self.FilePathOut = QLineEdit(self.centralwidget)
        self.FilePathOut.setObjectName(u"FilePathOut")
        self.FilePathOut.setGeometry(QRect(150, 150, 581, 31))
        self.FilePathOut.setStyleSheet(u"font: 12pt \"Impact\";")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 760, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Parser 0.1b", None))
        self.Parse_but.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0430\u0440\u0441\u0438\u0442\u044c", None))
        self.Lab.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u043c\u0435\u0440 \u0437\u0430\u043a\u0443\u043f\u043a\u0438", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u041b\u043e\u0433", None))
        self.InputFileBut.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0431\u0440\u0430\u0442\u044c \u0444\u0430\u0439\u043b", None))
        self.OutPutFileBut.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0432", None))
    # retranslateUi

