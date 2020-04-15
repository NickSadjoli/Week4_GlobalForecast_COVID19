#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 05:25:58 2020

@author: josephinemonica
"""
import pandas as pd 
import numpy as np

def string_to_integer(s):
     # e.g. '1,439,323,776' --->  '1439323776'
    s = s.replace(",","")
    # Convert string to integer
    s = int(s)
    
    return s

class Population():
    def __init__(self,population_filename):
        df = pd.read_csv(population_filename)
        self.country_list = np.array(df["Country (or dependency)"])
        self.population_list = np.array(df["Population (2020)"])
        self.median_age_list = np.array(df["Med. Age"])
        self.population_density_list = np.array(df["Density (P/Km²)"])
        
    def get_country_index(self,country):
        # If country doesn't exist return None
        
        aliases = {}
        aliases["US"] = "United States"
        aliases["Brunei"] = 'Brunei '
        aliases["Taiwan*"] = "Taiwan"
        aliases["Korea, South"] = "South Korea"
        if(country in aliases.keys()):
            country = aliases[country]
        ix = np.where(self.country_list==country)[0]
        if(len(ix)==0):
            return None
        return ix[0]
    
    def get_population(self,country):
        ix = self.get_country_index(country)
        
        if(ix is None):
            return None
        res = self.population_list[ix]
        
        return string_to_integer(res)
    
    def get_population_density(self,country):
        ix = self.get_country_index(country)
        
        if(ix is None):
            return None
        
        res = self.population_density_list[ix]
        
        return string_to_integer(res)
    
    def get_median_age(self,country):
        ix = self.get_country_index(country)
        
        if(ix is None):
            return None
        
        median_age = self.median_age_list[ix]
        
        if(median_age == 'N.A.'):
            return None
        else:
            return string_to_integer(median_age)
    
    
if __name__ =="__main__":
    p = Population("data/Worldometer_Population_Latest.csv")
    
    print("Median age for China is {}".format(p.get_median_age("China")))
    print("Population for China is {}".format(int(p.get_population("China"))))