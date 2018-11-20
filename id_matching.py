import pandas as pd

### parameters
# population cutoff for GCOM cities:
pop_cutoff = 10000

# read action and cities files into pandas data frames, replacing empty fields with "'blank'"
actions = pd.read_excel(r"input_data\Actions_db2.xlsx", encoding="utf-8").fillna('(blank)')
# change USA to United States of America and UK to United Kingdom
actions = actions.replace(to_replace='USA', value='United States of America')
actions = actions.replace(to_replace='UK', value='United Kingdom')
actions = actions.replace(to_replace='Hong Kong', value='China, Hong Kong SAR')

# add new placeholder columns for match result

cities  = pd.read_csv(r"input_data\gcom_cities.csv", encoding="utf-8").fillna('(blank)')
# select cities with population > pop_cutoff, reset index:
cities = cities.loc[cities['Population'] > pop_cutoff].reset_index(drop=True)

# create dictionary of city names with city id's as keys
citiesDict = dict(zip(list(cities['new_id']), list(cities['city'])))

# create dictionary of countries of the cities with city id's as keys
countriesDict = dict(zip(list(cities['new_id']), list(cities['country'])))

# looping through all city names in the actions file, check whether these are in
# the GCOM cities
for index, row in actions.iterrows():
    city    = row[0]
    country = row[1]
    # this line checks the GCOM file for exact name matches
    exact_matches = [city_id for (city_id, city_name) in citiesDict.items()
                     if city_name == city]
    # if there are one or more matches, check whether the country matches
    if len(exact_matches) > 0:
        for city_id in exact_matches:
            if countriesDict[city_id] == country:
                actions.iloc[index]['GCOM ID'] = city_id

actions.to_excel('result.xlsx')

print(citiesDict['AL0002'])

