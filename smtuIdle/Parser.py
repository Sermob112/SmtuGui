import csv

from bs4 import BeautifulSoup
import requests
import locale
import re

import json
import os
from selenium import webdriver
from docx import Document
class  Parser:
    def __init__(self):
        self.log_data = []
        pass

    def makeLinkNum(self, numer,filePath):
        self.filePath = filePath
    # num = numer
        try:
            search_url = f'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={numer}&morphology=on&search-filter=Дате+размещения&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1'
            # test_url3 = f'https://zakupki.gov.ru/epz/order/notice/ok20/view/common-info.html?regNumber={numer}'
            HEADERS_test = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
                                ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36', 'accept': '*/*'}
            req = requests.get(search_url, headers=HEADERS_test, params=None)
            src = req.text
            soup = BeautifulSoup(src, 'lxml')
            status = 'Успешное подключение'
            col = soup.find('div', class_ = 'registry-entry__header-mid__number')
            a_tag = col.find('a')
            match = re.search(r'noticeInfoId=(\d+)', a_tag['href'])
            link_text = 'https://zakupki.gov.ru/' + a_tag.get('href')
            number = match.group(1)
            self.main_directory = 'Закупка № ' + str(numer) + " "
            self.num = numer
            self.agent(numer = number,filePath = filePath,link = link_text)
            # return  number
        except:
            status = 'Ошибка подключения'
    def agent(self, numer, filePath):
        self.num = numer
        self.filePath = filePath
        try:
            test_url3 = f'https://zakupki.gov.ru/epz/order/notice/ok20/view/common-info.html?regNumber={numer}'
            test_url2 = f'https://zakupki.gov.ru/epz/order/notice/notice223/common-info.html?noticeInfoId={numer}'
            self.HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
                              ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36', 'accept': '*/*'}

            req = requests.get(test_url3, headers=self.HEADERS, params=None)
            src = req.text
            self.soup = BeautifulSoup(src, 'lxml')
            self.status = 'Успешное подключение'
            return self.soup
        except:
            self.status = 'Ошибка подключения'

    ##############################################################################################################
    #основная информация
    ######################################################
    #Серийный номер

    def parse_head(self ):

        mass = []
        serial_date = {}
        serial_number = self.soup.find(class_="registry-entry__header-mid__number")
        name = self.soup.find(class_='cardMainInfo__content').get_text().strip().replace('"','').replace('\r','')[:60].replace(' ', '_').replace('\n','')
        self.object_name = f' {name}'
        try:
            if serial_number != None:
                serial_number = self.soup.find(class_="registry-entry__header-mid__number").find('a').text.strip()
            else:
                serial_number = self.soup.find('a', {'class': 'distancedText'})
                regNumber = serial_number['href'].split('=')[1]
                status_text = self.soup.find(class_= 'cardMainInfo__state distancedText').get_text().strip()
                mass.append({regNumber:status_text})
                self.main_directory = 'Закупка № ' + str(regNumber)

        #####Сведенья о закупке###########################
            svedenia_o_zakupke = []
            zakupchik = self.soup.find(class_ = 'registry-entry__body')
            if zakupchik != None:
                zakupchik = self.soup.find(class_ = 'registry-entry__body').find_all(class_ = 'registry-entry__body-block')
                for i in zakupchik:
                    object_zak = i.find(class_ = 'registry-entry__body-title').text.strip()
                    zakazchic = i.find(class_ = 'registry-entry__body-value').text.strip()
                    svedenia_o_zakupke.append({object_zak: zakazchic})
                    a_tag = i.find('a')
                    if a_tag == None:
                        continue
                    else:
                        link = 'https://zakupki.gov.ru' + a_tag["href"]
                    svedenia_o_zakupke.append({object_zak: zakazchic, 'ссылка на огранизацию': link})
            else:
                zakupchik = self.soup.find(class_='sectionMainInfo__body').find_all(class_='cardMainInfo__section')
                for i in zakupchik:
                    object_zak = i.find(class_='cardMainInfo__title').text.strip()
                    zakazchic = i.find(class_='cardMainInfo__content').text.strip()
                    
                    svedenia_o_zakupke.append({object_zak: zakazchic})
                    a_tag = i.find('a')
                    if a_tag == None:
                        continue
                    else:
                        link = 'https://zakupki.gov.ru' + a_tag["href"]
                    mass.append({object_zak:zakazchic, 'ссылка на огранизацию':link})
                mass.append(svedenia_o_zakupke)

            # link = a_tag["href"]


        #######################################
        #Сведенья о закупе (начальная цена и пр)
        ####Начальная цена
            priece_info = []
            price = self.soup.find(class_ = 'price-block')
            locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
            if price != None:
                price = self.soup.find(class_ = 'price-block').find_all('div')
                for i in price:
                    title = i.text
            else:
                price = self.soup.find(class_='sectionMainInfo borderRight col-3 colSpaceBetween').find_all('span')
                for i in price:
                    title = i.text.strip()
                    if '\xa0' in title:
                        title = title.replace('\xa0', '')  # remove non-breaking spaces
                        title = title.replace(',', '.')  # replace comma with dot
                    priece_info.append(title)
            result = []
            for i in range(0, len(priece_info), 2):
                key = priece_info[i]
                value = priece_info[i+1] if i+1 < len(priece_info) else ''
                # result.append({key: value})
                mass.append({key: value})
                serial_date['Номер заказа'] = mass
            self.status = 'Успешный парсинг заголовка'
            return serial_date
        except Exception:
                self.status = 'Произошла ошибка с парсингом заголовка'





    # ###########################################################################################################
    # #Парсинг всех ссылок на информацию
    def all_link(self):
        tabs_of_links = {}
        link_razdels = self.soup.find(class_ = 'tabsNav d-flex align-items-end')
        if link_razdels != None:
            try:
                link_razdels = self.soup.find(class_ = 'tabsNav d-flex').find_all('a')
                for links in link_razdels:
                    linkl = 'https://zakupki.gov.ru/' + links.get('href')
                    title_razde = links.text.strip()
                    tabs_of_links[title_razde] = linkl
                    # tabs_of_links.append({title_razde:linkl})
            except Exception:
                link_razdels = self.soup.find(class_='tabsNav d-flex align-items-end').find_all('a')
                for links in link_razdels:
                    linkl = 'https://zakupki.gov.ru/' + links.get('href')
                    title_razde = links.text.strip()
                    tabs_of_links[title_razde] = linkl
            return tabs_of_links
    # print(all_link())
    # ##################################################################################
    #Парсинг сведений о закупке
    def main_info_body(self,soup):
        main_infp = soup.find_all(class_ ='common-text b-bottom pb-3')
        list_info = []
        all_table_info = []
        data_td = []
        block_title = []
        new_dict = {}
        table_info = []
        try:
            if len(main_infp) != 0:
            # title_cap = soup.find(class_= 'common-text__caption').text.strip()
            # print(title_cap)
                for info in main_infp:
                    #весь текст
                    # zagolovok = info.text.strip()
                    col_9 = info.find_all(class_='col-9 mr-auto')
                    title_cap = info.find(class_='common-text__caption').text.strip()
                    list_info.append({title_cap})
                    for values in col_9:
                        # title_cap = info.find(class_='common-text__caption')

                        title_text = values.find(class_= 'common-text__title')
                        value_text = values.find(class_= 'common-text__value')
                        if (title_text == None  or value_text == None):
                            continue
                        else:
                            title_text = values.find(class_='common-text__title').text.strip()
                            value_text = values.find(class_='common-text__value').text.strip()
                        list_info.append({title_text:value_text})


            else:
                b = 0
                n = 0
                main_infp = soup.find_all(class_='row blockInfo')
                for info in main_infp:
                    # col_9 = info.find_all(class_='blockInfo__section section')
                    col_9 = info.find_all(class_='blockInfo__section')
                    title_cap = info.find(class_='blockInfo__title').get_text().strip()
                    block_title.append(title_cap)
                    for values in col_9:
                        title_text = values.find(class_='section__title')
                        value_text = values.find(class_='section__info')
                        if (title_text == None  or value_text == None):
                            continue
                        else:
                            title_text = values.find(class_='section__title').get_text().strip()
                            value_text = values.find(class_='section__info').get_text().strip()
                            if '\n' in title_text or '\n' in value_text:
                                title_text = title_text.replace('\n', '')  # remove non-breaking spaces
                                value_text = value_text.replace('\n', '')
                            if ' ' in value_text:
                                value_text = value_text.replace(' ', '')  # remove non-breaking spaces
                            list_info.append({title_text:value_text})

                    table = info.find_all(class_ ='blockInfo__table tableBlock')
                    if table != None:
                        for tables in table:
                            # table = info.find(class_='blockInfo__table tableBlock')
                            hiegth_row = tables.find_all('th')
                            table_td = tables.find_all('td')

                            for i in hiegth_row:
                                column_name = i.text.strip()
                                all_table_info.append(column_name)

                            for i in table_td:
                                td = i.get_text().strip()
                                if(td == ''):
                                    continue
                                if '\n' in td:
                                    td = td.replace('\n', '') # remove non-breaking spaces
                                    td = re.findall('[A-ZА-Я][^A-ZА-Я]*', td)
                                if '\xa0' in td:
                                    td = td.replace('\xa0', '').replace(',', '.')   # remove non-breaking spaces

                                data_td.append(td)
                                try:
                                    list_info.append({all_table_info[n]:td})
                                except IndexError:
                                    # continue
                                    n = 0
                                    list_info.append({all_table_info[n]: td})
                                n = n + 1
                    new_dict[title_cap] = list_info
                    list_info = []
                    b = b + 1
                # return data_td
            self.status = 'успешный парсинг Общей информации'
            return new_dict
        except Exception:
            self.status = 'Общая информация ошибка парсинга'


    # print(main_info_body())
    #############################################################################################
    #Выподающая страница
    ##############################################################################################
    def collapse_element(self,soup):
        i = 0
        j = 0
        collaps_titles  = []
        collaps_main_title_mass = []
        cont_main_title_mass = []
        th_mass = []
        titls_table_main = []
        collaps_main = []
        collaps_data = {}
        conteiner_text = []
        table_data = {}
        conteiner_titls_data = {}
        fgh = 0
        collaps_content = soup.find_all( 'div', class_ = 'blockInfo__collapse collapseInfo')
        try:
            if collaps_content != None:
                for infos in collaps_content:
                    collaps_title = infos.find( class_ = 'collapse__title_text').get_text()
                    collaps_title = collaps_title.replace('\n', '').replace('\xa0', ' ')
                    collaps_titles.append(collaps_title)
                    content_block_info  = infos.find_all('div', class_="content__block blockInfo")
                    collaps_data[0] = collaps_title
                    for item in content_block_info:

                        block_info_title = item.find( class_ = 'blockInfo__title').get_text()
                        collaps_titles.append(block_info_title)
                        block_sec_title = item.find_all(class_='section__title')
                        for its in block_sec_title:
                            collaps_main_title_mass.append(its.get_text().replace('\n', ''))
                        block_sec_info = item.find_all(class_='section__info')
                        for it in block_sec_info:
                            # block_sec_info_mass.append(it.get_text().replace('\n', '').replace('\xa0', ' '))
                            try:
                                collaps_main.append(
                                    {collaps_main_title_mass[fgh]: it.get_text().replace('\n', '').replace('\xa0', ' ')})
                            except IndexError:
                                collaps_main.append({'': it.get_text().replace('\n', '').replace('\xa0', ' ')})
                            fgh = fgh +1

                        collaps_data[block_info_title] = collaps_main
                        collaps_main = []
                    #####парсинг таблицы
                    conteiner_table= infos.find_all('div', class_="container")
                    if conteiner_table != None:
                        conteiner_table = infos.find_all('div', class_="container")

                        ###################################################
                        #Парсинг значений таблицы
                        for tb in conteiner_table:
                            # может быть несколько тайтлов\ пока только один
                            row_block_info = tb.find_all(class_ = 'row blockInfo')
                            for rower in row_block_info:
                                tit = rower.find(class_ = 'blockInfo__title').get_text().strip()

                            block_info = tb.find_all(class_='blockInfo__section')
                            for bs in block_info:
                                cont_sec_title = bs.find_all(class_='section__title')
                                for its in cont_sec_title:
                                    cont_main_title_mass.append(its.get_text().strip().replace('\n', ''))
                                cont_sec_info = bs.find_all(class_='section__info')
                                for its in cont_sec_info:
                                    try:
                                        titls_table_main.append(
                                            {cont_main_title_mass[j]: its.get_text().replace('\n', '').replace('\xa0',
                                                                                                               ' ').strip()})
                                    except IndexError:
                                        titls_table_main.append(
                                            {'': its.get_text().replace('\n', '').replace('\xa0', ' ').strip()})

                                    j = j + 1
                                conteiner_titls_data[tit] = titls_table_main
                            t = j
                            #Поиск всех элементов таблицы
                            tablos = tb.find_all('table')
                            for tbn in tablos:
                                c_th = tbn.find_all('th')
                                for th_items in c_th:
                                    th_text = th_items.get_text().strip()
                                    th_mass.append(th_text)

                                c_td = tbn.find_all('td')
                                for td_items in c_td:
                                    td_text = td_items.get_text().strip()
                                    try:
                                        conteiner_text.append({th_mass[i]: td_text})
                                    except Exception:
                                        i = 0
                                        conteiner_text.append({'': td_text})
                                    i += 1

                                table_data[cont_main_title_mass[t]] = conteiner_text
                                t = t + 1
                                conteiner_text = []
                collaps_data.update(conteiner_titls_data)
                collaps_data.update(table_data)

            self.status = 'успешный парсинг выпадающих элементов'
            return collaps_data
        except Exception:
            self.status = 'Произошла ошибка с парсингом Выпадающих элементов'



    def documents(self, num):
        block_info_title = []
        infos = []
        sec_attrib = []
        sec_value = []
        col_data = []
        data= {}
        font = []
        files_links = {}
        i = 0
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
                          ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36', 'accept': '*/*'}
        link = f'https://zakupki.gov.ru/epz/order/notice/ea20/view/documents.html?regNumber={num}'
        req = requests.get(url=link, headers=HEADERS)
        src = req.text
        soup = BeautifulSoup(src, "lxml")
        try:
            col_sm_12 = soup.find_all(class_ ='col-sm-12 blockInfo')
            for col in col_sm_12:
                titles = col.find(class_='blockInfo__title').get_text().strip()
                block_info_title.append(titles)

                try:
                    section_value = col.find_all(class_='section__value docName')
                    for sec in section_value:
                        infos.append(sec.get_text().strip())

                    #######################LINKS##########################
                    link_of_files = col.find_all(class_='blockFilesTabDocs')
                    for lux in link_of_files:
                        luxit = lux.find_all('a')
                        try:
                            for links in luxit:
                                if 'download' in links.get('href') or 'file' in links.get('href'):
                                    linkl = links.get('href')
                                    titk = links.get('title')
                                    files_links[titk] = linkl
                            if len(files_links) > 0:
                                try:
                                    # path = os.path.join(self.main_directory, titles)
                                    os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{titles}', exist_ok=True)
                                    # os.makedirs(path)
                                except Exception:
                                    pass
                                for title, url in files_links.items():
                                    response = requests.get(url, headers=self.HEADERS)
                                    with open(f'{self.filePath}/{self.main_directory + self.object_name}/{titles}/{title}', "wb") as f:
                                        f.write(response.content)
                                files_links = {}
                        except Exception as e:
                            print(e)
                            if len(files_links) > 0:
                                # if not os.path.exists(self.main_directory):
                                # path = os.path.join(self.main_directory, titles)
                                # os.makedirs(path)
                                os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{titles}', exist_ok=True)
                                for title, url in files_links.items():
                                    response = requests.get(url, headers=self.HEADERS)
                                    with open(f'{self.filePath}/{self.main_directory + self.object_name}/{titles}/{title}', "wb") as f:
                                        f.write(response.content)
                                files_links = {}

                    #############################################################
                    col_sm = col.find_all(class_='col-sm')
                    for col_12 in col_sm:
                        sec_values = col_12.find_all(class_='section__value')
                        for val in sec_values:
                            sec_value.append(val.get_text().strip())
                        sec_attributs = col_12.find_all(class_='section__attrib')
                        for col_12 in sec_attributs:
                            try:
                                sec_attrib.append(col_12.get_text().strip().replace('\n', ''))
                                i = i + 1
                            except Exception:
                                i = 0
                                sec_attrib.append(col_12.get_text().strip().replace('\n', ''))
                    front = col.find_all('div', attrs={'style': 'font-size: 14px'})
                    if len(front) > 0:
                        for f in front:
                            font.append(f.get_text().strip())

                    if len(col_sm) == 0:
                        perm = col.find(class_='section__title').get_text().strip()
                        # font = []
                        sec_attrib.append(perm)

                    infos.append(sec_attrib)
                    infos.append(font)
                    data[titles] = infos
                    infos = []
                    font = []
                    sec_value = []
                    sec_attrib = []

                except Exception:
                    pass
                    sec_titl = col.find_all(class_ = 'section__title')
                    for ttl in sec_titl:
                        col_data.append(ttl.get_text().strip())
                    data[titles] = col_data
                    infos = []
                    sec_value = []
                    col_data = []

            self.status = 'успешный парсинг Документов'

        except Exception:
            self.status = 'Ошибка парсинга Документов'

        # return block_info_title
        return data


    def journal_of_events(self,link):

        th_mass = []
        data = []
        fn_date= {}
        i = 0
        driver = webdriver.Chrome()
        driver.get(link)
        import time
        time.sleep(0)
        html = driver.page_source

        soup = BeautifulSoup(html, 'lxml')

        driver.quit()
        wrapper = soup.find_all( class_='table mb-0 displaytagTable')
        #не нашел журнал событий
        try:
            for tbn in wrapper:
                c_th = tbn.find_all('th')
                for th_items in c_th:
                    th_text = th_items.get_text().strip()
                    th_mass.append(th_text)

                c_td = tbn.find_all('td')
                for td_items in c_td:
                    td_text = td_items.get_text().strip()
                    try:
                        data.append({th_mass[i]: td_text})
                    except Exception:
                        i = 0
                        data.append({th_mass[i]: td_text})
                    i += 1
            self.status = 'Успешный парсинг Журнала'
            return data

        except Exception:
            self.status = 'Ошибка парснига  Журнала'

    def supplier_result(self, link):
        block_title = []
        title_data = []
        value_data = []
        list_info = []
        zakazchic_data = []
        table_titles = []
        all_table_info = []
        doc_titles = []
        data = {}
        i = 0
        n = 0
        # row_info = soup.find_all(class_= 'row blockInfo')
        # for info in row_info:
        driver = webdriver.Chrome()
        driver.get(link)
        import time
        time.sleep(0)
        html = driver.page_source

        soup = BeautifulSoup(html, 'lxml')

        driver.quit()

        col_9 = soup.find_all(class_='row blockInfo')

        for col in col_9:
            title_cap = col.find(class_='blockInfo__title').get_text().strip()

            # td_text = info.find('td',class_='tableBlock__col').get_text().strip()
            #
            # value_text = 'None'
            # title_text = 'None'

            block_section = col.find_all('section', class_="blockInfo__section section")
            for inf in block_section:
                title_text = inf.find(class_='section__title').get_text().strip()
                try:
                    title_value = inf.find(class_='section__info').get_text().strip()
                    value_data.append({title_text: title_value})
                except  Exception:
                    value_data.append({title_text: ''})
            ##Заказчик(и), с которыми планируется заключить контракт
            try:
                th = col.find('th', class_="tableBlock__col tableBlock__col_header").get_text().strip()
                td = col.find('td', class_='tableBlock__col').get_text().strip()
                zakazchic_data.append({th: td})
                zac = zakazchic_data[0]

            except Exception:
                None

            try:
                table_sup = col.find_all(class_='blockInfo__table tableBlock')
                if len(table_sup) > 1:
                    second_element = table_sup[1]
                    table_tr = second_element.find_all(class_='tableBlock__col tableBlock__col_header')
                    for th in table_tr:
                        table_titles.append(th.get_text().strip())
                    table_td = second_element.find_all(class_='tableBlock__body')
                    for row in table_td:
                        try:
                            table_td_row = row.find_all(class_='tableBlock__col')
                            for th in table_td_row:
                                try:
                                    all_table_info.append({table_titles[n].replace('\n', '').replace(' ',
                                                                                                     ''): th.get_text().strip().replace(
                                        '\n', '').replace(' ', '')})
                                except Exception:
                                    n = 0
                                    all_table_info.append({table_titles[n].replace('\n', '').replace(' ',
                                                                                                     ''): th.get_text().strip().replace(
                                        '\n', '').replace(' ', '')})
                                n = n + 1
                        except Exception:
                            None
                    value_data.append(all_table_info)
                    all_table_info = []

                # Дальнейшие таблицы
                else:
                    table_tr = col.find_all(class_='tableBlock__col tableBlock__col_header')
                    for th in table_tr:
                        table_titles.append(th.get_text().strip())
                    table_td = col.find_all(class_='tableBlock__body')
                    for row in table_td:
                        try:
                            table_td_row = row.find_all(class_='tableBlock__col')
                            for th in table_td_row:
                                try:
                                    all_table_info.append({table_titles[n].replace('\n', '').replace(' ',
                                                                                                     ''): th.get_text().strip().replace(
                                        '\n', '').replace(' ', '')})
                                except Exception:
                                    n = 0
                                    all_table_info.append({table_titles[n].replace('\n', '').replace(' ',
                                                                                                     ''): th.get_text().strip().replace(
                                        '\n', '').replace(' ', '')})
                                n = n + 1
                        except Exception:
                            None
                    value_data.append(all_table_info)
                    all_table_info = []


            except Exception:
                None
            value_data.append(zac)
            # value_data.append(all_table_info)
            data[title_cap] = value_data
            value_data = []
            zac = []
            zakazchic_data = []
        return data

    # print(journal_of_events())
    def other_info(self):
        data = {}
        i = 0
        HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
                              ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36', 'accept': '*/*'}
        linkers = self.all_link()

        for title, link in linkers.items():
            req = requests.get(url=link, headers=HEADERS)
            src = req.text
            soup = BeautifulSoup(src, "lxml")
            try:
                # def docs():
                #     data[title] = self.documents(soup)
                # def jorns():
                #     data[title] = self.journal_of_events(link)
                #
                # options = {
                #     'Документы': docs(),
                #     'Журнал событий': jorns()
                #
                # }
                # options.get(title)()

                if len(self.main_info_body(soup)) < 0:
                    data[title] = self.main_info_body(soup)
                elif title == 'Документы':
                    data[title] = self.documents(soup)
                elif title == 'Результаты определения поставщика (подрядчика, исполнителя)':
                    # data[title] = self.supplier_result(link)
                    self.supplier_docs()   
                # elif len(self.journal_of_events(link))> 0:
                elif title == 'Журнал событий':
                    data[title] = self.journal_of_events(link)
                else:
                    pass
            except Exception:
               print(f"Ошибка в этой части {title}")

        return data


    

        


    def GetAllDocks(self):
        data = {}
        i = 0
        # HEADERS = {
        #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0'
        #                         ' YaBrowser/23.3.0.2246 Yowser/2.5 Safari/537.36', 'accept': '*/*'}
        linkers = self.all_link()

        for title, link in linkers.items():
            test = 0
            # req = requests.get(url=link, headers=self.HEADERS)
            # src = req.text
            # soup = BeautifulSoup(src, "lxml")
            try:
                # def docs():
                #     data[title] = self.documents(soup)
                # def jorns():
                #     data[title] = self.journal_of_events(link)
                #
                # options = {
                #     'Документы': docs(),
                #     'Журнал событий': jorns()
                #
                # }
                # options.get(title)()

                # if len(self.main_info_body(soup)) < 0:
                #     data[title] = self.main_info_body(soup)
                # elif title == 'Документы':
                #     data[title] = self.documents(soup)
                if title == 'Результаты определения поставщика':
                    # data[title] = self.supplier_result(link)
                    test = self.get_supplier_docs(link)
                # elif len(self.journal_of_events(link))> 0:
                # elif title == 'Журнал событий':
                #     data[title] = self.journal_of_events(link)
                else:
                    pass
            except Exception:
                print(f"Ошибка в этой части {title}")

        # return data
        return test

    def get_supplier_links(self,num):
        link_mass = []
        link = f'https://zakupki.gov.ru/epz/order/notice/ok20/view/supplier-results.html?regNumber={num}'
        req = requests.get(url=link, headers=self.HEADERS)
        src = req.text
        soup = BeautifulSoup(src, "lxml")
        rows = soup.find_all(class_='row blockInfo')
        for i in rows:
            a = i.find_all('a')
            for j in a:
                try:
                    substring1 = 'https://zakupki.gov.ru/epz/order/notice/ok20/view/protocol/protocol-main-info.html?'
                    substring2 = 'https://zakupki.gov.ru/epz/contract/contractCard/common-info.html?'
                    substring3 = 'https://zakupki.gov.ru/epz/rdik/card/info.html?'
                    link = 'https://zakupki.gov.ru' + j.get('href')
                    # self.get_result_contracts(num)
                    if substring1 in link:
                        link = link.replace('protocol-main-info.html', 'protocol-docs.html')
                        
                        self.get_supplier_docs(link)
                    if substring2 in link:
                        link = link.replace('common-info.html', 'document-info.html')
                        self.get_contract_details(link)
                    if substring3 in link:
                        self.get_electronic_documents(link)

                    link_mass.append(link)
                except:
                    continue
        # if  link_mass:
        #     for i in link_mass:
        #         try:
        #             self.get_electronic_documents(i)
        #         except Exception as e3:
        #             print(f'Ошибка в self.get_electronic_documents для {i}: {e3}')
        #             # Если нужно прервать выполнение после всех ошибок
        #             continue
                

        # linkl = 'https://zakupki.gov.ru/' + links.get('href')
        # link_element = soup.find_all('a')
        # if link_element:
        #     link = link_element.get('href')
        #     link_mass.append(link)
        return link_mass
    
    def get_supplier_docs(self, link):
        req = requests.get(url=link, headers=self.HEADERS)
        src = req.text
        soup = BeautifulSoup(src, "lxml")
        row_block_info= soup.find_all(class_='row blockInfo')
        for laxir in row_block_info:
            title = laxir.find(class_='blockInfo__title')
            title_text = title.get_text().strip()
            luxit = laxir.find_all('a')
            try:
                for links in luxit:
                    # href = links.get('href')
                    if 'download' in links.get('href') or 'file' in links.get('href'):
                            linkl = links.get('href')
                            titk = links.get_text().strip()
                            self.downloader(linkl,title_text)
                            response = requests.get(f'{linkl}', headers=self.HEADERS)
                            if response.status_code == 200:
                                os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}', exist_ok=True)   
                                with open(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}/{titk}', "wb") as f:
                                    f.write(response.content)
                            else:
                                print(f"Не удалось скачать файл: {linkl}")
            except Exception as e:
                print(f"Произошла ошибка: {str(e)}")
                continue

    def downloader(self,linkl,title_text,titk):
        response = requests.get(f'{linkl}', headers=self.HEADERS)
        if response.status_code == 200:
            os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}', exist_ok=True)   
            with open(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}/{titk}', "wb") as f:
                f.write(response.content)
        else:
            print(f"Не удалось скачать файл: {linkl}")
    


    def get_result_contracts(self, num):
        link = f'https://zakupki.gov.ru/epz/order/notice/rpec/documents.html?regNumber={num}0001'
        req = requests.get(link, headers=self.HEADERS, params=None)
        src = req.text
        soup = BeautifulSoup(src, 'lxml')
        findTitle = soup.find_all(class_='col-sm-12 blockInfo')
        for titles in findTitle:
            title = titles.find(class_='blockInfo__title')
            if title:
                title_text = title.get_text().strip()
                values = titles.find_all(class_='blockFilesTabDocs')
                for laxir in values:
                    luxit = laxir.find_all('a')
                    try:
                        for links in luxit:
                            # href = links.get('href')
                            if 'download' in links.get('href') or 'file' in links.get('href'):
                                    linkl = links.get('href')
                                    titk = links.get('title')
                                    response = requests.get(f'{linkl}', headers=self.HEADERS)
                                    if response.status_code == 200:
                                        os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}', exist_ok=True)   
                                        with open(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}/{titk}', "wb") as f:
                                            f.write(response.content)
                                    else:
                                        print(f"Не удалось скачать файл: {linkl}")
                    except Exception as e:
                        print(f"Произошла ошибка: {str(e)}")
                        continue

    def get_contract_details(self, link):
        req = requests.get(url=link, headers=self.HEADERS)
        src = req.text
        soup = BeautifulSoup(src, "lxml")
        cart = soup.find(class_='card-attachments')
        findTitle = cart.find_all(class_='container card-attachments-container')
        for titles in findTitle:
            title = titles.find(class_='title pb-0')
            title_text = title.get_text().strip()
            values = titles.find_all(class_='col-12')
            for laxir in values:
                luxit = laxir.find_all('a')
                try:
                    for links in luxit:
                        # href = links.get('href')
                        if 'download' in links.get('href') or 'file' in links.get('href'):
                                linkl = links.get('href')
                                titk = links.get('title')
                                # file_type_pattern = r'\.\w+'
                                # cleaned_titk = re.sub(file_type_pattern, '', titk)
                                new_titk = re.sub(r'\s*\([^)]*\)', '', titk)
                                # titk = links.get_text().replace("\n","").replace(" ","")
                                response = requests.get(f'{linkl}', headers=self.HEADERS)
                                if response.status_code == 200:
                                    os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}', exist_ok=True)   
                                    with open(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}/{new_titk}', "wb") as f:
                                        f.write(response.content)
                                else:
                                    print(f"Не удалось скачать файл: {linkl}")
                except Exception as e:
                    print(f"Произошла ошибка: {str(e)}")
                    continue

    def get_electronic_documents(self, link):
        req = requests.get(url=link, headers=self.HEADERS)
        src = req.text
        soup = BeautifulSoup(src, "lxml")

        findTitle = soup.find_all(class_='block-lot card-attachments__block')
        for titles in findTitle:
            title = titles.find(class_='title pb-0')
            title_text = title.get_text().strip()
            values = titles.find_all(class_='col-12')
            for laxir in values:
                luxit = laxir.find_all('a')
                try:
                    for links in luxit:
                        # href = links.get('href')
                        if 'download' in links.get('href') or 'file' in links.get('href'):
                                linkl = links.get('href')
                                titk = links.get_text()
                                response = requests.get(f'{linkl}', headers=self.HEADERS)
                                if response.status_code == 200:
                                    os.makedirs(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}', exist_ok=True)   
                                    with open(f'{self.filePath}/{self.main_directory + self.object_name}/{title_text}/{titk}', "wb") as f:
                                        f.write(response.content)
                                else:
                                    print(f"Не удалось скачать файл: {linkl}")
                except Exception as e:
                    print(f"Произошла ошибка: {str(e)}")
                    continue


    def Test_Json(self):
        with open(f"{self.main_directory}/all_docs.json", "a", encoding="utf-8") as file:
            json.dump(self.other_info(), file, indent=4, ensure_ascii=False)
    # Test_Json()
    #######################################################################

    #########################################################################
    #JSON#####
    def status_log(self):
         self.log_data.append(self.status)
         return self.log_data
    def Make_Json(self):
        global_dict = {}
        global_dict.update(self.parse_head())
        self.status_log()
        global_dict.update(self.main_info_body(self.soup))
        self.status_log()
        global_dict.update(self.collapse_element(self.soup))
        self.status_log()
        global_dict.update(self.other_info())
        self.status_log()
        # global_dict.update(self.documents(self.soup))
        try:
            with open(f"{self.filePath}/{self.main_directory}/Все данные закупки №{self.num}.json", "a", encoding="utf-8") as file:
                json.dump(global_dict, file, indent=4, ensure_ascii=False)
            self.status = 'Успешная запись файлов'
        except Exception:
            self.status = 'Ошибка записи файлов'
        self.status_log()

    def Make_Dock(self,num):
        global_dict = {}
        global_dict.update(self.parse_head())
        self.status_log()

       
        global_dict.update(self.main_info_body(self.soup))
        self.status_log()
        global_dict.update(self.collapse_element(self.soup))
        self.status_log()
        global_dict.update(self.documents(num))
        global_dict.update(self.other_info())
        
        try:
            doc = Document()
            # for item in global_dict:
            #     doc.add_paragraph(item)
            # doc.save(f"{self.main_directory}/Все данные о закупке №{self.num}.docx")
            # Добавляем заголовок
            doc.add_heading('Данные о закупке', level=1)

