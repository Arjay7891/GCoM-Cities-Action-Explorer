import csv
import pandas as pd
import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt


### utilites
# utility to find the list of actions from the CDP actions data base with a given gcom ID
# and data frame of actions
def findListOfActions(actions_df, gcomId):
    # pull out the relevant actions for the city from the data base,
    # reset the index
    city_actions_df = actions_df.loc[actions_df['Account number'] ==
                                     citiesDict[gcomId]['cdp_id']].reset_index(drop=True)
    # create placeholder list of actions
    actionsList = [{} for x in range(len(city_actions_df))]
    # make key list for each action dict
    action_keys = ['reporting year', 'category', 'activity'] #, 'description']
    for index, action in city_actions_df.iterrows():
        action_values = [action['Reporting Year'], action['Sector'],
                         action['Emissions reduction activity']]
                         #, action['Action description']]
        # zip keys and values together to create the dict
        actionsList[index] = dict(zip(action_keys, action_values))
    return actionsList


### prepare dictionary of GCoM cities
# read gcom cities into pandas dataframe
# cities = pd.read_csv(r"C:\Users\roman.hennig\Documents\Workspace\GCoMActionExplorer\gcom_cities.csv", encoding="utf-8")
cities = pd.read_csv(r"gcom_cities.csv", encoding="utf-8")

# initialize dictionary with city id's as keys
citiesDict = dict.fromkeys(list(cities['new_id']))

# fill dictionary values by looping over rows in dataframe

# take keys from headers, add placeholders for actions and matches
keys = list(cities) + ['cdp_id', 'actions', 'matches']
for index, row in cities.iterrows():
    # take value for each city dict from the row and add NA/empty list placeholders for cdp_id/actions and matches
    values = list(row) + ['NA', [], []]
    # zip keys and values together to create the dict
    citiesDict[row[0]] = dict(zip(keys, values))

### prepare CDP cities for matching

# read cdp actions into pandas dataframe
# actions_df = pd.read_csv(r"C:\Users\roman.hennig\Documents\Workspace\GCoMActionExplorer\Actions_cdp_2012-2017.csv",
                         # encoding="utf-8")
actions_df = pd.read_csv(r"Actions_cdp_2012-2017.csv",
                        encoding="utf-8")

# change USA to United States of America
actions_df = actions_df.replace(to_replace='USA', value='United States of America')

# find set of city names used in the CDP actions file (stripping leading and trailing whitespace)
cdp_cities = set(actions_df['City'].str.strip())
print(cdp_cities)

### match GCoM cities to cdp action data base
counter = 0
for entry in citiesDict.values():
    gcomCityName = entry['city']
    if gcomCityName in cdp_cities:
        counter += 1
        cdpId = set(actions_df.loc[actions_df['City'].str.strip() ==
                                   gcomCityName]['Account number'])
        if len(cdpId) > 1:
            print("Found several matches for " + gcomCityName)
            print(cdpId)
        # update GCoM cities list entry with cdp Id found
        entry['cdp_id'] = cdpId.pop()
        # update list of actions with the matched city in cdp data base
        entry['actions'] = findListOfActions(actions_df, entry['new_id'])

print("# of matched cities: " + str(counter))
# print(citiesDict['AL0004'])

print(citiesDict['BR0003'])

# # some fun seaborn plots
# sns.lmplot(x='Population', y='GDP', data=cities)
# fig, axes = plt.subplots()
# sns.violinplot(data=cities[['HDD','CDD','TDD']], ax=axes)
# sns.lmplot(x='HDI_country', y='Fuel_price', data=cities)
# plt.show()
