import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from pathlib import Path

## only needed for plots:
# import seaborn as sns
# import matplotlib.pyplot as plt
# import random

### parameters
# population cutoff for cities:
pop_cutoff = 50000

# similarity score cutoff for matching:
sim_cutoff = 0.7

# list of variables that should be log transformed
log_transform = ["GDP", "Population", "GDP_per_cap_method1"]

# list of variables for feature scaling
# (subtracting the mean and dividing by std deviation of distribution)
feature_scaling = ["GDP", "Population", "GDP_per_cap_method1",
                   "HDD", "CDD", "HDI_2", "Fuel_price"]

# ID of city to run tests on
# check gcom_cities file for id's
test_city = 'BR0003'

# set data folder, default is local folder in which the script is located
data_folder = Path('')

### utilites
# utility to find the list of actions from the CDP actions data base with a given gcom ID
# and data frame of actions
def findListOfCDPActions(actions_df, gcomId):
    # pull out the relevant actions for the city from the data base,
    # reset the index
    # TO-DO: better name matching than simple complete string match
    city_actions_df = actions_df.loc[actions_df['Account number'] ==
                                     citiesDict[gcomId]['cdp_id']].reset_index(drop=True)
    # create placeholder list of actions
    actionsList = [{} for x in range(len(city_actions_df))]
    # make key list for each action dict
    action_keys = ['description quality', 'description', 'reporting year',
                   'category', 'activity', 'source', 'link']
    for index, action in city_actions_df.iterrows():
        # translate CDP categories to reclassified ones
        descr = str(action['Action description'])
        description_quality = ""
        if len(descr) < 31:
            description_quality = "self-reported, low"
        elif len(descr) < 101:
            description_quality = "self-reported, medium"
        else:
            description_quality = "self-reported, high"
        action_values = [description_quality, descr,  action['Reporting Year'],
                         categoryDict[action['Sector']],
                         action['Emissions reduction activity'],
                         'CDP', 'https://www.cdp.net/en']
        # , action['Action description']]
        # zip keys and values together to create the dict
        actionsList[index] = dict(zip(action_keys, action_values))
    return actionsList

def findListOfCuratedActions(city_actions_df):
    # create placeholder list of actions
    actionsList = [{} for x in range(len(city_actions_df))]
    # make key list for each action dict
    action_keys = ['description quality', 'description', 'reporting year', 'category',
                   'activity', 'source', 'link']
    for index, action in city_actions_df.iterrows():
        # translate CDP categories to reclassified ones
        descr = str(action['Description'])
        description_quality = "curated"
        action_values = [description_quality, descr,  action['Year'],
                         action['Category'], action['Action Name'],
                         action['Source(s)'], action['Link(s)']]
        # , action['Action description']]
        # zip keys and values together to create the dict
        actionsList[index] = dict(zip(action_keys, action_values))
    return actionsList

def findListOfCuratedActionsGCOM(actions_df, gcomId):
    city_actions_df = actions_df.loc[actions_df['GCOM ID'] ==
                                     gcomId].reset_index(drop=True)
    return findListOfCuratedActions(city_actions_df)

def findListOfCuratedActionsNonGCOM(actions_df, cityName):
    city_actions_df = actions_df.loc[actions_df['City'].str.strip() ==
                                     cityName.strip()].reset_index(drop=True)
    return findListOfCuratedActions(city_actions_df)

def distance(city1_dict, city2_dict):
    # result will be a list of distances in each characteristic
    dist = list(range(1 + len(feature_scaling)))
    # first check whether cities are in same country (by country code cc)
    # if yes, this distance is 0. if no, 1
    dist[0] = int(city1_dict['cc'] != city2_dict['cc'])
    # distance for all numeric features
    for i, feature in enumerate(feature_scaling):
        dist[1+i] = city1_dict[feature] - city2_dict[feature]
    return dist

# utility to calculate similarity between two cities,
# given lists of their characteristics
# using numpy to calculate exponential function and euclidian distance between the
# vectors of city characteristics
def similarity(city1_dict, city2_dict):
    dist = distance(city1_dict, city2_dict)
    return np.exp(- np.linalg.norm(dist)/len(dist))

