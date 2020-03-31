"""
Contains basic utilities to be re-usable for webscraping of relevant COVID-19 Data.
Scraper functions below assumes the Worldometer's COVID-19 site
("https://www.worldometers.info/coronavirus/") as the default site to scrape, however
can be utilized for other pages as well, with minor changes

Authored by: Nicholas Sadjoli (Github @NickSadjoli)
Co-authored by: Josephine Monica (Github @josephinemonica)
"""

from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import sys
import re

worldometer_path = ("https://www.worldometers.info/coronavirus/")

class BasicScraper():
    def __init__(self, driver=None, verbose=False, default_site="https://www.worldometers.info/coronavirus/"):
        
        self.driver = self._check_webdriver(driver=driver, default_site=default_site, verbose=verbose)

    def _check_webdriver(self, driver, default_site, verbose=False):
        if driver is not None:
            if verbose:
                print("driver is already initiated")
            return driver
        else:
            if verbose:
                print("no drivers initated yet. Intiating...")
            cur_driver = webdriver.Chrome()
            cur_driver.get(default_site)
            return cur_driver

    #### Functions for Scraping the Table from Main Coronavirus Page ###
    def parse_table(self, table_element):
        '''
        Given a table element (assumed already obtained from a page_soup), pare content of table and return it as a 
        Pandas Dataframe object. Also returns the name of the table columns and rows
        '''
        rows = table_element.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        num_of_columns = len(column_names)
        table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]
            self.latest_table_data.loc[i-1] = row_values

        return table_data, column_names, num_of_columns


    def find_all_highcharts(self, js_text, verbose=False):
        '''
        Function that parses a given js_text string for all possible strings
        containing a Highchart.js section. Returns dictionary containing
        all parsed Highchart sections
        '''

        listed_charts = {}

        def find_highchart_recur(js_text, listed_charts, verbose=False):
            
            if verbose:
                print(js_text.count("Highcharts.chart("))
            
            if js_text.count("Highcharts.chart(") <= 1:
                cur_domId = js_text.split("Highcharts.chart(" )[1].split("'")[1]
                previous_data, cur_chartData = js_text.split("Highcharts.chart('" + cur_domId + "',")
                listed_charts[self.domId_map[cur_domId]] = cur_chartData
                #listed_charts[cur_domId] = cur_chartData
                return previous_data, listed_charts
            else:
                cur_domId = js_text.split("Highcharts.chart(")[1].split("'")[1]
                subsequent_strings = js_text.split("Highcharts.chart('" + cur_domId + "',")[1]
                cur_chartData, listed_charts = find_highchart_recur(subsequent_strings, listed_charts)
                listed_charts[self.domId_map[cur_domId]] = cur_chartData
                return cur_chartData, listed_charts

        _, listed_charts = find_highchart_recur(js_text, listed_charts, verbose)
        return listed_charts

    def find_all_chart_series_values(self, series_data, verbose=False):
        '''
        Given a Highchart's series data, function parses all values and returns a
        dictionary containing all the data's 'name' (i.e type of data), and their
        data values
        '''

        values_dict = {}
        def find_values_recur(series_data, values_dict, verbose=False):
            
            if verbose:
                print(series_data.count("name: '"))

            val_name = series_data.split("name: '")[1].split("',")[0]
            values_str = series_data.split("data: [")[1].split("]")[0]#.replace('\"', '')
            values = values_str.split(',')
            values_dict[val_name] = values

            if series_data.count("name: '") <= 1:
                return values_dict
            else:
                next_vals = series_data.split("data: [" + values_str + "]")[1]#.split("]")[1]
                values_dict = find_values_recur(next_vals, values_dict=values_dict)
                return values_dict

        return find_values_recur(series_data, values_dict, verbose)


class WorldometerScraper(BasicScraper):
    def __init__(self):
        return
    
    #### Functions for Scraping the Table from Main Coronavirus Page ###
    def parse_worldometer_table(self, table_element):
        '''
        Special variation of the normal parse_table that also returns any countries with potential hrefs to a more 
        dedicated country page on the Worldometer site.
        '''
        rows = table_element.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        num_of_columns = len(column_names)
        table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        countries_w_hrefs = {}

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]

            #check whether worldometer has extra page for this country
            href_check = row_elements[0].find_all('a', href=True)
            if len(href_check) > 0:
                countries_w_href[row_elements[0].text] = worldometer_path + href_check[0]['href']

            table_data.loc[i-1] = row_values

        return table_data, column_names, num_of_columns, countries_w_hrefs
