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
        
        self.driver = self.check_webdriver(driver=driver, default_site=default_site, verbose=verbose)

    def check_webdriver(self, driver, default_site, verbose=False):
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
            table_data.loc[i-1] = row_values

        return table_data, column_names, num_of_columns

    def parse_worldometertable_w_hrefs(self, table_element, href_element_pos, cur_path):
        '''
        Special variation of the normal parse_table that also returns any country elements (specifically countries) any countries in 
        a Worldometer table with potential href elements to a more dedicated page on the Worldometer site. Note that the href_element_pos 
        variable is expected as an integer which specifies the position of the element in each row that is suspected to have an href 
        trait.

        A more generic version of the parse_global_worldometer_table function. 
        '''
        rows = table_element.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        num_of_columns = len(column_names)
        table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        countries_w_href = {}

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]

            #check whether worldometer has extra page for this country
            href_check = row_elements[href_element_pos].find_all('a', href=True)
            if len(href_check) > 0:
                countries_w_href[row_elements[href_element_pos].text] = cur_path + href_check[0]['href']

            table_data.loc[i-1] = row_values

        return table_data, column_names, num_of_columns, countries_w_href


    def find_all_highcharts(self, js_text, domId_map=None, verbose=False):
        '''
        Function that parses a given js_text string for all possible strings
        containing a Highchart.js section. Returns dictionary containing
        all parsed Highchart sections
        '''

        listed_charts = {}

        def find_highchart_recur(js_text, listed_charts, domId_map, verbose=False):
            
            #if verbose: #Only uncomment for debug purposes!
            #    print(js_text.count("Highcharts.chart("))
            
            if js_text.count("Highcharts.chart(") <= 1:
                cur_domId = js_text.split("Highcharts.chart(" )[1].split("'")[1]
                previous_data, cur_chartData = js_text.split("Highcharts.chart('" + cur_domId + "',")
                if domId_map is not None:
                    listed_charts[domId_map[cur_domId]] = cur_chartData
                else:
                    listed_charts[cur_domId] = cur_chartData
                #listed_charts[cur_domId] = cur_chartData
                return previous_data, listed_charts
            else:
                cur_domId = js_text.split("Highcharts.chart(")[1].split("'")[1]
                subsequent_strings = js_text.split("Highcharts.chart('" + cur_domId + "',")[1]
                cur_chartData, listed_charts = find_highchart_recur(subsequent_strings, listed_charts, domId_map)
                if domId_map is not None:
                    listed_charts[domId_map[cur_domId]] = cur_chartData
                else:
                    listed_charts[cur_domId] = cur_chartData
                return cur_chartData, listed_charts

        _, listed_charts = find_highchart_recur(js_text, listed_charts, domId_map=domId_map, verbose=verbose)
        return listed_charts

    def find_all_chart_series_values(self, series_data, verbose=False):
        '''
        Given a Highchart's series data, function parses all values and returns a
        dictionary containing all the data's 'name' (i.e type of data), and their
        data values
        '''

        values_dict = {}
        def find_values_recur(series_data, values_dict, verbose=False):
            
            #if verbose: #Only uncomment for debug purposes!
            #    print(series_data.count("name: '"))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    #### Functions for Scraping the Table from Main Coronavirus Page ###
    def parse_global_worldometer_table(self, table_element):
        '''
        Special variation of the normal parse_table that also returns any countries with potential hrefs to a more 
        dedicated country page on the Worldometer site.
        '''
        rows = table_element.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        num_of_columns = len(column_names)
        table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        countries_w_href = {}

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]

            #check whether worldometer has extra page for this country
            href_check = row_elements[0].find_all('a', href=True)
            if len(href_check) > 0:
                countries_w_href[row_elements[0].text] = worldometer_path + href_check[0]['href']

            table_data.loc[i-1] = row_values

        return table_data, column_names, num_of_columns, countries_w_href

    def parse_country_table(self, country, table_element, cur_dict=None):
        '''
        Special variation of the normal parse_table for a specific Worldometer Country Site. 
        Returns a dictionary containing data on columns and all of the country's region instead.
        '''
        if cur_dict is None:
            cur_dict = {}

        rows = table_element.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup
        column_names[0] = 'Region'
        column_names.insert(0, 'Country')
        column_names.pop() #remove the 'Source' column
        cur_dict[country] = {}
        cur_dict[country]['columns'] = column_names
        cur_dict[country]['regions'] = []

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '').replace('\xa0', ' ') for row_el in row_elements]
            #cur_dict[country]['regions] = row_values
            cur_dict[country]['regions'].append(row_values[:-1])

        return cur_dict
