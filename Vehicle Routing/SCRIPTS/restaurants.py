import pandas as pd
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')


pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 200)

df = pd.read_excel(r'DATA/restaurants_raw.xlsx')

df = df.filter(regex='openingHours|categories/1|location/lat|location/lng|title|totalScore')

melt = pd.melt(df, id_vars=['location/lat',  'location/lng', 'title', 'totalScore', 'categories/1'],
                   var_name='reference',
                   value_name='value')

melt[['drop1', 'dayvalue', 'reference']] = melt['reference'].str.split("/", expand=True)
melt.drop(columns=['drop1'], inplace=True)

df1 = melt[melt['reference']=='day'].copy()
# df1['value'] = df1['value'].map(lambda x: str(x)[:-1])

df2 = melt[melt['reference']=='hours']

final = pd.merge(df1, df2, on=['location/lat',  'location/lng', 'title', 'totalScore', 'dayvalue', 'categories/1'])

final = final.drop(columns=['reference_x', 'reference_y', 'dayvalue'])
final = final.rename(columns={'value_x': 'day', 'value_y': 'openinghours', 'categories/1': 'category',
                              'location/lat': 'latitude_cords', 'location/lng': 'longitude_cords'})

final = final.dropna(subset=['totalScore', 'category']).reset_index(drop=True)
closed = final[final['openinghours'] == 'Closed']['title'].unique()
# final = final[final['totalScore']>4.3].reset_index(drop=True)
final = final[~final['title'].isin(closed)].reset_index(drop=True)
# final.title.nunique()

# final.to_excel(r'DATA/restaurants_mod.xlsx', index=False)
