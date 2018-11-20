import pandas as pd
import csv


### parameters
# population cutoff for GCOM cities:
pop_cutoff = 10000

# read cdp actions file into pandas
actions = pd.read_excel(r"input_data\cdp_actions.xlsx", encoding="utf-8").fillna(0)
# change USA to United States of America and UK to United Kingdom
actions = actions.replace(to_replace='USA', value='United States of America')
actions = actions.replace(to_replace='UK', value='United Kingdom')
actions = actions.replace(to_replace='Hong Kong', value='China, Hong Kong SAR')

actions_copy = actions.copy()

cities  = pd.read_csv(r"input_data\gcom_cities.csv", encoding="utf-8").fillna('(blank)')
# select cities with population > pop_cutoff, reset index:
cities = cities.loc[cities['Population'] > pop_cutoff].reset_index(drop=True)

# create dictionary of city names with city id's as keys
citiesDict = dict(zip(list(cities['new_id']), list(cities['city'])))

# create dictionary of countries of the cities with city id's as keys
countriesDict = dict(zip(list(cities['new_id']), list(cities['country'])))

### set up categories
# read category matching from file
categories = pd.read_csv(r"reclassification_files\cdp_sector_reclass.csv", encoding="utf-8").fillna('(blank)')
# build dict
categoryDict = dict(zip(list(categories['CDP Sector']), list(categories['reclass_sector'])))

print(actions.tail(5))

with open('cdp_actions_mod.csv', 'w', newline='', encoding="utf-8") as csvfile:
    csvwriter = csv.writer(csvfile)
    for index, row in actions.iterrows():
        category = row[3]
        # update categories to our system
        if category == 0 or category == '0':
            row[3] = 'unknown'
        else:
            row[3] = categoryDict[category]
        city    = row[0]
        country = row[1]
        # this line checks the GCOM file for exact name matches
        exact_matches = [city_id for (city_id, city_name) in citiesDict.items()
                         if city_name == city]
        # if there are one or more matches, check whether the country matches
        if len(exact_matches) > 0:
            for city_id in exact_matches:
                if countriesDict[city_id] == country:
                    row[11] = city_id
        # select usability based on count of characters in description
        descriptionChars = row[13]
        if descriptionChars < 31:
            row[14] = 'low'
        elif descriptionChars < 101:
            row[14] = 'medium'
        else:
            row[14] = 'high'
        csvwriter.writerow(row)


# actions_copy.to_excel('cdp_actions_mod.xlsx')