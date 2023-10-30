import os
from datetime import datetime, timedelta
import datetime as dt
import numpy as np
import pandas as pd
import itertools
import ast
from openrouteservice import client
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')

api_key = '5b3ce3597851110001cf6248181cfe4bf5a441cbac67b8e4327bcce7'
ors = client.Client(key=api_key)

pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 50)

hotels = pd.read_excel(r'DATA/hotels_mod.xlsx', usecols=['title'])
short_df = pd.read_excel(r'DATA/aois_short.xlsx')
aois_times = pd.read_excel(r"DATA/pop_times_mod.xlsx")
tsp_dfs = pd.read_excel(r'DATA/tsp_dfs.xlsx')
restaurants = pd.read_excel(r"DATA/restaurants_mod.xlsx")
hex_colours = ['#6b5b95', '#feb236', '#d64161', '#82b74b', '#405d27', '#bc5a45', '#FF8C00', '#48D1CC', '#FF7F50', '#0000FF']

# parse lists
for i, j in tsp_dfs.iterrows():
    tsp_dfs['ndf'][i] = ast.literal_eval(tsp_dfs['ndf'][i])
    tsp_dfs['time_matrix_walking'][i] = ast.literal_eval(tsp_dfs['time_matrix_walking'][i])
    tsp_dfs['distance_matrix_walking'][i] = ast.literal_eval(tsp_dfs['distance_matrix_walking'][i])
    tsp_dfs['time_matrix_driving'][i] = ast.literal_eval(tsp_dfs['time_matrix_driving'][i])
    tsp_dfs['distance_matrix_driving'][i] = ast.literal_eval(tsp_dfs['distance_matrix_driving'][i])
    tsp_dfs['coords'][i] = ast.literal_eval(tsp_dfs['coords'][i])
    tsp_dfs['coords_lat'][i] = ast.literal_eval(tsp_dfs['coords_lat'][i])
    tsp_dfs['coords_lng'][i] = ast.literal_eval(tsp_dfs['coords_lng'][i])

def choose_visits(start, visits):
    st_idx = hotels.title.to_list().index(start)

    vis_idx = []
    for aoi in visits:
        vis_idx.append(tsp_dfs['ndf'][0].index(aoi))

    routes = list(itertools.permutations(vis_idx, len(vis_idx)))

    count = 0
    for i in routes:
        routes[count] = list(i)
        routes[count].insert(0, 0)
        count += 1

    type_flag = 'optimal'

    choose_visits_c = []
    choose_visits_c.append(st_idx)
    choose_visits_c.append(routes)
    choose_visits_c.append(type_flag)

    return choose_visits_c

def suggest_visits(stpoint, n_of_visits, available_hours, path_contains=[]):
    st_idx = hotels.title.to_list().index(stpoint)
    aoi_idx = range(1, len(tsp_dfs['ndf'][0]))
    routes = list(itertools.combinations(aoi_idx, n_of_visits))
    # routes2 = list(itertools.permutations(perm) for perm in routes)

    count = 0
    for i in routes:
        routes[count] = list(i)
        routes[count].insert(0, 0)
        count += 1

    type_flag = 'suggestions'

    if path_contains is not None:
        for i, x in enumerate(path_contains):
            path_contains[i] = tsp_dfs['ndf'][0].index(path_contains[i])

    suggest_visits_c = []

    suggest_visits_c.append(st_idx)
    suggest_visits_c.append(routes)
    suggest_visits_c.append(available_hours)
    suggest_visits_c.append(type_flag)
    suggest_visits_c.append(path_contains)

    return suggest_visits_c

