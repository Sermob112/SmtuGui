from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QFile,QTextStream
from peewee import Model, SqliteDatabase, AutoField, CharField, IntegerField, FloatField, DateField
from playhouse.shortcuts import model_to_dict
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6 import QtCore
from PySide6 import QtWidgets
from DBtest import PurchasesWidget
from LoadCsv import CsvLoaderWidget
from InsertWidgetNMCK import InsertWidgetNMCK
from statisticWidget import StatisticWidget
from CurrencyWindow import CurrencyWidget
from debugWindow import DebugWidget
from AllDbScroller import PurchasesWidgetAll
from ChangeLogWindow import ChangeLogWindow
from parserV3 import count_total_records
from datetime import datetime
from parserV3 import export_to_excel_all
from models import *
from peewee import JOIN

# from Module_start import AuthManager

class Ui_MainWindow(QMainWindow):
    def __init__(self,username):
        super(Ui_MainWindow, self, ).__init__()
        self.auth_window = None  
        self.username = username
        self.setupUi()
    def setupUi(self):

        style = QStyleFactory.create('Fusion')
        app = QApplication.instance()
        app.setStyle(style)
        self.resize(1680, 960)
       
        
        # Установка каскадной таблицы стилей (CSS) для всего приложения
        # file = QFile(":/qdarkstyle/style.qss")
        # file.open(QFile.ReadOnly | QFile.Text)
        # stream = QTextStream(file)
        # app.setStyleSheet(stream.readAll())

        # Главный макет

      
      
    
                # Общий макет
    
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.topLayout = QtWidgets.QHBoxLayout()
        # Статический виджет в центре
        self.centerWidget = QtWidgets.QWidget(self.centralwidget)
        self.centerLayout = QtWidgets.QVBoxLayout(self.centerWidget)
        self.topLayout.addWidget(self.centerWidget)
     
        self.rightTopWidget = QtWidgets.QWidget(self.centralwidget)
        self.rightTopLayout = QtWidgets.QVBoxLayout(self.rightTopWidget)
        # self.rightTopLayoutButton = QtWidgets.QHBoxLayout(self.rightTopWidget)
        # self.rightTopLayoutButton.addWidget(self.logoutButton, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.layoutBut = QHBoxLayout()
        self.logoutButton = QPushButton("Выйти")
        self.logoutButton.setFixedWidth(150)
        self.logoutButton.clicked.connect(self.exit)
       
        self.userLabel = QtWidgets.QLabel(self.rightTopWidget)
        self.RolLabel = QtWidgets.QLabel(self.rightTopWidget)
        self.dbLabel = QtWidgets.QLabel(self.rightTopWidget)
        current_date = datetime.now()
        self.formatted_date = current_date.strftime("%d-%m-%Y")
        self.dbLabel.setText("БАЗА ДАННЫХ ОБОСНОВАНИЙ НАЧАЛЬНЫХ (МАКСИМАЛЬНЫХ) ЦЕН КОНТРАКТОВ И ЦЕН КОНТРАКТОВ, ЗАКЛЮЧАЕМЫХ С ЕДИНСТВЕННЫМ ПОСТАВЩИКОМ, А ТАКЖЕ ЦЕН ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ")
        user = User.get(User.username == self.username)
        user_roles = UserRole.select().where(UserRole.user == user)
        self.users_roles = [user_role.role.name for user_role in user_roles]
        self.user = f"Пользователь: <b>{self.username}</b>"
        self.role = f"Роль: <b>{self.users_roles[0]}</b>"
        self.date = f"Дата: <b>{self.formatted_date}</b>"
        self.totalRecords = f"Закупок в БД:<b> {count_total_records()}</b>"
        
        self.userLabel.setText(self.user)
        self.RolLabel.setText(self.role)
        self.rightTopLayout.addWidget(self.dbLabel)
        self.rightTopLayout.addWidget(self.userLabel)
        self.rightTopLayout.addWidget(self.RolLabel)
        self.purchaseLabel = QtWidgets.QLabel(self.rightTopWidget)
        self.purchaseLabel2 = QtWidgets.QLabel(self.rightTopWidget)
        
       
        self.purchaseLabel.setText( self.totalRecords)
        self.purchaseLabel2.setText(self.date)
        self.updatePurchaseLabel()
        self.rightTopLayout.addWidget(self.purchaseLabel)
        self.rightTopLayout.addWidget(self.purchaseLabel2)
  
        self.topLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.topLayout.addWidget(self.rightTopWidget)
        self.layoutBut.addWidget(self.logoutButton, alignment=QtCore.Qt.AlignRight)
        self.verticalLayout.addLayout( self.layoutBut)
        self.verticalLayout.addLayout(self.topLayout)
         # Добавляем вертикальную разделительную черту внизу
        line = QtWidgets.QFrame(self.centralwidget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout.addWidget(line)
        # Общий макет
        self.horizontalLayout = QtWidgets.QHBoxLayout()

        # Левая панель с кнопками
    
        # self.leftPanelFrame = QtWidgets.QFrame(self.centralwidget)
        self.leftPanelLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.pushButton0 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton0.setObjectName("pushButton0")
        self.leftPanelLayout.addWidget(self.pushButton0)
        
        self.leftPanelLayout.addSpacing(50)
        self.pushButton1 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton1.setObjectName("pushButton1")
        self.leftPanelLayout.addWidget(self.pushButton1)
        
        self.leftPanelLayout.addSpacing(50)
        self.pushButton2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton2.setObjectName("pushButton2")
        self.leftPanelLayout.addWidget(self.pushButton2)
        self.leftPanelLayout.addSpacing(50)
        self.pushButton3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton3.setObjectName("pushButton3")
        self.leftPanelLayout.addWidget(self.pushButton3)
        self.leftPanelLayout.addSpacing(50)
        self.pushButton4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton4.setObjectName("pushButton4")
        self.leftPanelLayout.addWidget(self.pushButton4)
        self.leftPanelLayout.addSpacing(50)
        self.pushButton5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton5.setObjectName("pushButton5")
        self.leftPanelLayout.addWidget(self.pushButton5)
        self.leftPanelLayout.addSpacing(50)
        self.pushButton5_1 = QtWidgets.QPushButton(self.centralwidget)
        self.leftPanelLayout.addWidget(self.pushButton5_1)
        self.leftPanelLayout.addSpacing(50)
        
        self.pushButton6 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton6.setObjectName("pushButton6")
        self.leftPanelLayout.addWidget(self.pushButton6)


  
        # Задаем фиксированную высоту и максимальное расстояние между кнопками
        button_height = 30  # Задайте желаемую высоту

        self.leftPanelLayout.setAlignment(QtCore.Qt.AlignTop)
        self.pushButton0.setFixedHeight(button_height)
        self.pushButton1.setFixedHeight(button_height)
        self.pushButton2.setFixedHeight(button_height)
        self.pushButton3.setFixedHeight(button_height)
        self.pushButton4.setFixedHeight(button_height)
        self.pushButton5.setFixedHeight(button_height)
        self.pushButton5_1.setFixedHeight(button_height)
        self.pushButton6.setFixedHeight(button_height)
        # max_height = 300
        # self.leftPanelFrame.setMaximumHeight(max_height)
   
        
        self.pushButton0.setIcon(QIcon("Pics/6.png"))
        self.pushButton1.setIcon(QIcon("Pics/14.png"))
        self.pushButton2.setIcon(QIcon("Pics/4.png"))
        self.pushButton3.setIcon(QIcon("Pics/1.png"))
        self.pushButton4.setIcon(QIcon("Pics/15.png"))
        self.pushButton5.setIcon(QIcon("Pics/13.png"))
        self.pushButton5_1.setIcon(QIcon("Pics/3.png"))
        self.pushButton6.setIcon(QIcon("Pics/7.png"))
  
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
        self.page0 = QtWidgets.QWidget()
        self.label0 = QtWidgets.QLabel(self.page0)
        self.label0.setGeometry(QtCore.QRect(100, 100, 200, 50))
        self.stackedWidget.addWidget(self.page0)
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
        
        self.page6 = QtWidgets.QWidget()
        self.label6 = QtWidgets.QLabel(self.page6)
        self.stackedWidget.addWidget(self.page6)
        #Загрузка виджета изминений бд
        self.ChangeWindow = ChangeLogWindow(self.users_roles[0])
        self.ChangeWindow.setParent(self)
        layout = QVBoxLayout(self.page5)
        layout.addWidget(self.ChangeWindow)

         #Загрузка виджета БД 
        self.purchaseViewerall = PurchasesWidgetAll(self,self.users_roles[0])
        self.purchaseViewerall.setParent(self)
        layout = QVBoxLayout(self.page0)
        layout.addWidget(self.purchaseViewerall)
        #Загрузка виджета БД закупок
        self.purchaseViewer = PurchasesWidget(self,self.users_roles[0],self.username,self.ChangeWindow)
        self.purchaseViewer.setParent(self)
        layout = QVBoxLayout(self.page2)
        layout.addWidget(self.purchaseViewer)
     
        
        self.Debug = DebugWidget()
        self.Debug.setParent(self)
        layout = QVBoxLayout(self.page6)
        layout.addWidget(self.Debug)
        
        #Загрузка виджета ввод данных валюты
        self.Insert = CurrencyWidget(self.users_roles[0])
        self.Insert.setParent(self)
        layout = QVBoxLayout(self.page4)
        layout.addWidget(self.Insert)
         
            #Загрузка виджета CSV
        self.loadCsv = CsvLoaderWidget(self, self.Insert,self.purchaseViewerall,self.users_roles[0],self.username,self.ChangeWindow )
        self.loadCsv.setParent(self)
        layout = QVBoxLayout(self.page1)
        layout.addWidget(self.loadCsv)
          #Загрузка виджета статистического анализа
        self.Statistic = StatisticWidget(self.purchaseViewerall,self.users_roles[0])
        self.Statistic.setParent(self)
        layout = QVBoxLayout(self.page3)
        layout.addWidget(self.Statistic)

       

        self.purchaseViewerall.window = self
        self.horizontalLayout.addWidget(self.stackedWidget)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.setCentralWidget(self.centralwidget)
        self.buttons = [
            self.pushButton0, self.pushButton1, self.pushButton2,
            self.pushButton3, self.pushButton4,self.pushButton5_1, self.pushButton6,self.pushButton5
        ]
        
       
        self.pushButton0.setStyleSheet("background-color: #4CAF50; color: white;")
        self.stackedWidget.currentChanged.connect(self.update_button_style)
        # Подключение сигналов к слотам
        self.pushButton0.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.pushButton4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        
        self.pushButton5.clicked.connect(self.export_to_excel_all)
        self.pushButton5_1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(5))
        self.pushButton6.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(6))
        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

        if self.users_roles[0] == "Администратор":
            self.pushButton6.show()
        else:
            self.pushButton6.hide()
        
        if self.users_roles[0] == "Гость":
            self.pushButton5.hide()
        else:
            self.pushButton5.show()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "БАЗА ДАННЫХ ОБОСНОВАНИЙ НАЧАЛЬНЫХ (МАКСИМАЛЬНЫХ) ЦЕН КОНТРАКТОВ И ЦЕН КОНТРАКТОВ, ЗАКЛЮЧАЕМЫХ С ЕДИНСТВЕННЫМ ПОСТАВЩИКОМ, А ТАКЖЕ ЦЕН ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ"))
        self.pushButton0.setText(_translate("MainWindow", "Просмотр Формуляра Закупки"))
        self.pushButton1.setText(_translate("MainWindow", "Ввод данных по закупкам"))
        self.pushButton2.setText(_translate("MainWindow", "Просмотр закупок БД"))
        self.pushButton3.setText(_translate("MainWindow", "Статистический анализ"))
        self.pushButton4.setText(_translate("MainWindow", "Валюта"))
        self.pushButton5.setText(_translate("MainWindow", "Экспорт БД НМЦК в Excel"))
        self.pushButton5_1.setText(_translate("MainWindow", "Панель изменений"))
        self.pushButton6.setText(_translate("MainWindow", "Отладка"))
        # self.pushButton1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        # self.pushButton2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        # self.pushButton3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        # self.pushButton4.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        # self.pushButton5.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
    def update_button_style(self, index):
        for i, button in enumerate(self.buttons):
            if i == index:
                button.setStyleSheet("background-color: #4CAF50; color: white;")
            else:
                button.setStyleSheet("")
    
    def exit(self,event):
   
        # Обработка события закрытия главного окна
        reply = QMessageBox()
        reply.setWindowTitle("Предупреждение о выходе") 
        reply.setText("Вы уверены, что хотите выйти из текущей роли?")
        reply.addButton("Нет", QMessageBox.NoRole)
        reply.addButton("Да", QMessageBox.YesRole)
        result = reply.exec()
       

        if result == 1:
            self.write_logout_log()
            self.close()
            from start import AuthWindow
            self.auth_window = AuthWindow()
            self.auth_window.show()
        else:
            pass
            # from start import AuthWindow
            # self.auth_window = AuthWindow()
            # self.auth_window.show()
    def updatePurchaseLabel(self):
        self.user = f"Пользователь: <b>{self.username}</b>"
        self.date = f"Дата: <b>{self.formatted_date}</b>"
        self.totalRecords = f"Закупок в БД:<b> {count_total_records()}</b>"
        self.purchaseLabel.setText(self.totalRecords)
        self.purchaseLabel2.setText(self.date)
    def return_variabels(self):
        self.user = f"Пользователь {self.username}"
        self.date = f"Дата {self.formatted_date}"
        self.totalRecords = f"Закупок в БД {count_total_records()}"
        return self.totalRecords,self.date, self.user
    def export_to_excel_all(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)
        self.purchases = Purchase.select()
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            selected_file = selected_file if selected_file else None
            if selected_file:
                # query1 = self.purchases
                # query = self.purchases.select(Purchase, Contract).join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                query = (
                    self.purchases
                    .select(Purchase.Id, Purchase.PurchaseOrder, Purchase.RegistryNumber, Purchase.ProcurementMethod,
        Purchase.PurchaseName, Purchase.AuctionSubject, Purchase.PurchaseIdentificationCode,
        Purchase.LotNumber, Purchase.LotName, Purchase.InitialMaxContractPrice, Purchase.Currency,
        Purchase.InitialMaxContractPriceInCurrency, Purchase.ContractCurrency,
        Purchase.OKDPClassification, Purchase.OKPDClassification, Purchase.OKPD2Classification,
        Purchase.PositionCode, Purchase.CustomerName, Purchase.ProcurementOrganization,
        Purchase.PlacementDate, Purchase.UpdateDate, Purchase.ProcurementStage,
        Purchase.ProcurementFeatures, Purchase.ApplicationStartDate, Purchase.ApplicationEndDate,
        Purchase.AuctionDate, Purchase.QueryCount, Purchase.ResponseCount, Purchase.AveragePrice,
        Purchase.MinPrice, Purchase.MaxPrice, Purchase.StandardDeviation, Purchase.CoefficientOfVariation,
        Purchase.TKPData, Purchase.NMCKMarket, Purchase.FinancingLimit, Purchase.InitialMaxContractPriceOld,
        Purchase.notification_link,Purchase.quantity_units,Purchase.nmck_per_unit,
        Contract.TotalApplications, Contract.AdmittedApplications, Contract.RejectedApplications,
        Contract.PriceProposal, Contract.Applicant, Contract.Applicant_satatus, Contract.WinnerExecutor,
        Contract.ContractingAuthority, Contract.ContractIdentifier, Contract.RegistryNumber,
        Contract.ContractNumber, Contract.StartDate, Contract.EndDate, Contract.ContractPrice,
        Contract.AdvancePayment, Contract.ReductionNMC, Contract.ReductionNMCPercent,
        Contract.SupplierProtocol, Contract.ContractFile, FinalDetermination.RequestMethod, FinalDetermination.PublicInformationMethod,
        FinalDetermination.NMCObtainedMethods, FinalDetermination.CostMethodNMC,
        FinalDetermination.ComparablePrice, FinalDetermination.NMCMethodsTwo,
        FinalDetermination.CEIComparablePrices, FinalDetermination.CEICostMethod,
        FinalDetermination.CEIMethodsTwo,  CurrencyRate.CurrencyValue, CurrencyRate.CurrentCurrency,
        CurrencyRate.DateValueChanged, CurrencyRate.CurrencyRateDate, CurrencyRate.PreviousCurrency)
                    .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                    .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                    .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                )     
                
                # query = (
                #     self.purchases
                #     .select(Purchase, Contract, FinalDetermination, CurrencyRate)
                #     .join(Contract, JOIN.LEFT_OUTER, on=(Purchase.Id == Contract.purchase))
                #     .join(FinalDetermination, JOIN.LEFT_OUTER, on=(Purchase.Id == FinalDetermination.purchase))
                #     .join(CurrencyRate, JOIN.LEFT_OUTER, on=(Purchase.Id == CurrencyRate.purchase))
                # )     
                self.data = list(query.tuples())
                records, data, user = self.return_variabels()
                # print(self.data[0])
                if export_to_excel_all(self.data ,f'{selected_file}/Все данные__{data}_{records}_{user}.xlsx') == True:
                    QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка записи")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")

    # def closeEvent(self, event):
    #     # Обработка события закрытия главного окна
    #     reply = QMessageBox()
    #     reply.setWindowTitle("Предупреждение о выходе") 
    #     reply.setText("Вы уверены, что хотите закрыть приложение?")
    #     reply.addButton("Нет", QMessageBox.NoRole)
    #     reply.addButton("Да", QMessageBox.YesRole)
    #     result = reply.exec()
       

    #     if result == 1:
    #         self.write_logout_log()
    #         event.accept()
    #     else:
    #         event.ignore()

    def write_logout_log(self):
        # Запись лога выхода пользователя при закрытии приложения
        try:
            last_login = UserLog.select().where(UserLog.username == self.username, UserLog.logout_time == None).get()
            last_login.logout_time = datetime.now()
            last_login.save()
        except UserLog.DoesNotExist:
            # Если запись о входе пользователя не найдена, не делаем ничего
            pass

# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     MainWindow = QtWidgets.QMainWindow()
#     ui = Ui_MainWindow(username="user")
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec())