### set up categories
# read category matching from file
reclass_file = data_folder / "reclassification_files/cdp_sector_reclass.xlsx"
categories = pd.read_excel(reclass_file, encoding='latin-1').fillna('(blank)')
# build dict
categoryDict = dict(zip(list(categories['CDP Sector']), list(categories['reclass_sector'])))
# print(categoryDict)

### prepare dictionary of GCoM cities
# read gcom cities into pandas dataframe
cities_file = data_folder / "input_data/gcom_cities.csv"
cities = pd.read_csv(cities_file, encoding="utf-8").fillna('(blank)')

# select cities with population > pop_cutoff, reset index:
cities = cities.loc[cities['Population'] > pop_cutoff].reset_index(drop=True)

# x = pd.Series(cities["GDP"], name = 'GDP')
# sns.distplot(x).set_title("Distribution of GDP of GCOM cities "
#                           "with population > {}".format(pop_cutoff))
# plt.show()

# apply log transformation
cities[log_transform] \
    = cities[log_transform].apply(np.log)

# perform feature scaling:
cities[feature_scaling] \
    = StandardScaler().fit_transform(cities[feature_scaling])

# x = pd.Series(cities["GDP"], name = 'Scaled log of GDP')
# sns.distplot(x).set_title("Distribution of GDP of GCOM cities with population > {}"
#     " after a log transform and feature scaling".format(pop_cutoff))
# plt.show()

# initialize dictionary with city id's as keys
citiesDict = dict.fromkeys(list(cities['new_id']))

# fill dictionary values by looping over rows in dataframe

# take keys from headers, add placeholders for actions and matches
keys = list(cities) + ['cdp_id', 'actions', 'matches']
for index, row in cities.iterrows():
    # take value for each city dict from the row and add NA/empty 
    # list placeholders for cdp_id/actions and matches
    values = list(row) + ['NA', [], []]
    # zip keys and values together to create the dict
    citiesDict[row[0]] = dict(zip(keys, values))

### prepare CDP cities for matching

# read cdp actions into pandas dataframe
cdp_actions_file = data_folder / "input_data/Actions_cdp_2012-2017.csv"
actions_df_cdp = pd.read_csv(cdp_actions_file,
                         encoding="utf-8").fillna('(blank)')

# change USA to United States of America
actions_df_cdp = actions_df_cdp.replace(to_replace='USA',
                                value='United States of America')

# find set of city names used in the CDP actions file 
# (stripping leading and trailing whitespace)
cdp_cities = set(actions_df_cdp['City'].str.strip())
# print(cdp_cities)

### read in curated list of actions
curated_actions_file = data_folder / "input_data/Actions_db2.xlsx"
actions_df_curated = pd.read_excel(curated_actions_file,
                         encoding="utf-8").fillna('(blank)')

# find actions of cities that aren't in the GCOM cities
non_GCOM_cities = list(set(actions_df_curated.loc[actions_df_curated['GCOM ID'] == '(blank)']['City'].str.strip()))

# create dictionary for non GCOM cities
non_GCOM_dict = dict.fromkeys(non_GCOM_cities)

for a_city in non_GCOM_cities:
    non_GCOM_dict[a_city] = {'actions': findListOfCuratedActionsNonGCOM(actions_df_curated, a_city)}

### match GCoM cities to cdp action data base and curated actions
counter = 0
for entry in citiesDict.values():
    gcomCityName = entry['city']
    # match GCOM city to cdp_cities if possible and add list of cdp actions
    if gcomCityName in cdp_cities:
        counter += 1
        cdpId = set(actions_df_cdp.loc[actions_df_cdp['City'].str.strip() ==
                                   gcomCityName]['Account number'])
        ### TO-DO:
        # some city names appear multiple times.
        # have to match on add'l characteristics like country or coordinates
        if len(cdpId) > 1:
            print("Found several matches for " + gcomCityName)
            print(cdpId)
        # update GCoM cities list entry with cdp Id found
        entry['cdp_id'] = cdpId.pop()
        # update list of actions with the matched city in cdp data base
        entry['actions'] = findListOfCDPActions(actions_df_cdp, entry['new_id']) \
                           + findListOfCuratedActionsGCOM(actions_df_curated, entry['new_id'])


print("# of matched cities between GCOM and CDP: " + str(counter))