def solve_tsp(st_idx, routes, rest_time, rest_distance, rest_length, start_time, trans_type):
    # MAIN DF

    matrix_distance = "distance_matrix_" + trans_type.lower()
    matrix_time = "time_matrix_" + trans_type.lower()

    start_time = pd.to_datetime(start_time)

    indexes, path_titles, co_seq, route_time_s, route_time_dt, rest_info, node_arr_times_dt, node_arr_times, \
    node_dep_times_dt, node_dep_times, cumul_arr_time, cumul_dep_time, route_distance, distance_to, cumul_distance, end_time \
        = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []

    for combo in routes:

        time_of_arrival, cumulative_time_s, cum_arr_t, cum_dep_t, distance_of_path = 0, 0, 0, 0, 0
        index_title, cords_list = [], []
        rest_info_dic, nodes_arrival_dt, nodes_arrival_t, nodes_departure_dt, nodes_departure_t, cum_time_arr_dic, cum_time_dep_dic, \
        dist_between_nodes_dic, cum_dist_dic = dict([]), dict([]), dict([]), dict([]), dict([]), dict([]), dict([]), dict([]), dict([])
        previous = 0
        cumulative_time_eest = start_time
        break_flag = False

        for to_node in combo:

            # variables for entry + stay lookup
            cur_day = str(pd.Timestamp(cumulative_time_eest).day_name())[:2]
            cur_hour = int(cumulative_time_eest.strftime("%H"))
            node_title = tsp_dfs['ndf'][st_idx][to_node]
            previous_title = tsp_dfs['ndf'][st_idx][previous]
            entry = np.select((aois_times['hour_index'] == cur_hour) & (aois_times['day_index'] == cur_day)
                              & (aois_times['title'] == node_title), aois_times['entry_time'], 0)
            stay = np.select((aois_times['hour_index'] == cur_hour) & (aois_times['day_index'] == cur_day)
                             & (aois_times['title'] == node_title), aois_times['expected_stay'], 0)

            # path titles
            index_title.append(node_title)

            # path coordinates
            cords_list.append(tsp_dfs['coords'][st_idx][to_node])

            rest = 0

            if ((rest_time < cum_arr_t) | (rest_distance < distance_of_path)) & (break_flag == False):
                # rest before visit
                rest_info_dic['where'] = previous_title
                rest_info_dic['when'] = 'before visit'
                rest_info_dic['length'] = pd.to_datetime(rest_length, unit='s').strftime('%H:%M')
                rest = rest_length
                break_flag = True

            elif (rest_time < cum_dep_t) & (break_flag == False):
                # rest after visit
                rest_info_dic['where'] = previous_title
                rest_info_dic['when'] = 'after visit'
                rest_info_dic['length'] = pd.to_datetime(rest_length, unit='s').strftime('%H:%M')
                rest = rest_length
                break_flag = True

            # EEST time of arrival at node - finaldf['node_arrival_eest']
            time_to_node = tsp_dfs[matrix_time][st_idx][previous][to_node]
            time_of_arrival = cumulative_time_eest + timedelta(seconds=time_to_node)
            nodes_arrival_dt[node_title] = time_of_arrival
            nodes_arrival_t[node_title] = time_of_arrival.strftime('%H:%M')

            # cumulative travel time to node in seconds - finaldf['cumulative_arrival_time_s']
            cum_arr_t = int((time_of_arrival - start_time).total_seconds())
            cum_time_arr_dic[node_title] = cum_arr_t

            # EEST time of departure from node - finaldf['node_departure_eest']
            time_for_departure = entry + stay + rest
            cumulative_time_eest += timedelta(seconds=(time_to_node + time_for_departure))
            nodes_departure_dt[node_title] = cumulative_time_eest
            nodes_departure_t[node_title] = cumulative_time_eest.strftime('%H:%M')
            eta_end = cumulative_time_eest.strftime('%H:%M')

            # cumulative departure time from node in seconds - finaldf['cumulative_departure_time_s']
            cum_dep_t = int((cumulative_time_eest - start_time).total_seconds())
            cum_time_dep_dic[node_title] = cum_dep_t

            # cumulative distance at node - finaldf['path_dist_meters']
            distance_from_prev = tsp_dfs[matrix_distance][st_idx][previous][to_node]
            distance_of_path += distance_from_prev
            cum_dist_dic[node_title] = distance_of_path

            # distance between two nodes - to_node's distance from previous (m) - finaldf['distance_between_nodes']
            dist_between = int(distance_from_prev)
            dist_between_nodes_dic[node_title] = dist_between
            previous = to_node

        total_time_s = int((cumulative_time_eest - start_time).total_seconds())
        total_time_dt = total_time_s/3600
        indexes.append(combo)
        path_titles.append(index_title)
        co_seq.append(cords_list)
        route_time_s.append(total_time_s)
        route_time_dt.append(total_time_dt)
        rest_info.append(rest_info_dic)
        node_arr_times_dt.append(nodes_arrival_dt)
        node_arr_times.append(nodes_arrival_t)
        node_dep_times_dt.append(nodes_departure_dt)
        node_dep_times.append(nodes_departure_t)
        cumul_arr_time.append(cum_time_arr_dic)
        cumul_dep_time.append(cum_time_dep_dic)
        route_distance.append(int(distance_of_path))
        distance_to.append(dist_between_nodes_dic)
        cumul_distance.append(cum_dist_dic)
        end_time.append(eta_end)

    final_df = pd.DataFrame({'path_indexes': indexes, 'path_titles': path_titles, 'cords_sequence': co_seq,
                             'route_time_s': route_time_s, 'route_time_dt': route_time_dt,
                             'rest_info': rest_info, 'node_arrival_sys': node_arr_times_dt,
                             'node_departure_sys': node_dep_times_dt, 'node_arrival_eest': node_arr_times,
                             'node_departure_eest': node_dep_times, 'arrival_time_s': cumul_arr_time,
                             'departure_time_s': cumul_dep_time, 'path_dist_meters': route_distance,
                             'distance_between_nodes': distance_to, 'cumulative_node_dist': cumul_distance,
                             'eta_end': end_time})

    return final_df

