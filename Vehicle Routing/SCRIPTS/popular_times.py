import pandas as pd
import numpy as np
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')


pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 200)

aois_short = pd.read_excel(r"DATA/aois_short.xlsx")
df = pd.read_excel(r"DATA/landmarks.xlsx")
df = df[df['title'].isin(aois_short['title'])]

df = df.rename(columns={'title': 'title2', 'totalScore': 'totalScore2'}).reset_index(drop=True)
df = df.filter(regex='categories/1|location/lat|location/lng|title2|totalScore2|popularTimesHistogram')  # ---------- title expected_stay|
df = df.fillna(method='bfill')
df = df.rename(columns={'title2': 'title', 'totalScore2': 'totalScore'}).reset_index(drop=True)
df = pd.merge(df, aois_short[['title', 'expected_stay']], on=['title'], how='inner')

melt = pd.melt(df, id_vars=['location/lat',  'location/lng', 'title', 'expected_stay'],
                   var_name='day_hour_pop',
                   value_name='value')
melt[['drop1', 'day', 'drop2', 'type']] = melt['day_hour_pop'].str.split("/", expand=True)
hourdf = melt[melt['type'] == 'hour'].copy()
hourdf.rename(columns={'value': 'hour'}, inplace=True)
hourdf.drop(columns=['drop1', 'type', 'day_hour_pop'], inplace=True)
percdf = melt[melt['type'] == 'occupancyPercent'].copy()
percdf.rename(columns={'value': 'pop_value'}, inplace=True)
percdf.drop(columns=['drop1', 'type', 'day_hour_pop'], inplace=True)

pop_times_aoi = pd.merge(hourdf, percdf, on=['location/lat',  'location/lng', 'title', 'day', 'drop2', 'expected_stay'], how='inner')
pop_times_aoi.drop(columns=['drop2'], inplace=True)
pop_times_aoi.rename(columns={'hour': 'hour_index', 'day': 'day_index'}, inplace=True)

# implement waiting in line individual entry time for each aoi
pop_times_aoi['entry_time'] = 600 * pop_times_aoi['pop_value'] / 70
pop_times_aoi['entry_time'].fillna(0, inplace=True)
pop_times_aoi = pop_times_aoi.sort_values(['title', 'day_index', 'hour_index'])

# stay time mesos oros xronou pou tha katsei sto aksiotheato -> individual xronos * const = stay time
# pop_times_aoi['stay_time'] = pop_times_aoi['expected_stay'] * # coeff

# pop_times_aoi.to_excel(r'DATA/pop_times_mod.xlsx', index=False)
