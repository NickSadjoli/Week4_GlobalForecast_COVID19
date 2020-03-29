from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import sys

worldometer_path = "https://www.worldometers.info/coronavirus/"
worldometer_country_path = worldometer_path + "/country/"

class MainDataLatest():
    '''
    Class that scrapes the main page of the Worldometer site.
    '''
    def __init__(self, verbose=False):
        self.driver = webdriver.Chrome()
        self.driver.get(worldometer_path)
        self.mainpage_data = BeautifulSoup(self.driver.page_source, "html.parser")

        self.latest_table = self.mainpage_data.find_all('table')[0]
        self.table_data = None
        self.country_list = []
        self.countries_w_href = {}
        self.main_columns = None
        self.num_of_columns = 0
        self.parse_latest_main()

        if verbose:
            print("country lists")
            print(self.country_list)
            print(self.countries_w_href)
            print("list of columns", self.main_columns, self.num_of_columns)
            print(self.table_data)

        sys.exit(0)
        
        #If using purely selenium. Not recommended as BeautifulSoup is much faster and cleaner
        self.web_table = self.driver.find_element_by_xpath('//*[@id="main_table_countries_today"]/tbody[1]')
        self.web_table_header = self.driver.find_element_by_xpath('//*[@id="main_table_countries_today"]/thead')
        self.table_columns = []
        self.num_of_columns = 0
        self.get_table_columns()
        self.country_len = 0
        self.get_num_countries()
        self.country_list = []
        self.countries_w_href = {}
        self.get_country_list(verbose)

        self.table_data = pd.DataFrame(index=range(0, self.country_len), columns=self.table_columns)
        self.update_table_data()
        
        if verbose:
            print("country lists")
            print(self.country_list)
            print(self.countries_w_href)
            print("list of columns", self.table_columns, self.num_of_columns)
            print(self.table_data)
        
    def parse_latest_main(self):
        rows = self.latest_table.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        self.main_columns = column_names
        self.num_of_columns = len(column_names)
        self.table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ') for row_el in row_elements]

            #check whether worldometer has extra page for this country
            href_check = row_elements[0].find_all('a', href=True)
            if len(href_check) > 0:
                self.countries_w_href[row_elements[0].text] = worldometer_path + href_check[0]['href']

            self.table_data.loc[i-1] = row_values
        return

    def get_table_columns(self):
        column_els = self.web_table_header.find_elements_by_xpath("./tr/th")
        table_columns = []
        for el in column_els:
            table_columns.append(el.text.replace('\n', ' '))
        self.table_columns = table_columns
        self.num_of_columns = len(table_columns)
        return table_columns

    def get_num_countries(self):
        self.country_len = len(self.web_table.find_elements_by_xpath("./tr"))
        return self.country_len

    def get_country_list(self, verbose=False):
        country_list = []
        countries_w_href = {}
        country_href = None

        for i in range(1, self.country_len + 1):
            try:
                cur_element = self.web_table.find_element_by_xpath("./tr[{}]/td[1]/a".format(str(i)))
                country_href = cur_element.get_attribute("href")
                country_name = cur_element.text
                country_name = country_name.lower()
                countries_w_href[country_name] = country_href
                #countries_w_href.append(cur_element.text.lower())
            except:
                cur_element = self.web_table.find_element_by_xpath("./tr[{}]/td[1]".format(str(i)))
            cur_country = cur_element.text
            if verbose:
                print("Country #{}=>".format(str(i-1)), cur_country) 
            country_list.append(cur_country)

        self.country_list = country_list
        self.countries_w_href = countries_w_href

        return country_list, countries_w_href

    def update_table_data(self):
        table_data = self.table_data
        for i in range(1, self.country_len + 1):
            row_elements = self.web_table.find_elements_by_xpath("./tr[{}]/".format(str(i)))
            row_values = [el.text for el in row_elements[1:]]
            #print(row_elements[1:].text)
            #table_data.loc[i] = row_values
            print(row_values, len(row_values), row_elements[1].text)
            table_data.loc[i][self.table_columns[0]] = self.country_list[i-1]
            table_data.loc[i][self.table_columns[1]:] = row_values

        return

    def get_MainTable(self):
        return self.table_data

    def get_countries_w_href(self):
        return self.countries_w_href

    def write_to_csv(self, path=None):
        if path is None:
            path = "./Main_Worldometer_Table.csv"
        self.table_data.to_csv(path, sep=',')       
        return

class TimeSeriesData(MainDataLatest):
    def __init__(self, verbose=False):
        self.driver = None

if __name__=="__main__":
    main_table = MainDataLatest(verbose=True)
    #main_table.write_to_csv()