def get_solution(final_df, st_idx, type_flag, trans_type, available_hours=0, path_contains=[]):
    if type_flag == "optimal":

        optimal_idx = final_df['route_time_s'].idxmin()
        route_info_all = final_df[final_df.index.isin([optimal_idx])].reset_index(drop=True)

        if trans_type == 'Walking':
            dir_profile = 'foot-walking'
        elif trans_type == 'Driving':
            dir_profile = 'driving-car'
        # print(route_info_all['cords_sequence'][0])
        gjson = ors.directions(**{
            'coordinates': route_info_all['cords_sequence'][0],
            'profile': dir_profile,
            'instructions': 'false',
            'format_out': 'geojson'
        })

        output_df = pd.DataFrame()
        count = 0

        for idx in route_info_all['path_indexes'][0]:
            node_title = tsp_dfs['ndf'][st_idx][idx]
            row = pd.Series(data={'title': node_title,
                                  'cords_lat': tsp_dfs['coords_lat'][st_idx][idx],
                                  'cords_lng': tsp_dfs['coords_lng'][st_idx][idx],
                                  'node_arrival_eest': route_info_all['node_arrival_eest'][0][node_title],
                                  'node_departure_eest': route_info_all['node_departure_eest'][0][node_title],
                                  'arrival_time_s': route_info_all['arrival_time_s'][0][node_title],
                                  'distance_from_previous': route_info_all['distance_between_nodes'][0][node_title],
                                  'cumulative_node_dist': route_info_all['cumulative_node_dist'][0][node_title],
                                  'stop_count': "Visit #" + str(count),
                                  'color': hex_colours[count]
                                  })

            output_df = pd.concat([output_df, pd.DataFrame([row])], ignore_index=True)
            output_df.loc[0, 'stop_count'] = 'Starting point'

            count += 1

        return output_df, route_info_all, gjson

    elif type_flag == "suggestions":

        available_s = available_hours * 60 * 60

        suggestions_df = final_df[final_df['path_indexes'].apply(lambda x: set(path_contains).issubset(x))]
        suggestions_df = suggestions_df[suggestions_df['route_time_s'] < available_s]
        suggestions_df = suggestions_df.sort_values(by=['route_time_s']).head(5).reset_index(drop=True).copy()

        if trans_type == 'Walking':
            dir_profile = 'foot-walking'
        elif trans_type == 'Driving':
            dir_profile = 'driving-car'

        suggestions_gjson = []
        suggestions_out = pd.DataFrame()
        route_idx = 1
        for row, col in suggestions_df.iterrows():
            suggestions_gjson.append(ors.directions(**{
                'coordinates': suggestions_df['cords_sequence'][row],
                'profile': dir_profile,
                'instructions': 'false',
                'format_out': 'geojson'
            }))

            count = 0
            for idx in suggestions_df['path_indexes'][row]:
                node_title = tsp_dfs['ndf'][st_idx][idx]
                new_row = pd.Series(data={'route_index': route_idx,
                                          'title': node_title,
                                          'cords_lat': tsp_dfs['coords_lat'][st_idx][idx],
                                          'cords_lng': tsp_dfs['coords_lng'][st_idx][idx],
                                          'node_arrival_eest': suggestions_df['node_arrival_eest'][row][node_title],
                                          'node_departure_eest': suggestions_df['node_departure_eest'][row][node_title],
                                          'arrival_time_s': suggestions_df['arrival_time_s'][row][node_title],
                                          'distance_from_previous': suggestions_df['distance_between_nodes'][row][node_title],
                                          'cumulative_node_dist': suggestions_df['cumulative_node_dist'][row][node_title],
                                          'stop_count': "Visit #" + str(count),
                                          'color': hex_colours[count]
                                          })

                suggestions_out = pd.concat([suggestions_out, pd.DataFrame([new_row])], ignore_index=True)

                count += 1

            suggestions_out.replace({'stop_count': 'Visit #0'}, 'Starting point', inplace=True)

            route_idx += 1

        return suggestions_out, suggestions_df, suggestions_gjson

