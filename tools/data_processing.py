"""
Contains functions for more convenience data processing.

Authored by: Josephine Monica (Github @josephinemonica)
Co-authored by: Nicholas Sadjoli (Github @NickSadjoli)
"""
import pandas as pd
import numpy as np


def append_population_data(population, path_file_toappend):
    '''
    Adds data from a population instance to a target data file, and saves it
    to appended_data.csv file

    Arguments:
    - population => A Population class instance
    - path_file_toappend => Path of CSV data file to append

    Returns:
    - a list of countries missing in the target path file
    [Also saves appended dataFrame to an "appended_data.csv" file]
    '''
    df = pd.read_csv(path_file_toappend)

    missing_country_list = []
    missing_value_median_age = -1
    missing_value_population = 100000
    missing_value_population_density = 1
    median_age_list = []
    population_list = []
    population_density_list = []
    for country in df["Country_Region"]:
        
        ##############
        # Median age
        ##############
        median_age_ = population.get_median_age(country)
        if(median_age_ is None):

            median_age_list.append(missing_value_median_age)

            # Report/ note that this country is not available
            if(country not in missing_country_list):
                missing_country_list.append(country)
        else:
            median_age_list.append(median_age_)
        
        ###############
        # Population
        ###############
        population_ = population.get_population(country)
        if(population_ is None):
            population_list.append(missing_value_population)
        else:
            population_list.append(population_)
        
        #####################
        # Population density
        #####################
        population_density_ = population.get_population_density(country)
        if(population_density_ is None):
            population_density_list.append(missing_value_population_density)
        else:
            population_density_list.append(population_density_)
    
    df["Median_Age"] = median_age_list
    df["Population"] = population_list
    df["Population_Density"] = population_density_list
    df.to_csv("data/appended_data.csv")
    
    return missing_country_list

def preprocess(filename, features, targets):
    '''
    Preprocess data to specify the features to be chosen and imputed, as well as the targeted fields to predict.

    Arguments:
    - filename => Pathfile to data to be pre-processed and used
    - features => a list of features to be chosen and used from the dataset
    - targets => a list of fields to be chosen and predicted from dataset

    Returns:
    - X => the X-component of training data containing the chosen list of features
    - Y => the Y-component of training data containing the chosen list of targets
    '''
    df = pd.read_csv(filename)

    # Create category called Region: country_province
    region_list = ["{}_{}".format(df["Country_Region"][i], df["Province_State"][i]) for i in range(df.shape[0])]
    df["Region"]=region_list

    # Get first day of corona virus for each region
    unique_region_list = list(set(region_list))
    unique_region_list.sort()
    first_date_dict = {}
    for region in unique_region_list:
        mask = df["Region"]==region
        first_ix = np.where(df[mask]["ConfirmedCases"]>0)[0][0] -1    
        first_date = df[mask]["Date"].iloc[first_ix]
        first_date_dict[region] = first_date

    # add column "Days": number of days since the first day of case per each region
    def get_days(dt):
        return dt.days
    dummy = [first_date_dict[region] for region in df["Region"]]
    df["Days"]=(pd.to_datetime(df['Date'])-pd.to_datetime(dummy)).apply(get_days)

    # Add previous confirmed cases and previous fatalities to df
    loc_group=["Region"]
    for target in targets:
        df["prev_{}".format(target)] = df.groupby(loc_group)[target].shift()
        df["prev_{}".format(target)].fillna(0, inplace=True)
    
    # TODO
    df = df[df["Days"]>=-1].copy(deep=True)
    
    # TODO apply log
    for target in targets:
        df[target] = np.log1p(df[target])
        df["prev_{}".format(target)] = np.log1p(df["prev_{}".format(target)])
    
    # ConfirmCases, Fatilies
    X = df[features]
    # TODO use log1p
    Y = df[targets]
    
    return X,Y