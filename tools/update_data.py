"""
Script to update the data folder using the webscraper scripts from the tools directory.

Authored by: Nicholas Sadjoli (Github @NickSadjoli)
Co-authored by: Josephine Monica (Github @josephinemonica)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import sys
import re
import requests
import time

from covid19_scraper_utils import WorldometerScraper, BasicScraper
from scrape_worldometer_data import worldometer_path, Worldometer_LatestCountriesData, Worldometer_LatestGlobalData

default_data_dir = "./input/"

def update_worldometer_data(driver, data_dir=default_data_dir, verbose=False):
    driver.get(worldometer_path)
    mainpage_soup = BeautifulSoup(driver.page_source, "html.parser")

    global_cases = Worldometer_LatestGlobalData(mainpage_soup=mainpage_soup, driver=driver, verbose=verbose)
    global_cases.write_latestTable_to_csv(data_dir + "Main_Worldometer_Table.csv")
    global_cases.write_globalTimeSeries_to_csv(data_dir + "Main_Worldometer_TimeSeries.csv")
    recorded_dates = global_cases.get_timeseries_dates()
    print("Recorded dates", recorded_dates)

    countries_w_href = global_cases.get_countries_w_href()
    countries_data = Worldometer_LatestCountriesData(countries_w_href=countries_w_href, driver=driver, dates=recorded_dates, verbose=verbose)
    countries_data.write_countriesTimeSeries_to_csv(data_dir + "Worldometer_COVID19-Countries_TimeSeries.csv")
    countries_data.write_countriesRegional_to_csv(data_dir + "Worldometer_COVID19-Countries_Regional.csv")
    return

def get_worldometer_population_data(driver, verbose=False):
    driver.get("https://www.worldometers.info/world-population/population-by-country/")
    try:
        element = WebDriverWait(driver, 2.2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "footerlinks")) )
    except:
        pass
    scraper = WorldometerScraper(driver=driver, verbose=verbose)
    page_soup = BeautifulSoup(scraper.driver.page_source, "html.parser")
    population_table = page_soup.find_all('table')[0]
    #population_data, _, _ = scraper.parse_table(population_table)
    #return population_data
    population_data, _, _, countries_w_href = scraper.parse_worldometertable_w_hrefs(population_table, 1, "https://www.worldometers.info")
    #print(population_data, countries_w_href)
    population_data.insert(2, 'Region', 'All_Regions')
    pop_data_cols = population_data.columns
    for country in countries_w_href:
        country_href = countries_w_href[country]
        scraper.driver.get(country_href)
        '''
        try:
            element = WebDriverWait(scraper.driver, 10, poll_frequency=1.0).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")) )
        except:
            pass
        '''
        time.sleep(3)
        country_population_page_init = scraper.driver.page_source
        #country_population_page = country_population_page_init.replace("<!--", " ").replace("--> ", " ") #for some reason, these markup 
                                                                    #'comment' sections throws off BeautifulSoup  
        country_population_page = country_population_page_init
        country_population_soup = BeautifulSoup(country_population_page, "html.parser")
        #country_population_soup =  BeautifulSoup(re.findall(r'<table.*>.*</table>', country_population_page.read())[0])
        regional_population_table = country_population_soup.find_all('table')[-1]
        if len(regional_population_table) == 0:
            continue
        rows = regional_population_table.find_all('tr')
        header_row = rows[0].find_all('th')
        column_names = [head.text.replace('\xa0', ' ') for head in header_row] #&nbsp gets turned into \xa0 by BeautifulSoup

        #sanity check to ensure that Regional population table exists (if it doesn't, then another table would get picked for the 
        # regional_population_table variable)
        if 'CITY NAME' not in column_names:
            continue

        num_of_columns = len(column_names)
        table_data = pd.DataFrame(index=range(0, len(rows[1:])), columns=column_names)

        #HTML seems to use the 1-indexing system instead of the normal 0-indexing system
        for i in range(1, len(rows)):
            row_elements = rows[i].find_all('td')
            row_values = [row_el.text.replace('\n', ' ').replace('+', '') for row_el in row_elements]

            cur_country_index = population_data[population_data['Country (or dependency)'] == country].index.values[0]
            cur_df = pd.DataFrame(index=[cur_country_index + 1], columns=pop_data_cols)
            cur_df.loc[cur_country_index + 1]['#'] = str(cur_country_index + 1.5)
            cur_df.loc[cur_country_index + 1]['Country (or dependency)'] = country.rstrip()
            cur_df.loc[cur_country_index + 1]['Region'] = row_values[1]
            cur_df.loc[cur_country_index + 1]['Population (2020)'] = row_values[-1]

            population_data = population_data.append(cur_df)
            population_data = population_data.sort_values(by=['#']) #i.e. sort by the countries' index numbers. This will ensure that all the
                                                                    # regions belong for each country correctly

            #print(row_elements, row_values)

            '''
            table_data.loc[i-1] = row_values
            '''
        print(population_data)
    return population_data

def get_climate_data(driver, verbose=False):
    '''
    Getting the CSV data using the API provided by worldbank here:
    https://datahelpdesk.worldbank.org/knowledgebase/articles/902061-climate-data-api
    '''

    #First get the ISO-alpha3 code for all countries, as listed by UN
    driver.get("https://unstats.un.org/unsd/methodology/m49/")
    try:
        element = WebDriverWait(driver, 2.2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "footerlinks")) )
    except:
        pass
    
    scraper = BasicScraper(driver=driver, verbose=verbose)
    page_soup = BeautifulSoup(scraper.driver.page_source, "html.parser")
    iso_country_table = page_soup.find(id="ENG_COUNTRIES").find_all('table')[0] #Specifically find the country table in English
    iso_country_data, _, _ = scraper.parse_table(iso_country_table)
    iso_country_data = iso_country_data.set_index('Country or Area')
    country_names = iso_country_data.index.to_numpy()
    country_codes = iso_country_data['ISO-alpha3 code'].to_numpy()
    print(iso_country_data)
    print(len(country_names), len(country_codes), iso_country_data.loc[' Afghanistan']['ISO-alpha3 code'])
    #sys.exit(0)

    start_end_dict = {'2020':'2039', '2040':'2059', '2060':'2079', '2080': '2099'}

    template_link = "http://climatedataapi.worldbank.org/climateweb/rest/v1/country/" 
    period_type = "mavg"
    variable = "tas"
    start = "2020"
    end = start_end_dict[start]

    full_climate_data = None

    for country in country_names:
        cur_code = iso_country_data.loc[country]['ISO-alpha3 code']
        api_call = template_link + period_type + "/" + variable + "/" + start + "/" + end + "/" + cur_code + ".csv"
        print("Currently calling API:", api_call)
        cur_climate_data = pd.read_csv(api_call, sep=',')
        cur_climate_data['Country'] = country
        if full_climate_data is None:
            full_climate_data = cur_climate_data
        else:
            full_climate_data = full_climate_data.append(cur_climate_data, ignore_index=True)

    return full_climate_data

def get_ourworldindata_testing_data():
    ourworldindata_github_dir = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/testing/"
    ourworldindata_allobservations = pd.read_csv(ourworldindata_github_dir + "covid-testing-all-observations.csv")
    ourworldindata_latest_details = pd.read_csv(ourworldindata_github_dir + "covid-testing-latest-data-source-details.csv")
    
    ourworldindata_allobservations.to_csv(default_data_dir + "OurWorldinData-COVID_testing-all_observations.csv")
    ourworldindata_latest_details.to_csv(default_data_dir + "OurWorldinData-COVID_testing-latest_datasource_details.csv")
    return

def get_covidtracking_test_data():
    """
    Get test data from The COVID Tracking Project, for testing data collected in the US region.

    Writes out to several dataFrames and saves to more .csv-s as well
    """
    covidtracking_api_path =  "https://covidtracking.com/api/"

    perstates_timeseries_path = covidtracking_api_path + "v1/states/daily.csv"
    perstates_current_values_path = covidtracking_api_path + "v1/states/current.csv"
    us_whole_timeseries_path = covidtracking_api_path + "us/daily.csv" 
    us_whole_current_values_path = covidtracking_api_path  + "v1/us/current.csv"

    us_perstates_timeseries     = pd.read_csv(perstates_timeseries_path)
    us_perstates_current_values = pd.read_csv(perstates_current_values_path)
    us_whole_timeseries         = pd.read_csv(us_whole_timeseries_path)
    us_whole_current_values     = pd.read_csv(us_whole_current_values_path)

    us_perstates_timeseries.to_csv("./input/COVIDTracking-US_PerStates-Timeseries.csv")
    us_perstates_current_values.to_csv("./input/COVIDTracking-US_PerStates-CurVal.csv")
    us_whole_timeseries.to_csv("./input/COVIDTracking-US_Whole-Timeseries.csv")
    us_whole_current_values.to_csv("./input/COVIDTracking-US_Whole-CurVal.csv")

    return

def update_all_data(verbose=False):

    driver = webdriver.Chrome()
    update_worldometer_data(driver)
    population_data = get_worldometer_population_data(driver)
    population_data.to_csv(default_data_dir + "Worldometer_Population_Regional_Latest.csv")
    full_climate_data = get_climate_data(driver)
    full_climate_data.to_csv(default_data_dir + "Climate_Data_Worldbank.csv")
    get_covidtracking_test_data()
    get_ourworldindata_testing_data()

    return

if __name__ == "__main__":
    update_all_data()
