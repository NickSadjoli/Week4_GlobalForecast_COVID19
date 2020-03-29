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
        self.latest_table_data = None
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
            print(self.latest_table_data)

    def parse_latest_main(self):
        rows = self.latest_table.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        self.main_columns = column_names
        self.num_of_columns = len(column_names)
        self.latest_table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ') for row_el in row_elements]

            #check whether worldometer has extra page for this country
            href_check = row_elements[0].find_all('a', href=True)
            if len(href_check) > 0:
                self.countries_w_href[row_elements[0].text] = worldometer_path + href_check[0]['href']

            self.latest_table_data.loc[i-1] = row_values
        return

    def get_latestTable_columns(self):
        return self.main_columns

    def get_list_of_countries(self):
        return self.country_list

    def get_number_of_countries(self):
        return len(self.country_list) - 1 #Not counting the 'World' as a country
    
    def get_list_of_countries_w_href(self):
        return self.countries_w_href

    def get_num_countries(self):
        self.country_len = len(self.web_table.find_elements_by_xpath("./tr"))
        return self.country_len

    def get_latestTable_data(self):
        return self.latest_table_data

    def get_countries_w_href(self):
        return self.countries_w_href

    def write_latestTable_to_csv(self, path=None):
        if path is None:
            path = "./Main_Worldometer_Table.csv"
        self.latest_table_data.to_csv(path, sep=',')       
        return

class TimeSeriesData(MainDataLatest):
    def __init__(self, verbose=False):
        self.driver = None

if __name__=="__main__":
    main_table = MainDataLatest(verbose=True)
    main_table.write_latestTable_to_csv("./data/Main_Worldometer_Table.csv")