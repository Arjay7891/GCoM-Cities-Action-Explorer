import csv
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt

### parameters
# population cutoff for cities:
pop_cutoff = 100000

# similarity score cutoff for matching:
sim_cutoff = 0.7

# list of variables that should be log transformed
log_transform = ["GDP", "Population", "GDP_per_cap_method1"]

# list of variables for feature scaling
# (subtracting the mean and dividing by std deviation of distribution)
feature_scaling = ["GDP", "Population", "GDP_per_cap_method1", "HDD", "CDD", "HDI_2", "Fuel_price"]

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

def distance(city1_dict, city2_dict):
    # result will be a list of distances in each characteristic
    dist = list(range(1+len(feature_scaling)))
    # first check whether cities are in same country (by country code cc)
    # if yes, this distance is 0. if no, 1
    dist[0] = int(city1_dict['cc'] != city2_dict['cc'])
    # distance for all numeric features
    for i, feature in enumerate(feature_scaling):
        dist[1+i] = city1_dict[feature] - city2_dict[feature]
    return dist

# utility to calculate similarity between two cities, given lists of their characteristics
# using numpy to calculate exponential function and euclidian distance between the
# vectors of city characteristics
def similarity(city1_dict, city2_dict):
    dist = distance(city1_dict, city2_dict)
    return np.exp(- np.linalg.norm(dist)/len(dist))

### prepare dictionary of GCoM cities
# read gcom cities into pandas dataframe
# cities = pd.read_csv(r"C:\Users\roman.hennig\Documents\Workspace\GCoMActionExplorer\gcom_cities.csv", encoding="utf-8")
cities = pd.read_csv(r"gcom_cities.csv", encoding="utf-8")

# select cities with population > pop_cutoff, reset index:
cities = cities.loc[cities['Population'] > pop_cutoff].reset_index(drop=True)

# print(len(cities.index))

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
# actions_df = pd.read_csv(r"C:\Users\roman.hennig\Documents\Workspace\GCoMActionExplorer\Actions_cdp_2012-2017.csv",
                         # encoding="utf-8")
actions_df = pd.read_csv(r"Actions_cdp_2012-2017.csv",
                        encoding="utf-8")

# change USA to United States of America
actions_df = actions_df.replace(to_replace='USA', 
	value='United States of America')

# find set of city names used in the CDP actions file 
# (stripping leading and trailing whitespace)
cdp_cities = set(actions_df['City'].str.strip())
# print(cdp_cities)

### match GCoM cities to cdp action data base
counter = 0
for entry in citiesDict.values():
    gcomCityName = entry['city']
    # match GCOM city to cdp_cities if possible and add list of cdp actions
    if gcomCityName in cdp_cities:
        counter += 1
        cdpId = set(actions_df.loc[actions_df['City'].str.strip() ==
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
        entry['actions'] = findListOfActions(actions_df, entry['new_id'])

print("# of matched cities between GCOM and CDP: " + str(counter))

# find matches for cities
for i, city1_id in enumerate(cities['new_id']):
    for j, city2_id in enumerate(cities['new_id'][i+1:]):
        city1 = citiesDict[city1_id]
        city2 = citiesDict[city2_id]
        sim = similarity(city1, city2)
        if sim > sim_cutoff:
            city1['matches'] += [{'city_id': city2_id, 'score': sim}]
            city2['matches'] += [{'city_id': city1_id, 'score': sim}]

# calculate top ten matches for Salvador and print cities with match scores
top_ten = sorted(citiesDict['BR0003']['matches'], key = lambda k: k['score'], reverse = True)[:10]
print("Top Ten Matches for Salvador, Brazil:")
for entry in top_ten:
    print(citiesDict[entry['city_id']]['city'] + ", " + citiesDict[entry['city_id']]['cc'] + ". Score: {:05.4f}".format(entry['score']))
    # # print all actions that matched cities have taken
    # print("City's actions: ")
    # for action in citiesDict[entry['city_id']]['actions']:
    #     print(action['reporting year'],":",action['category'],":",action['activity'])


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


# creating a visual for Salvadors similarity scores with other cities
sim_scores = list(range(len(cities.index)))
for i, entry in enumerate(citiesDict.values()):
    sim = similarity(citiesDict['BR0003'], entry)
    sim_scores[i] = sim
    if sim > sim_cutoff:
        # print(entry['city'] + ", similarity: {}".format(sim))
        entry['matches'] += ['BR0003']

plt.plot(list(reversed(sorted(sim_scores)[:-1])))
plt.ylabel('Similarity Score')
plt.xlabel('Cities with population > {}'.format(pop_cutoff))
plt.title('Matches for Salvador, Brazil')
plt.show()