# find matches for cities
for i, city1_id in enumerate(cities['new_id']):
    for j, city2_id in enumerate(cities['new_id'][i + 1:]):
        city1 = citiesDict[city1_id]
        city2 = citiesDict[city2_id]
        sim = similarity(city1, city2)
        if sim > sim_cutoff:
            city1['matches'] += [{'city_id': city2_id, 'score': sim}]
            city2['matches'] += [{'city_id': city1_id, 'score': sim}]

# get info for only cities above test city's population to keep the file smaller:
bigCitiesDict = {k: citiesDict[k] for k in citiesDict.keys() if
                 citiesDict[k]['Population'] >= citiesDict[test_city]['Population']}
# add non GCOM cities
citiesDict['non-GCOM_cities'] = non_GCOM_dict
bigCitiesDict['non-GCOM_cities'] = non_GCOM_dict

# save data in json files
output_data_file = data_folder / 'output/cities_data.json'
with open(output_data_file, 'w') as f:
    json.dump(citiesDict, f) #, sort_keys=True, indent=4)

big_cities_output_file = data_folder / 'output/big_cities_data.json'
with open(big_cities_output_file, 'w') as f:
    json.dump(bigCitiesDict, f, sort_keys=True, indent=4)

### build general resources data base
general_resource_file = data_folder / "input_data/Guides for Action Explorer.xlsx"
general_resources = pd.read_excel(general_resource_file, encoding='latin-1').fillna('(blank)')
general_resource_keys = list(general_resources)
general_resource_dict = {}
for index, row in general_resources.iterrows():
    general_resource_values = list(row)
    general_resource_dict[index] = dict(zip(general_resource_keys, general_resource_values))

# print(general_resource_dict)
general_resource_output = data_folder / 'output/general_resources.json'
with open(general_resource_output, 'w') as f:
    json.dump(general_resource_dict, f, sort_keys=True, indent=4)


# # calculate top ten matches for test city and print cities with match scores
# top_ten = sorted(citiesDict[test_city]['matches'], key=lambda k: k['score'],
#                  reverse=True)[:10]
# print("Top Ten Matches for {}, {}:".format(citiesDict[test_city]['city'],
#                                            citiesDict[test_city]['country']))
# for entry in top_ten:
#     print(citiesDict[entry['city_id']]['city'] + ", " + \
#           citiesDict[entry['city_id']]['country'] + \
#           ". Score: {:05.4f}".format(entry['score']))
#     # print all actions that matched cities have taken
#     print("City's actions: ")
#     for action in citiesDict[entry['city_id']]['actions']:
#         print(action['reporting year'], ":", action['category'], ":", action['activity'])

# # look at 10 random scores for other cities with test city:
# print("Random Ten Scores for {}, {}:".format(citiesDict[test_city]['city'], citiesDict[test_city]['country']))
# for i in range(10):
#     random_match = random.choice(list(citiesDict))
#     print(citiesDict[random_match]['city'] + ", " + citiesDict[random_match]['cc'] + ". Score: {:05.4f}".format(
#         similarity(citiesDict[random_match], citiesDict[test_city])))

# # some fun seaborn plots
# sns.lmplot(x='Population', y='GDP', data=cities)
# fig, axes = plt.subplots()
# sns.violinplot(data=cities[['HDD','CDD','TDD']], ax=axes)
# sns.lmplot(x='HDI_country', y='Fuel_price', data=cities)
# x = pd.Series(cities["GDP"], name = 'Normalized log of GDP')
# sns.distplot(x)
# plt.show()
# y = pd.Series(cities["Population"], name = 'Normalized log of Population, cutoff at {}'.format(pop_cutoff))
# sns.distplot(y)
# plt.show()


# creating a visual for test city's similarity scores with other cities
# sim_scores = list(range(len(cities.index)))
# for i, entry in enumerate(citiesDict.values()):
#     sim = similarity(citiesDict[test_city], entry)
#     sim_scores[i] = sim
#     if sim > sim_cutoff:
#         # print(entry['city'] + ", similarity: {}".format(sim))
#         entry['matches'] += [test_city]
#
# plt.plot(list(reversed(sorted(sim_scores)[:-1])))
# plt.ylabel('Similarity Score')
# plt.xlabel('Cities with population > {}'.format(pop_cutoff))
# plt.title('Matches for {}, {}:'.format(citiesDict[test_city]['city'],
#                                        citiesDict[test_city]['country']))
# plt.show()
