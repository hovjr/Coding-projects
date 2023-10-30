import pandas as pd
from openrouteservice import client
import random
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')


pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 50)

# ors setup
api_key = '5b3ce3597851110001cf6248181cfe4bf5a441cbac67b8e4327bcce7'
ors = client.Client(key=api_key)

locations = pd.read_excel(r"DATA/raw_multi.xlsx")

locations[['location_lat', 'location_lng']] = locations['lat_lng'].str.split(',', expand=True)
locations['location_lat'] = locations['location_lat'].apply(lambda x: float(x))
locations['location_lng'] = locations['location_lng'].apply(lambda x: float(x))
locations['coords_rev'] = locations[['location_lng', 'location_lat']].apply(list, axis=1)

cords_list = locations['coords_rev'].to_list()

# heavy goods vehicle
distance_matrices, time_matrices = [], []
ors_matrices = ors.distance_matrix(locations=cords_list,
                               profile='driving-hgv',
                               metrics=['distance', 'duration'])
distance_matrices.append(ors_matrices['distances'])
time_matrices.append(ors_matrices['durations'])

gmp_dm = pd.DataFrame(distance_matrices[0])
gmp_tm = pd.DataFrame(time_matrices[0])

occ = locations
occupancy_df = pd.DataFrame()
for i, j in occ.iterrows():
    if occ['type'][i] == 'Depot':
        row = pd.Series(data={'type': 'depot', 'identity': i})
        occupancy_df = pd.concat([occupancy_df, pd.DataFrame([row])], ignore_index=True)
    if occ['type'][i] == 'Garbage':
        occ_perc = random.randint(0, 60)
        for hour in range(0, 24):
            occ_perc += 3
            if occ_perc >= 100:
                occ_perc = 100
            row = pd.Series(data={'type': 'garbage', 'time': hour, 'occupancy': occ_perc, 'identity': i})
            occupancy_df = pd.concat([occupancy_df, pd.DataFrame([row])], ignore_index=True)