def gant_table(route_info, type_flag, trans_type):

    gant_choose = pd.DataFrame()

    if type_flag == "optimal":

        # rest_spot = route_info['rest_info']['where']

        for count, value in enumerate(route_info['path_indexes'][0]):

            current_node_title = route_info['path_titles'][0][count]
            arrival_time_current = route_info['node_arrival_sys'][0][current_node_title]

            if count == 0:
                row = pd.Series(data={'title': current_node_title,
                                      'start': arrival_time_current,
                                      'end': arrival_time_current,
                                      'color': hex_colours[count]
                                      })

                gant_choose = pd.concat([gant_choose, pd.DataFrame([row])], ignore_index=True)


            elif count > 0:

                previous_node_title = route_info['path_titles'][0][count - 1]
                previous_departure = route_info['node_departure_sys'][0][previous_node_title]
                start_next = route_info['node_departure_sys'][0][current_node_title]

                row1 = pd.Series(data={'title': trans_type.capitalize(),
                                       'start': previous_departure,
                                       'end': arrival_time_current,
                                       'color': '92a8d1'})
                row2 = pd.Series(data={'title': current_node_title,
                                       'start': arrival_time_current,
                                       'end': start_next,
                                       'color': hex_colours[count]})

                gant_choose = pd.concat([gant_choose, pd.DataFrame([row1])], ignore_index=True)
                gant_choose = pd.concat([gant_choose, pd.DataFrame([row2])], ignore_index=True)

        return gant_choose

    if type_flag == "suggestions":

        gant_suggest = []

        for idx in range(0, len(route_info)):

            gant_df = pd.DataFrame()

            for count, value in enumerate(route_info['path_indexes'][idx]):

                current_node_title = route_info['path_titles'][idx][count]
                arrival_time_current = route_info['node_arrival_sys'][idx][current_node_title]

                if count == 0:
                    row = pd.Series(data={'title': current_node_title,
                                          'start': arrival_time_current,
                                          'end': arrival_time_current,
                                          'color': hex_colours[count]
                                          })

                    gant_df = pd.concat([gant_df, pd.DataFrame([row])], ignore_index=True)

                elif count > 0:

                    previous_node_title = route_info['path_titles'][idx][count - 1]
                    previous_departure = route_info['node_departure_sys'][idx][previous_node_title]
                    start_next = route_info['node_departure_sys'][idx][current_node_title]

                    row1 = pd.Series(data={'title': trans_type.capitalize(),
                                           'start': previous_departure,
                                           'end': arrival_time_current,
                                           'color': '#92a8d1'})
                    row2 = pd.Series(data={'title': current_node_title,
                                           'start': arrival_time_current,
                                           'end': start_next,
                                           'color': hex_colours[count]})

                    gant_df = pd.concat([gant_df, pd.DataFrame([row1])], ignore_index=True)
                    gant_df = pd.concat([gant_df, pd.DataFrame([row2])], ignore_index=True)

            gant_suggest.append(gant_df)

        return gant_suggest

# # suggest
# stid, routes, availhr, typefl, mustcon = suggest_visits(stpoint='360 Degrees Hotel', n_of_visits=3,
# available_hours=8, path_contains=['Parthenon']) #, path_contains=['Ancient Salamis Port'],'Penteli cave (Daveli)', path_contains=['Parnitha Mola Location']
#
# df = solve_tsp(st_idx=2, routes=routes, rest_time=100000, rest_distance=200000, rest_length=1800, start_time = '2022-05-10 09:00:00', trans_type='Driving')
# sugg_out, suggestions_df, sug_json = get_solution(available_hours=8, st_idx=2, final_df=df, trans_type='Driving', type_flag='suggestions', path_contains=mustcon) #
# sugant = gant_table(route_info=suggestions_df, type_flag='suggestions', trans_type='Driving')

# choose
# routes = choose_visits(start='360 Degrees Hotel', visits=['Parthenon', 'Kerameikos Archaeological Site'])[1]
# df = solve_tsp(st_idx=2, routes=routes, rest_time=5000, rest_distance=2500, rest_length=1800, start_time = '2022-05-10 09:00:00', trans_type='Driving')
# out, route_info_all, geoout = get_solution(available_hours=12, st_idx=2, path_contains=[], final_df=df, type_flag='optimal', trans_type='Walking')
# gant = gant_table(route_info=route_info_all, type_flag='optimal', trans_type='driving')
# print(out, '\n', route_info_all)
# print(gant)

# route_info_all.to_excel("G:\\Shared drives\\GR Data & Analytics\\Projects\\Athens CT\\DATA\\TSP\\ganttest.xlsx", index=False)
