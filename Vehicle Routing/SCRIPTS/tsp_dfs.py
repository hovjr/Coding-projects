import pandas as pd
from openrouteservice import client
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')


pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 50)

# ors setup
api_key = '5b3ce3597851110001cf6248181cfe4bf5a441cbac67b8e4327bcce7'
ors = client.Client(key=api_key)

# READ DATA
keepcols = ['location/lat', 'location/lng', 'title']

aois_times = pd.read_excel(r"DATA/landmarks.xlsx")
aois_times = aois_times.sort_values('reviewsCount', ascending=False)
aois_short = aois_times[['location/lat', 'location/lng', 'title']].head(12).copy()
aois_short = aois_short[aois_short['title']!='Acropolis of Athens']
aois_short['coordsjoin'] = aois_short[['location/lng', 'location/lat']].apply(list, axis=1)
aois_short = aois_short.drop_duplicates(['location/lat', 'location/lng', 'title'])

hotels = pd.read_excel('DATA/hotels_raw.xlsx', usecols=['location/lat', 'location/lng', 'title'])
# hotels = hotels.sort_values(['totalScore', 'reviewsCount'], ascending=False)
hotels = hotels[hotels.title.isin(['360 Degrees Hotel', 'Acropolis View Hotel', 'Four Streets Athens'])]
hotels['coordsjoin'] = hotels[['location/lng', 'location/lat']].apply(list, axis=1)
hotels = hotels.drop_duplicates(['location/lat', 'location/lng', 'title'])

# tsp df for n starting hotels
ndfs = []
for name in hotels['title']:
    df = hotels[hotels['title'] == name]
    ndfs.append(pd.concat([df, aois_short], ignore_index=True))

route_titles = []
for name in hotels['title']:
    titles = []
    titles.append(name)
    for aoi in aois_short['title']:
        titles.append(aoi)
    route_titles.append(titles)

# coordinates for n tsp dfs
ncoordinates, cords_lat, cords_lng = [], [], []
for nstp in ndfs:
    ncoordinates.append(nstp['coordsjoin'].to_list())
    cords_lat.append(nstp['location/lat'].to_list())
    cords_lng.append(nstp['location/lng'].to_list())


# time matrix for each df
time_matrix_walking, time_matrix_driving = [], []
distance_matrix_walking, distance_matrix_driving = [], []
for group in ncoordinates:
    temp = ors.distance_matrix(locations=group,
                               profile='foot-walking',
                               metrics=['distance', 'duration'])
    time_matrix_walking.append(temp['durations'])
    distance_matrix_walking.append(temp['distances'])

    temp2 = ors.distance_matrix(locations=group,
                               profile='driving-car',
                               metrics=['distance', 'duration'])
    time_matrix_driving.append(temp2['durations'])
    distance_matrix_driving.append(temp2['distances'])

# df
tsp_dfs = pd.DataFrame({'ndf': route_titles, 'coords': ncoordinates, 'coords_lng': cords_lng, 'coords_lat': cords_lat,
                        'time_matrix_walking': time_matrix_walking, 'distance_matrix_walking': distance_matrix_walking,
                        'time_matrix_driving': time_matrix_driving, 'distance_matrix_driving': distance_matrix_driving})

# aois_short.to_excel(r'DATA/aois_short.xlsx', index=False)
# tsp_dfs.to_excel(r'DATA/tsp_dfs.xlsx', index=False)

