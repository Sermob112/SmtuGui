
from PySide6.QtWidgets import QMainWindow, QApplication, QFileDialog
from ui_mainwindow import Ui_MainWindow  # Import the generated UI module
import sys

soup = 0
from Parser import *
from ParserOld import * 

# mass =[ '0187300008423000152', '32110777875', '31704661640', '0117300097419000068', '0373100119818000003', '32008888078', '32110426361', '32110477999', '31908469331', '32110029893', '32312158319', '31300488760', '32110367790', '32009406308', '32009437611', '31604137673', '0373100119819000002', '32211175016', '32009421024', '31908334236', '32009460975', '32009607869', '32110591447', '31400906460', '31908274538', '32110352094', '32110356078', '32110800848', '0373100119819000003', '0851200000614006593', '0851200000614007131', '31603437437', '0373100000217000017', '0373100000217000019', '31705500831', '32009550449', '32009587229', '32110153394', '31908156631', '31705391673', '32110917171', '32110874792', '32009739366', '31807313750', '0345100003720000059', '0345100003720000047', '0345100003720000060', '0345100003720000048', '32211175094', '31806053544', '31603963840', '0365300000815000001', '32009300287', '0335100005614000007', '32008872983', '31603945673', '32110690659', '31705347862', '31907553468', '32009421007', '31705541885', '32009045774', '32009003588', '32110431555', '32110383587', '32110007769', '31704658625', '31300363122', '31300719936', '31401554400', '31401722622', '31502949391', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009517000196', '0173100009516000302', '0173100009516000302', '0173100009516000302', '0173100009516000302', '0173100009516000302', '0173100009516000302', '0173100009516000306', '0173100009516000306', '0173100009516000306', '0173100009516000306', '0173100009516000306', '31502351607', '31502351607', '31806162433', '31806162433', '31401414099', '31401414099', '31503084624', '31503084624', '31503084624', '31503084624', '31503084624', '31503084624', '31502441989', '31502441989', '31300725659', '31300725659', '31300725659', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105598', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31502105596', '31603501055', '31603501055', '31603501055', '31603501055', '31603501055', '31603501055', '31603314524', '31603314524', '31603314524', '31603314524', '31603314524', '31603314524', '31806205504', '31806205504']
# # mass =['32312023607', '31200081551', '31603891359', '31704935501', '0373100119818000001', '0373100119817000007', '31603439928', '31807389642',
# #  '31907934507', '31704765959', '31300737694', '31401318769', '32211736468', '31806221729', '31907875825', '0373100119817000008',
# #  '0373100119817000004', '0373100119817000003', '32211569555', '32009311539', '32211659411', '32110216494', '0173100009519000166', 
# # '31604056957', '31907592925', '31705007151', '0173100009916000013', '31300216922', '31300216926', '31603439942', '0138200001216000001', 
# # '31705166510', '0190200000315008084', '0190200000315009924', '31704767107', '31806159008', '31806805298', '31908729237', '31806158607', 
# #  '31806158148', '31400910520', '32008819026', '31705618760', '32312634394', '0373200068615000061', '31300216916', '31300677102', '31908512667',
# #  '32111007664', '0372200084223000073', '0372200084223000054', '31806975039', '31908218858', '0373100119815000003', '31908372904', 
# #  '0138200003120000001', '0372200084223000078', '0373100112516000020', '31603968852', '0373100112518000004', '32009713614', '32009791222', 
# #  '0124200000614001463', '0372200084223000076', '31806322718', '0372200084223000040', '0373100112516000006', '31300376416', '32008941545', 
# #  '32009060983', '32110507457', '0138200003117000004', '31806752170', '32211062904', '32211101236', '0138300014818000034', '0373100119814000001', 
# #  '32110408671', '32009144139', '32009087829', '32110032742', '0147300002322000014', '31502864350', '31806151849', '31704797897', '32110663522', 
# #  '31908359335', '31705889472', '0373100119814000002', '31401199831', '31300281251', '31807328537', '31806502569', '32211313312', '31705166929', 
# #  '1035600008723000004', '31502679138', '31401206038', '32312494164', '32211657949', '0162200011819002718', '0119300026922000018', '0131200001014002886',
# #   '31806043714', '32009218902', '32110125901', '32009820476', '31502778322', '32009654213', '31503132557', '31907631108', '32009524644', '32009511379', 
# #  '32009417909', '31400922197', '31705132829', '31705157576', '31908595264', '0187300008422000006', '0373100119820000007', '31503106802', '0187300008423000161']
# mass2 = []

