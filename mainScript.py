import csv
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# read gcom cities into pandas dataframe
cities = pd.read_csv(r"C:\Users\roman.hennig\Documents\Workspace\GCoMActionExplorer\gcom_cities.csv", encoding="utf-8")

# initialize dictionary with city id's as keys
citiesDict = dict.fromkeys(list(cities['new_id']))

# fill dictionary values by looping over rows in dataframe

# take keys from headers, add placeholders for actions and matches
keys = list(cities) + ['actions', 'matches']
for index, row in cities.iterrows():
    # take value for each city dict from the row and add empty list placeholders for actions and matches
    values = list(row) + [[], []]
    # zip keys and values together to create the dict
    citiesDict[row[0]] = dict(zip(keys, values))

print(citiesDict['AL0004'])

# # some fun seaborn plots
# sns.lmplot(x='Population', y='GDP', data=cities)
# fig, axes = plt.subplots()
# sns.violinplot(data=cities[['HDD','CDD','TDD']], ax=axes)
# sns.lmplot(x='HDI_country', y='Fuel_price', data=cities)
# plt.show()