# Перебираем данные и добавляем их в документ
            for key, value in global_dict.items():
                doc.add_heading(key, level=2)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for sub_key, sub_value in item.items():
                                doc.add_paragraph(f'{sub_key}: {sub_value}')
                        else:
                            doc.add_paragraph(str(item))
                else:
                    doc.add_paragraph(str(value))
            doc.save(f"{self.filePath}/{self.main_directory + self.object_name}/Все данные о закупке №{self.num}.docx")
            self.status = 'Успешная запись файлов'
        except Exception:
            self.status = 'Ошибка записи файлов'
        self.status_log()
    
        return global_dict


    #######################################################################
#par = Parser()
# par.agent('0373100119622000001')
# par.parse_head()
#print(par.get_supplier_links('0373100119622000001'))
# par.get_result_contracts('0373100119622000001')

# par.get_supplier_docs('https://zakupki.gov.ru/epz/order/notice/ok20/view/protocol/protocol-docs.html?regNumber=0373100119622000001&protocolId=39399003')
#par.get_contract_details('https://zakupki.gov.ru/epz/contract/contractCard/document-info.html?reestrNumber=1770201740022000003&contractInfoId=83632530')
# par.get_electronic_documents('https://zakupki.gov.ru/epz/rdik/card/info.html?id=2652630')

# par.get_documents_contracts('0345100003720000060')
# print(par.GetAllDocks())

# par = Parser()
# par.agent('0373100119621000003')
#                 # par.Make_Json()
# par.Make_Dock()