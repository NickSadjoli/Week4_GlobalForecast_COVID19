"""
Contains the functions and Scraper classes used for scraping Data of Countries from the
Worldometer Websites, including the country-specifc pages. 

Authored by: Nicholas Sadjoli (Github @NickSadjoli)
Co-authored by: Josephine Monica (Github @josephinemonica)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from bs4 import BeautifulSoup
import sys
import re
import json as json

from covid19_scraper_utils import BasicScraper, WorldometerScraper

worldometer_path = "https://www.worldometers.info/coronavirus/"

## TODO: Create a Class that can scrape the time series data for all countries that has hrefs in Worldometer!
class Worldometer_LatestCountriesData(WorldometerScraper):
    def __init__(self, countries_w_href=None, driver=None, dates=None, verbose=False):
        super().__init__(driver=driver, verbose=verbose, default_site=worldometer_path)
        
        #self.driver = self._check_webdriver(driver=driver, verbose=verbose)

        self.countries_w_href = None
        if countries_w_href is not None:
            self.countries_w_href = countries_w_href
        else:
            self._parse_countries_w_href()
            return
        
        self.countries_w_region_dict = {}
        self.countries_timeseries_dict = {}
        self.countries_timeseries = None
        self.timeseries_rows = 0

        self.dates = dates

        if self.dates is None:
            if verbose:
                print("No dates provided. Will use the country with longest date range")
            self.no_dates_provided = True
        else:
            if verbose:
                print("Using provided dates")
            self.no_dates_provided = False
        
        self.domId_map = {'total-currently-infected-linear': 'Current Active Cases (Linear)',
                          'deaths-cured-outcome-small': 'Closed Cases',
                          'coronavirus-cases-linear': 'Cumulative Confirmed (Linear)',
                          'coronavirus-cases-log': 'Cumulative Confirmed (Logarithmic)',
                          'coronavirus-deaths-linear': 'Cumulative Deaths (Linear)',
                          'coronavirus-deaths-log': 'Cumulative Deaths (Logarithmic)',
                          'graph-active-cases-total': 'Daily Current Active Cases',
                          'graph-cases-daily': 'Daily New Active Cases',
                          'graph-deaths-daily': 'Daily New Deaths',
                          'cases-cured-daily': 'Daily New Case & Recoveries',
                          'deaths-cured-outcome': 'Closed Cases'
                          }
                          
        for country in self.countries_w_href:
            country_href = self.countries_w_href[country]
            self.driver.get(country_href)
            try:
                element = WebDriverWait(self.driver, 2.2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "footerlinks")) )
            except:
                pass
            #print("Current country and href:", country, country_href)
            countrypage_soup = BeautifulSoup(self.driver.page_source, "html.parser")
            self.get_country_timeseries(country, countrypage_soup, verbose=verbose)
            self.get_country_regional_data(country, countrypage_soup, verbose=verbose)

        self.timeseries_columns = self.dates
        self.timeseries_columns.insert(0, 'Data Type')
        self.timeseries_columns.insert(0, 'Country')
        
        #self.countries_timeseries_data = pd.DataFrame(index=range(0, self.timeseries_rows), columns=self.timeseries_columns)
        self.countries_timeseries_data = pd.DataFrame(columns=self.timeseries_columns)

        i = 0
        for country in self.countries_timeseries_dict:
            for data_type in self.countries_timeseries_dict[country]:
                if data_type == 'dates':
                    pass
                else:
                    data_date = self.countries_timeseries_dict[country][data_type]['chart_dates']
                    cur_timeseries = pd.Series(index=self.timeseries_columns)
                    cur_timeseries['Country'] = country
                    cur_timeseries['Data Type'] = data_type
                    cur_timeseries[data_date] = self.countries_timeseries_dict[country][data_type]['values']
                    self.countries_timeseries_data = self.countries_timeseries_data.append(cur_timeseries, ignore_index=True)
                    '''
                    self.countries_timeseries_data.loc[i]['Country'] = country
                    self.countries_timeseries_data.loc[i]['Data Type'] = data_type
                    self.countries_timeseries_data.loc[i][data_date] = self.countries_timeseries_dict[country][data_type]['values']
                    '''
                    i += 1

        self.regional_columns = None
        self.regional_rows = 0
        for country in self.countries_w_region_dict:
            if self.regional_columns is None:
                self.regional_columns = self.countries_w_region_dict[country]['columns']
            else:
                self.regional_columns.append(self.countries_w_region_dict[country]['columns'])
            self.regional_rows += len(self.countries_w_region_dict[country]['regions'])
        self.countries_regional_data = pd.DataFrame(index=range(0, self.regional_rows), columns=self.regional_columns)

        j=0
        for country in self.countries_w_region_dict:
            for region_data in self.countries_w_region_dict[country]['regions']:
                self.countries_regional_data.loc[j]['Country'] = country
                self.countries_regional_data.loc[j]['Region': ] = region_data
                j += 1

        if verbose:
            print(self.countries_timeseries_data)
            print(self.countries_regional_data)

    def _parse_countries_w_href(self):
        
        #Get driver back to mainpage first
        self.driver.get(worldometer_path)
        try:
            element = WebDriverWait(self.driver, 2.2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "footerlinks"))  )
        except:
            pass
        mainpage_soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        #parse mainpage table to get all the countries with hrefs
        latest_table = mainpage_soup.find_all('table')[0]
        rows = latest_table.find_all('tr')

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')

            #check whether worldometer has extra page for this country
            href_check = row_elements[0].find_all('a', href=True)
            if len(href_check) > 0:
                self.countries_w_href[row_elements[0].text] = worldometer_path + href_check[0]['href']
        return

    def get_country_regional_data(self, country, countrypage_soup, verbose=False):
        country_latest_table = countrypage_soup.find_all('table')
        
        if len(country_latest_table) == 0:
            print("{} has no tables".format(country))
            return
        else:
            country_latest_table = country_latest_table[0]
        
        #self.parse_table(country_latest_table[0])
        rows = country_latest_table.find_all('tr')
        header_row = rows[0].find_all('th')
        self.countries_w_region_dict = self.parse_country_table(country, country_latest_table, cur_dict = self.countries_w_region_dict)

        return

    def get_country_timeseries(self, country, countrypage_soup, verbose=False):
        country_charts_elements = countrypage_soup.body.find_all('script', text=re.compile("Highcharts.chart"))
        print(len(country_charts_elements))
        self.countries_timeseries_dict[country] = {}
        self.parse_country_charts(country, country_charts_elements, verbose)
        return

    def parse_country_charts(self, country, country_charts_elements, verbose=False):
        for i in range(0, len(country_charts_elements)):
            list_of_charts = self.find_all_highcharts(country_charts_elements[i].text, domId_map=self.domId_map, verbose=verbose)
            #print([domId for domId in list_of_charts])
            for cur_chart_domId in list_of_charts:
                cur_chartData = list_of_charts[cur_chart_domId]
                dates = cur_chartData.split("categories: [")[1].split("]")[0].replace('\"', '')
                dates = dates.split(',')

                #there are potentially more than just one data series projected in one chart (e.g. Closed Cases)
                series_data = cur_chartData.split("series: [{")[1]
                values_dict = self.find_all_chart_series_values(series_data, verbose)

                #If there aren't any list of dates to use, use list of dates that are the longest
                if self.no_dates_provided:
                    if self.dates is None:
                        self.dates = dates 
                    else:
                        if len(dates) > len(self.dates):
                            self.dates = dates

                if len(self.countries_timeseries_dict[country]) == 0:
                    self.countries_timeseries_dict[country]['dates'] = dates #All WorldoMeter Time series charts assumed to share the same dates

                if len(values_dict) > 1:
                    for val_name in values_dict:
                        self.countries_timeseries_dict[country][cur_chart_domId + " - " + val_name] = {}
                        self.countries_timeseries_dict[country][cur_chart_domId + " - " + val_name]['chart_dates'] = dates
                        self.countries_timeseries_dict[country][cur_chart_domId + " - " + val_name]['values'] = values_dict[val_name]
                else:
                    for val_name in values_dict:
                        self.countries_timeseries_dict[country][cur_chart_domId] = {}
                        self.countries_timeseries_dict[country][cur_chart_domId]['chart_dates'] = dates
                        self.countries_timeseries_dict[country][cur_chart_domId]['values'] = values_dict[val_name]
            
        return
    
    def write_countriesTimeSeries_to_csv(self, path=None):
        if path is None:
            path = "./Worldometer_Countries_TimeSeries.csv"
        self.countries_timeseries_data.to_csv(path, sep=',', float_format='%.5f')       
        return
    
    def write_countriesRegional_to_csv(self, path=None):
        if path is None:
            path = "./Worldometer_Countries_Regional.csv"
        self.countries_regional_data.to_csv(path, sep=',', float_format='%.5f')
        return


class Worldometer_LatestGlobalData(WorldometerScraper):
    '''
    Class that scrapes the main page of the Worldometer site.
    '''
    def __init__(self, mainpage_soup=None, driver=None, verbose=False):
        super().__init__(driver=driver, verbose=verbose, default_site=worldometer_path)
        #self.driver = self._check_webdriver(driver=driver, verbose=verbose)

        if mainpage_soup is not None:
            self.mainpage_soup = mainpage_soup
        else:
            self.mainpage_soup = BeautifulSoup(self.driver.page_source, "html.parser")

        self.mainpage_soup = BeautifulSoup(self.driver.page_source, "html.parser")

        #Get the Main Table first
        self.latest_table = self.mainpage_soup.find_all('table')[0]
        self.latest_table_data = None
        self.country_list = []
        self.countries_w_href = {}
        self.main_columns = None
        self.num_of_columns = 0

        self.latest_table_data, self.main_columns, self.num_of_columns, self.countries_w_href = self.parse_global_worldometer_table(self.latest_table)
        
        #self.parse_latest_maintable()

        #Then get the Charts
        #find all dom-s with charts created with Highchart.js 
        self.global_charts = mainpage_soup.body.find_all('script', text=re.compile("Highcharts.chart"))
        self.global_timeseries_dict = {}
        
        self.domId_map = {'total-currently-infected-linear': 'Current Active Cases (Linear)',
                          'deaths-cured-outcome-small': 'Closed Cases',
                          'coronavirus-cases-linear': 'Cumulative Confirmed (Linear)',
                          'coronavirus-cases-log': 'Cumulative Confirmed (Logarithmic)',
                          'coronavirus-deaths-linear': 'Cumulative Deaths (Linear)',
                          'coronavirus-deaths-log': 'Cumulative Deaths (Logarithmic)'
                          }
        
        self.recorded_dates = None
        self.global_timeseries_data = None
        self.parse_global_timeseries(verbose=verbose)

        if verbose:
            print("country lists")
            print(self.country_list)
            print(self.countries_w_href)
            print("list of columns", self.main_columns, self.num_of_columns)
            print(self.latest_table_data)
            print(self.global_timeseries_data)
    
    def _check_webdriver(self, driver, verbose=False):
        if driver is not None:
            if verbose:
                print("driver is already initiated")
            return driver
        else:
            if verbose:
                print("no drivers initated yet")
            cur_driver = webdriver.Chrome()
            cur_driver.get(worldometer_path)
            try:
                element = WebDriverWait(cur_driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "footerlinks"))
                )
            except:
                pass
            return cur_driver

    #### Functions for Scraping the Table from Main Coronavirus Page ###
    def parse_latest_maintable(self):
        rows = self.latest_table.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        self.main_columns = column_names
        self.num_of_columns = len(column_names)
        self.latest_table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]

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

    def get_latestTable_data(self):
        return self.latest_table_data

    def get_countries_w_href(self):
        return self.countries_w_href

    def write_latestTable_to_csv(self, path=None):
        if path is None:
            path = "./Main_Worldometer_Table.csv"
        self.latest_table_data.to_csv(path, sep=',')       
        return

    ####################################################################


    #### Functions for Scraping the Charts from Main Coronavirus Page ###
    def parse_global_timeseries(self, verbose=False):
        js_charts = self.global_charts

        for i in range(0, len(js_charts)):

            #There might be more than 1 chart in one particular dom
            list_of_charts = self.find_all_highcharts(js_charts[i].text, domId_map=self.domId_map, verbose=verbose)
            #list_of_charts = self.find_all_highcharts(js_charts[i].text, verbose)

            for cur_chart_domId in list_of_charts:
                cur_chartData = list_of_charts[cur_chart_domId]
                dates = cur_chartData.split("categories: [")[1].split("]")[0].replace('\"', '')
                dates = dates.split(',')

                #there are potentially more than just one data series projected in one chart (e.g. Closed Cases)
                series_data = cur_chartData.split("series: [{")[1]
                values_dict = self.find_all_chart_series_values(series_data, verbose)

                if len(self.global_timeseries_dict) == 0:
                    self.global_timeseries_dict['dates'] = dates #All WorldoMeter Time series charts assumed to share the same dates

                if len(values_dict) > 1:
                    for val_name in values_dict:
                        self.global_timeseries_dict[cur_chart_domId + " - " + val_name] = values_dict[val_name]
                else:
                    for val_name in values_dict:
                        self.global_timeseries_dict[cur_chart_domId] = values_dict[val_name]

        self.recorded_dates = self.global_timeseries_dict['dates']
        ts_data_col = self.recorded_dates.copy()
        ts_data_col.insert(0, 'Data Type')
        print("number of columns", len(ts_data_col))

        #not including dates as a main data row
        self.global_timeseries_data = pd.DataFrame(index=range(0, len(self.global_timeseries_dict) -1), columns=ts_data_col) 

        i = 0
        #for i in range(0, len(self.global_timeseries_dict) -1):
        for data_type in self.global_timeseries_dict:
            if data_type == "dates":
                continue
                
            to_be_inserted = self.global_timeseries_dict[data_type]

            #Some data might be started to be recorded at a different date. In this case fill the rest of the data with '0'
            if len(to_be_inserted) < len(ts_data_col):
                for j in range(0, len(ts_data_col) - len(to_be_inserted) - 1):
                    to_be_inserted.insert(0, '0')
            to_be_inserted.insert(0, data_type)
            self.global_timeseries_data.loc[i] = to_be_inserted #self.global_timeseries_dict[data_type]
            i += 1

        return

    def get_timeseries_dates(self):
        return self.recorded_dates

    def get_globalTimeSeries(self):
        return self.global_timeseries_data

    def write_globalTimeSeries_to_csv(self, path=None):
        if path is None:
            path = "./Main_Worldometer_TimeSeries.csv"
        self.global_timeseries_data.to_csv(path, sep=',', float_format='%.5f')       
        return
    #####################################################################



if __name__=="__main__":
    
    driver = webdriver.Chrome()
    driver.get(worldometer_path)
    mainpage_soup = BeautifulSoup(driver.page_source, "html.parser")

    global_cases = Worldometer_LatestGlobalData(mainpage_soup=mainpage_soup, driver=driver, verbose=True)
    global_cases.write_latestTable_to_csv("./data/Main_Worldometer_Table.csv")
    global_cases.write_globalTimeSeries_to_csv("./data/Main_Worldometer_TimeSeries.csv")
    recorded_dates = global_cases.get_timeseries_dates()
    print("Recorded dates", recorded_dates)

    countries_w_href = global_cases.get_countries_w_href()
    countries_data = Worldometer_LatestCountriesData(countries_w_href=countries_w_href, driver=driver, dates=recorded_dates, verbose=True)
    countries_data.write_countriesTimeSeries_to_csv("./data/Worldometer_Countries_TimeSeries.csv")
    countries_data.write_countriesRegional_to_csv("./data/Worldometer_Countries_Regional.csv")

    #global_timeseries = GlobalTimeSeries(mainpage_soup=mainpage_soup, driver=driver, verbose=True)



