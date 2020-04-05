"""
Script to update the data folder using the webscraper scripts from the tools directory.

Authored by: Nicholas Sadjoli (Github @NickSadjoli)
Co-authored by: Josephine Monica (Github @josephinemonica)
"""

from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import sys
import re

from covid19_scraper_utils import WorldometerScraper, BasicScraper
from scrape_worldometer_data import worldometer_path, Worldometer_LatestCountriesData, Worldometer_LatestGlobalData

default_data_dir = "./data/"

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
    countries_data.write_countriesTimeSeries_to_csv(data_dir + "Worldometer_Countries_TimeSeries.csv")
    countries_data.write_countriesRegional_to_csv(data_dir + "Worldometer_Countries_Regional.csv")
    return

def get_worldometer_population_data(driver, verbose=False):
    driver.get("https://www.worldometers.info/world-population/population-by-country/")
    try:
        element = WebDriverWait(self.driver, 2.2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "footerlinks")) )
    except:
        pass
    scraper = WorldometerScraper(driver=driver, verbose=verbose)
    page_soup = BeautifulSoup(scraper.driver.page_source, "html.parser")
    population_table = page_soup.find_all('table')[0]
    population_data, _, _ = scraper.parse_table(population_table)
    return population_data
    

def get_climate_data(driver, verbose=False):
    '''
    Getting the CSV data using the API provided by worldbank here:
    https://datahelpdesk.worldbank.org/knowledgebase/articles/902061-climate-data-api
    '''

    #First get the ISO-alpha3 code for all countries, as listed by UN
    driver.get("https://unstats.un.org/unsd/methodology/m49/")
    try:
        element = WebDriverWait(self.driver, 2.2).until(
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


def update_all_data(verbose=False):

    driver = webdriver.Chrome()
    update_worldometer_data(driver)
    population_data = get_worldometer_population_data(driver)
    population_data.to_csv(default_data_dir + "Worldometer_Population_Latest.csv")
    full_climate_data = get_climate_data(driver)
    full_climate_data.to_csv(default_data_dir + "Climate_Data_Worldbank.csv")

    return

if __name__ == "__main__":
    update_all_data()