class MyWindow(QMainWindow, Ui_MainWindow):  # Inherit from Ui_MainWindow
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)  # Call setupUi to initialize the UI
        self.Parse_but.clicked.connect(self.test)
        self.InputFileBut.clicked.connect(self.open_file_dialog)
        self.OutPutFileBut.clicked.connect(self.open_file_dialog_to_load)
        # self.InputFileBut_2.clicked.connect(self.test_mass)
        # self.new_win_but.clicked.connect(self.new_win)

    def test(self):
        par = Parser()
        parOld = ParserOld()
        if hasattr(self, 'mass') and self.mass is not None:
            for i in self.mass:
                try:
                    par.agent(i, self.folder_path_out)
                    par.parse_head()
                    par.documents(i)
                    par.get_supplier_links(i)
                    par.get_result_contracts(i)
                    # par.Make_Json()
                    par.Make_Dock(i)
                    # tr = par.status_log()
                    # self.textBrowser.append(tr )
                except Exception as e:
                    try:
                        parOld.makeLinkNum(i, self.folder_path_out)
                        parOld.parse_head()
                        parOld.makeDoc()
                        # self.textBrowser.append(f"Ошибка при обработке элемента {i}: {e}")
                    except Exception as e:
                        self.textBrowser.append(f"Не получилось спарсить элемент {i}: {e}")
                        continue
                # else:
                #     continue
        else:
            self.textBrowser.append(f"Выбирите файл для парсинга")
        self.textBrowser.append(f"Закончил парсинг")

    def open_file_dialog(self):
        file_dialog = QFileDialog()
        options = file_dialog.options()
        file_name, _ = file_dialog.getOpenFileName(self, "Выберите файл", "", "All Files (*);;Text Files (*.csv)", options=options)
        if file_name:
            self.FilePathIn.setText(file_name)
            self.mass = self.make_mass(file_name)

    def open_file_dialog_to_load(self):
        file_dialog = QFileDialog()
        options = file_dialog.options()
        self.folder_path_out = file_dialog.getExistingDirectory(self, "Выберите папку", options=options)
        if self.folder_path_out:
            self.FilePathOut.setText(self.folder_path_out)

    def make_mass(self, csv_filename):
        data_from_second_column = []
        # Открываем CSV файл для чтения
        with open(csv_filename, newline='', encoding='cp1251') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            # Пропускаем заголовок, если есть
            next(reader, None)
            # Читаем вторую строку и выбираем вторую часть (индекс 1)
            for row in reader:
                # Проверяем, что строка содержит как минимум два элемента (для второго столбца)
                if len(row) >= 2:
                    # Добавляем элемент второго столбца в массив
                    data_from_second_column.append(row[1].replace("№", ""))
        return data_from_second_column

def application():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    application()



# URL = {'fz223': 'https://zakupki.gov.ru/223/purchase/public/purchase/info/documents.html',
#        'fz44': 'https://zakupki.gov.ru/epz/order/notice/view/documents.html',} # шаблон адреса страницы с документами по закупке
# CONTRACT_URL = {'fz44': 'https://zakupki.gov.ru/epz/contract/search/results.html'}# шаблон адреса страницы с контрактами
# CONTRACT_DOCS_URL = {'fz44': 'https://zakupki.gov.ru/epz/contract/contractCard/document-info.html'}# шаблон адреса страницы с документами по контракту
#
# HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
#                          '(KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
#            'accept': '*/*'}
#
#
# test_url = 'https://zakupki.gov.ru/epz/order/notice/notice223/common-info.html?noticeInfoId=15097592'
# test_url2 = 'https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber=0124200000623001098'
# test_url3 = 'https://zakupki.gov.ru/epz/order/notice/ok20/view/common-info.html?regNumber=0172500000423000006'
# HEADERS_test = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
#                          ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36','accept': '*/*'}
# req = requests.get(test_url, headers= HEADERS_test)
# src = req.text
# req = requests.get(test_url2, headers= HEADERS_test, params= None)
# src = req.text
# print(src)
# req = requests.get(test_url3, headers= HEADERS_test, params= None)
# src = req.text
# with open("index3.html", 'w', encoding="utf-8") as file:
#     file.write(src)
# with open ('index2.html','r', encoding="utf-8") as file:
#     source = file.read()


