# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FilterWindow.ui'
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
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QSizePolicy,
    QStatusBar, QTextEdit, QWidget)

class Ui_FilterWindow(object):
    def setupUi(self, FilterWindow):
        if not FilterWindow.objectName():
            FilterWindow.setObjectName(u"FilterWindow")
        FilterWindow.resize(800, 600)
        self.centralwidget = QWidget(FilterWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.Id = QTextEdit(self.centralwidget)
        self.Id.setObjectName(u"Id")
        self.Id.setGeometry(QRect(30, 80, 341, 31))
        font = QFont()
        font.setFamilies([u"Times New Roman"])
        font.setPointSize(14)
        self.Id.setFont(font)
        self.porchaseOrder = QTextEdit(self.centralwidget)
        self.porchaseOrder.setObjectName(u"porchaseOrder")
        self.porchaseOrder.setGeometry(QRect(30, 160, 341, 31))
        self.porchaseOrder.setFont(font)
        self.RegistryNumber = QTextEdit(self.centralwidget)
        self.RegistryNumber.setObjectName(u"RegistryNumber")
        self.RegistryNumber.setGeometry(QRect(30, 220, 341, 31))
        self.RegistryNumber.setFont(font)
        self.ProcurementMethod = QTextEdit(self.centralwidget)
        self.ProcurementMethod.setObjectName(u"ProcurementMethod")
        self.ProcurementMethod.setGeometry(QRect(30, 280, 341, 31))
        self.ProcurementMethod.setFont(font)
        FilterWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(FilterWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 22))
        FilterWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(FilterWindow)
        self.statusbar.setObjectName(u"statusbar")
        FilterWindow.setStatusBar(self.statusbar)

        self.retranslateUi(FilterWindow)

        QMetaObject.connectSlotsByName(FilterWindow)
    # setupUi

    def retranslateUi(self, FilterWindow):
        FilterWindow.setWindowTitle(QCoreApplication.translate("FilterWindow", u"MainWindow", None))
    # retranslateUi

