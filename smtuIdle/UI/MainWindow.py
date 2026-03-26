
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from PySide6 import QtCore
from PySide6 import QtWidgets
from smtuIdle.UI.PurchaseFormular import PurchasesWidget
from smtuIdle.LoadCsv import CsvLoaderWidget
from smtuIdle.statisticWidget import StatisticWidget
from smtuIdle.CurrencyWindow import CurrencyWidget
from smtuIdle.UI.AdminPanel import DebugWidget
from smtuIdle.HelpPanel import HelpPanel
from smtuIdle.UI.ContractFormular import ContractFormularWidget
from smtuIdle.UI.AllDbScroller import PurchasesWidgetAll
from smtuIdle.ChangeLogWindow import ChangeLogWindow
from smtuIdle.statisticWidgetContract import StatisticWidgetContract
from smtuIdle.parserV3 import count_total_records
from smtuIdle.parserV3 import export_to_excel_all
from smtuIdle.BD.models import *
from peewee import JOIN


# from ResultWindow import ResultWindow
# from Viewer import MyWindow
# from Module_start import AuthManager

class Ui_MainWindow(QMainWindow):
    def __init__(self,username):
        super(Ui_MainWindow, self, ).__init__()
        self.auth_window = None  
        self.username = username
        self.widgets = [] 
        self.setupUi()
        # Кнопка создается после setupUi и сразу добавляется в layout главного окна
        self.backButton = QPushButton("← Назад")
        self.backButton.setFixedWidth(120)
        self.backButton.setEnabled(False)  # Сначала выключена, так как истории еще нет
        self.backButton.clicked.connect(self.go_back)

        # Вставляем кнопку в самое начало верхнего меню (index 0)
        self.topLayout.insertWidget(0, self.backButton)
        self.page_history = []
    def setupUi(self):

        style = QStyleFactory.create('Fusion')
        app = QApplication.instance()
        app.setStyle(style)
        self.resize(1680, 960)
       
    
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.topLayout = QtWidgets.QHBoxLayout()
        # Статический виджет в центре

        self.layoutBut = QHBoxLayout()
        self.updateButton = QPushButton("Обновить БД")
        self.updateButton.setFixedWidth(150)
        self.updateButton.clicked.connect(self.GlobalUpdate)
        self.layoutBut.addWidget(self.updateButton)
        self.updateButton.hide()
        self.logoutButton = QPushButton("Выйти")
        self.logoutButton.setFixedWidth(150)
        self.logoutButton.clicked.connect(self.exit)
        self.layoutBut.addWidget(self.logoutButton)
       
    
        self.dbLabel = QtWidgets.QLabel()
        current_date = datetime.now()
        latest_record = ChangedDate.select().order_by(ChangedDate.chenged_time.desc()).first()
        if latest_record:
            # Получаем поле chenged_time из последней записи
            latest_changed_time = latest_record.chenged_time.strftime('%d.%m.%Y %H:%M') 
        
        else:
            latest_changed_time = "17.05.2024"
        self.formatted_date = current_date.strftime("%d-%m-%Y")
        
        user = User.get(User.username == self.username)
        user_roles = UserRole.select().where(UserRole.user == user)
        self.users_roles = [user_role.role.name for user_role in user_roles]
        # Получаем самую раннюю дату
        
        earliest_date = Purchase.select(fn.Min(Purchase.PlacementDate)).scalar()
        if earliest_date:
            erli = earliest_date.strftime('%d.%m.%Y')
        else:
            erli = "Нет данных"
        # Получаем самую позднюю дату
       
        latest_date = Purchase.select(fn.Max(Purchase.PlacementDate)).scalar()
        if latest_date:
            laster = latest_date.strftime('%d.%m.%Y')
        else:
            laster = earliest_date = "Нет данных"
        self.user = f"Пользователь: <b>{self.username}</b>"
        self.role = f"Роль: <b>{self.users_roles[0]}</b>"
        self.date = f"Дата сеанса: <b>{self.formatted_date}</b>"
        self.dateUpdate = f"Дата последнего обновления БД: <b>{latest_changed_time}</b>"
        self.dateLastPurch = f"Данные о закупках с <b>{erli} по {laster} </b>"
        self.totalRecords = f"Закупок в БД:<b> {count_total_records()}</b>"
        self.dbLabel.setText("БАЗА ДАННЫХ ЦЕН И ЭКОНОМИЧЕСКИХ ПОКАЗАТЕЛЕЙ ВЫПОЛНЕНИЯ ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ")

        # Установка максимальной высоты
        self.dbLabel.setFixedWidth(480)
  
        self.dbLabel.setWordWrap(True)
        self.topLayout.addWidget(self.dbLabel)
        self.topLayout.setAlignment(QtCore.Qt.AlignLeft)
        # self.topLayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
       
        self.userLabel = QtWidgets.QLabel()
        self.RolLabel = QtWidgets.QLabel()
        
        self.userLabel.setText(self.user)
        self.RolLabel.setText(self.role)
        # self.rightTopLayout.addWidget(self.dbLabel)
        # self.rightTopLayout.addWidget(self.userLabel)
        # self.rightTopLayout.addWidget(self.RolLabel)
        self.purchaseLabel = QtWidgets.QLabel()
        self.purchaseLabel.setText( self.date)
        self.purchaseLabel2 = QtWidgets.QLabel()
        self.purchaseLabel3 = QtWidgets.QLabel()
        self.purchaseLabel4 = QtWidgets.QLabel()
        self.rightLayout = QVBoxLayout()
        self.rightLayout.addWidget( self.userLabel)
        self.rightLayout.addWidget( self.RolLabel)
        self.rightLayout.addWidget( self.purchaseLabel)
        self.topLayout.addSpacing(20)
        self.topLayout.addLayout(self.rightLayout)
        
        self.rightLayout2 = QVBoxLayout()
        self.purchaseLabel2.setText(self.dateLastPurch)
        self.purchaseLabel3.setText(self.totalRecords)
        self.purchaseLabel4.setText(self.dateUpdate)
        self.rightLayout2.addWidget( self.purchaseLabel2)
        self.rightLayout2.addWidget( self.purchaseLabel3)
        self.rightLayout2.addWidget( self.purchaseLabel4)
        self.topLayout.addSpacing(20)
        self.topLayout.addLayout(self.rightLayout2)
        self.topLayout.addStretch()
        self.topLayout.addLayout(self.layoutBut)
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
        self.leftPanelLayout.addSpacing(20)
        self.pushButton1 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton1.setObjectName("pushButton1")
        self.leftPanelLayout.addWidget(self.pushButton1)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton2.setObjectName("pushButton2")
        self.leftPanelLayout.addWidget(self.pushButton2)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton3.setObjectName("pushButton3")
        self.pushButton8 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton8.setObjectName("pushButton8")
        self.leftPanelLayout.addWidget(self.pushButton8)
        self.leftPanelLayout.addSpacing(20)
        self.leftPanelLayout.addWidget(self.pushButton3)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton9 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton9.setObjectName("pushButton9")
        self.leftPanelLayout.addWidget(self.pushButton9)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton4.setObjectName("pushButton4")
        self.leftPanelLayout.addWidget(self.pushButton4)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton5.setObjectName("pushButton5")
        self.leftPanelLayout.addWidget(self.pushButton5)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton5_1 = QtWidgets.QPushButton(self.centralwidget)
        self.leftPanelLayout.addWidget(self.pushButton5_1)
        self.leftPanelLayout.addSpacing(20)
        
        self.pushButton6 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton6.setObjectName("pushButton6")
        self.leftPanelLayout.addWidget(self.pushButton6)
        self.leftPanelLayout.addSpacing(20)
        self.pushButton7 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton7.setObjectName("pushButton7")
        self.leftPanelLayout.addWidget(self.pushButton7)
        self.leftPanelLayout.addSpacing(20)
        # Задаем фиксированную высоту и максимальное расстояние между кнопками
        button_height = 30  # Задайте желаемую высоту

        self.leftPanelLayout.setAlignment(QtCore.Qt.AlignTop)
        # self.pushButtonParser.setFixedHeight(button_height)
        self.pushButton0.setFixedHeight(button_height)
        self.pushButton1.setFixedHeight(button_height)
        self.pushButton2.setFixedHeight(button_height)
        self.pushButton3.setFixedHeight(button_height)
        self.pushButton4.setFixedHeight(button_height)
        self.pushButton5.setFixedHeight(button_height)
        self.pushButton5_1.setFixedHeight(button_height)
        self.pushButton6.setFixedHeight(button_height)
        self.pushButton7.setFixedHeight(button_height)
        self.pushButton8.setFixedHeight(button_height)
        self.pushButton9.setFixedHeight(button_height)
        # self.pushButtonResult.setFixedHeight(button_height)
        # max_height = 300
        # self.leftPanelFrame.setMaximumHeight(max_height)
   
        # self.pushButtonParser.setIcon(QIcon("Pics/6.png"))
        self.pushButton0.setIcon(QIcon("../Pics/6.png"))
        self.pushButton1.setIcon(QIcon("../Pics/14.png"))
        self.pushButton2.setIcon(QIcon("../Pics/4.png"))
        self.pushButton3.setIcon(QIcon("../Pics/1.png"))
        self.pushButton4.setIcon(QIcon("../Pics/15.png"))
        self.pushButton5.setIcon(QIcon("../Pics/13.png"))
        # self.pushButtonResult.setIcon(QIcon("Pics/13.png"))
        self.pushButton5_1.setIcon(QIcon("../Pics/3.png"))
        self.pushButton6.setIcon(QIcon("../Pics/7.png"))
        self.pushButton7.setIcon(QIcon("../Pics/7.png"))
        self.pushButton8.setIcon(QIcon("../Pics/4.png"))
        self.pushButton9.setIcon(QIcon("../Pics/4.png"))
        # Добавление кнопок в левую часть
        self.horizontalLayout.addLayout(self.leftPanelLayout)
        self.buttons = [
            self.pushButton0, self.pushButton1, self.pushButton2,
            self.pushButton3, self.pushButton4,self.pushButton5_1, self.pushButton6,
            self.pushButton7,self.pushButton8,self.pushButton9, self.pushButton5
        ]
        self.update_button_style_all()

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

        self.page7 = QtWidgets.QWidget()
        self.label7 = QtWidgets.QLabel(self.page7)
        self.stackedWidget.addWidget(self.page7)

        self.page8 = QtWidgets.QWidget()
        self.label8 = QtWidgets.QLabel(self.page8)
        self.stackedWidget.addWidget(self.page8)

        self.page9 = QtWidgets.QWidget()
        self.label9 = QtWidgets.QLabel(self.page9)
        self.stackedWidget.addWidget(self.page9)


        self.page10 = QtWidgets.QWidget()
        self.label10 = QtWidgets.QLabel(self.page10)
        self.stackedWidget.addWidget(self.page10)

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
        self.add_child_widget(self.purchaseViewer)

        self.contractFormular = ContractFormularWidget(self,self.users_roles[0],self.username,self.ChangeWindow)
        self.contractFormular.setParent(self)
        layout = QVBoxLayout(self.page8)
        layout.addWidget(self.contractFormular)
        
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
              #Загрузка виджета статистики контрактов
        self.loadCsvContract = StatisticWidgetContract(self.purchaseViewerall,self.users_roles[0])
        self.loadCsvContract.setParent(self)
        layout = QVBoxLayout(self.page9)
        layout.addWidget(self.loadCsvContract)

        self.helper= HelpPanel()
        self.helper.setParent(self)
        layout = QVBoxLayout(self.page7)
        layout.addWidget(self.helper)


        self.purchaseViewerall.window = self
        self.horizontalLayout.addWidget(self.stackedWidget)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.setCentralWidget(self.centralwidget)
  
        
       
        self.pushButton0.setStyleSheet("background-color: #4CAF50;font-size: 11pt;text-align: left;padding-left: 8px; ")
        self.stackedWidget.currentChanged.connect(self.update_button_style)
        # Подключение сигналов к слотам

        self.pushButton0.clicked.connect(lambda: self.navigate_to_page(0))
        self.pushButton1.clicked.connect(lambda: self.navigate_to_page(1))
        self.pushButton2.clicked.connect(lambda: self.navigate_to_page(2))
        self.pushButton3.clicked.connect(lambda: self.navigate_to_page(3))
        self.pushButton4.clicked.connect(lambda: self.navigate_to_page(4))
        self.pushButton5_1.clicked.connect(lambda: self.navigate_to_page(5))
        self.pushButton6.clicked.connect(lambda: self.navigate_to_page(6))
        self.pushButton7.clicked.connect(lambda: self.navigate_to_page(7))
        self.pushButton8.clicked.connect(lambda: self.navigate_to_page(8))
        self.pushButton9.clicked.connect(lambda: self.navigate_to_page(9))
        self.pushButton5.clicked.connect(self.export_to_excel_all)




        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

        if self.users_roles[0] == "Администратор":
            self.pushButton6.show()
        else:
            self.pushButton6.hide()
        
        if self.users_roles[0] == "Гость" and self.users_roles[0] == "Пользователь" :
            self.pushButton5.hide()
            self.pushButton1.hide()
        else:
            self.pushButton5.show()
            self.pushButton1.show()

    def navigate_to_page(self, index):
        current_index = self.stackedWidget.currentIndex()
        if current_index != index:
            self.page_history.append(current_index)
            self.stackedWidget.setCurrentIndex(index)
            # ОБЯЗАТЕЛЬНО включаем кнопку здесь:
            self.backButton.setEnabled(True)

    def navigate_back(self):
        if self.page_history:
            prev_index = self.page_history.pop()
            self.stackedWidget.setCurrentIndex(prev_index)
        else:
            self.stackedWidget.setCurrentIndex(0)

    def go_back(self):
        if self.page_history:
            prev_index = self.page_history.pop()
            self.stackedWidget.setCurrentIndex(prev_index)
        else:
            self.stackedWidget.setCurrentIndex(0)

        if not self.page_history:
            self.backButton.setEnabled(False)
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "БАЗА ДАННЫХ ЦЕН И ЭКОНОМИЧЕСКИХ ПОКАЗАТЕЛЕЙ ВЫПОЛНЕНИЯ ЗАКЛЮЧЕННЫХ ГОСУДАРСТВЕННЫХ КОНТРАКТОВ НА СТРОИТЕЛЬСТВО СУДОВ"))
        # self.pushButtonParser.setText(_translate("MainWindow", "Парсер"))
        self.pushButton0.setText(_translate("MainWindow", "Просмотр БД"))
        self.pushButton1.setText(_translate("MainWindow", "Ввод данных по закупкам"))
        self.pushButton2.setText(_translate("MainWindow", "Просмотр формуляра закупки"))
        self.pushButton3.setText(_translate("MainWindow", "Статистический анализ закупок"))
        self.pushButton4.setText(_translate("MainWindow", "Валюта"))
        self.pushButton5.setText(_translate("MainWindow", "Экспорт БД НМЦК в Excel"))
        self.pushButton5_1.setText(_translate("MainWindow", "Панель изменений"))
        self.pushButton6.setText(_translate("MainWindow", "Администрирование"))
        self.pushButton7.setText(_translate("MainWindow", "Файлы руководства"))
        # self.pushButtonResult.setText(_translate("MainWindow", "Результаты"))
        self.pushButton8.setText(_translate("MainWindow", "Просмотр формуляра контрактов"))
        self.pushButton9.setText(_translate("MainWindow", "Статистический анализ контрактов"))

    def update_button_style(self, index):
        for i, button in enumerate(self.buttons):
            if i == index:
                button.setStyleSheet("background-color: #4CAF50;font-size: 11pt;text-align: left;padding-left: 8px;")
            else:
                button.setStyleSheet("font-size: 11pt;text-align: left;padding-left: 8px;")

    def update_button_style_all(self):
        for i, button in enumerate(self.buttons):
            button.setStyleSheet("font-size: 11pt;text-align: left;padding-left: 8px;")
    
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
            from smtuIdle.start import AuthWindow
            self.auth_window = AuthWindow()
            self.auth_window.show()
        else:
            pass
            # from start import AuthWindow
            # self.auth_window = AuthWindow()
            # self.auth_window.show()
    def updatePurchaseLabel(self):
        self.user = f"Пользователь: <b>{self.username}</b>"
        self.date = f"Дата сеанса: <b>{self.formatted_date}</b>"
        # self.date = f"Дата сеанса: 17.05.2024"
        self.totalRecords = f"Закупок в БД:<b> {count_total_records()}</b>"
        self.purchaseLabel3.setText(self.totalRecords)
        self.purchaseLabel.setText(self.date)
    def return_variabels(self):
        self.user = f"Пользователь {self.username}"
        self.date = f"Дата сеанса{self.formatted_date}"
        # self.date = f"Дата сеанса: 17.05.2024"
        self.totalRecords = f"Закупок в БД {count_total_records()}"
        return self.totalRecords,self.date, self.user
    
    def add_child_widget(self, widget):
        self.widgets.append(widget)

    def closeEvent(self, event):
        for widget in self.widgets:
            widget.close()
        event.accept()
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
                

                self.data = list(query.tuples())
                records, data, user = self.return_variabels()
                # print(self.data[0])
                if export_to_excel_all(self.data ,f'{selected_file}/Все данные__{data}_{records}_{user}.xlsx') == True:
                    QMessageBox.warning(self, "Успех", "Файл успешно сохранен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка записи")
            else:
                QMessageBox.warning(self, "Предупреждение", "Не выбран файл для сохранения")


    def GlobalUpdate(self):
        self.ChangeWindow.populate_table()
        self.purchaseViewerall.reload_data()
        self.purchaseViewerall.reload_data_cont()
        self.contractFormular.reload_data()
        self.purchaseViewer.reload_data()
        self.Insert.populate_table()
        self.loadCsv.update_table()
        self.loadCsv.update_second_table()
        self.updatePurchaseLabel()
        self.Statistic.update_data()
        self.loadCsvContract.update_data()
        self.ChangeWindow.populate_table()
    # def closeEvent(self, event):
    #     # Вызываем вашу функцию записи лога при закрытии окна
    #     self.write_logout_log()
    #     # Затем закрываем окно
    #     event.accept()
    def write_logout_log(self):
        # Запись лога выхода пользователя при закрытии приложения
        try:
            last_login = UserLog.select().where(UserLog.username == self.username, UserLog.logout_time == None).get()
            last_login.logout_time = datetime.now()
            last_login.save()
        except UserLog.DoesNotExist:
            # Если запись о входе пользователя не найдена, не делаем ничего
            pass
