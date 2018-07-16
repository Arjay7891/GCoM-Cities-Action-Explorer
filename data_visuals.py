import csv
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import seaborn as sns
import matplotlib.pyplot as plt

### parameters
# population cutoff for cities:
pop_cutoff = 0


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

visual_variable = "Population"

x = pd.Series(cities[visual_variable], name = visual_variable)
sns.distplot(x, bins=50, kde=False).set_title("Distribution of {} of GCOM cities "
                          "with population > {}".format(visual_variable, pop_cutoff))
plt.show()

# apply log transformation
cities[log_transform] \
    = cities[log_transform].apply(np.log)

# x = pd.Series(cities[visual_variable], name = 'log of {}'.format(visual_variable))
# sns.distplot(x, bins=50, kde=False).set_title("Distribution of {} of GCOM cities with population > {}"
#     " after a log transform".format(visual_variable, pop_cutoff))
# plt.show()

# perform feature scaling:
cities[feature_scaling] \
    = StandardScaler().fit_transform(cities[feature_scaling])

x = pd.Series(cities[visual_variable], name = 'Scaled log of {}'.format(visual_variable))
sns.distplot(x, bins=50, kde=False).set_title("Distribution of {} of GCOM cities with population > {}"
    " after a log transform and feature scaling".format(visual_variable, pop_cutoff))
plt.show()
