import numpy as np
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from openrouteservice import client
import geopy.distance
import os
# os.chdir(os.getcwd() + '/Vehicle Routing')

api_key = '5b3ce3597851110001cf6248181cfe4bf5a441cbac67b8e4327bcce7'
ors = client.Client(key=api_key)

occupancy = pd.read_excel(r'DATA/occupancy.xlsx')

dm = pd.read_excel(r'DATA/dm_multi.xlsx').astype('int64')
dt = pd.read_excel(r'DATA/tm_multi.xlsx').astype('int64')
locations = pd.read_excel(r"DATA/locations_multi.xlsx")
vehicle_info = pd.read_excel(r"DATA/vehicles.xlsx")
hex_colours = ['#6b5b95', '#feb236', '#d64161', '#82b74b', '#405d27', '#bc5a45', '#FF8C00', '#48D1CC', '#FF7F50', '#0000FF']

locations['cordsj'] = list(zip(locations.location_lat, locations.location_lng))

def create_data_model(time, active_depots):

    data = {}

    all_depots = vehicle_info.parent_depot.unique().tolist()
    tmp = vehicle_info[vehicle_info['parent_depot'].isin(active_depots)]

    occupancy['collect_flag'] = np.where((occupancy['time'] == time) & (occupancy['occupancy'] >= 80), 1, 0)
    uncollected = occupancy[(occupancy['time'] == time) & (occupancy['collect_flag'] == 0)]
    full_bins = occupancy[occupancy['collect_flag'] == 1]['identity']

    data['distance_matrix'] = dm.loc[all_depots + full_bins.tolist(), all_depots + full_bins.tolist()].values.tolist()

    data['demands'] = occupancy[(occupancy['time'] == time) & (occupancy['identity'].isin(full_bins.tolist()))]['occupancy'].tolist()
    for i in all_depots: data['demands'].insert(i, 0)
    data['ids'] = occupancy[(occupancy['time'] == time) & (occupancy['identity'].isin(full_bins.tolist()))]['identity'].tolist()
    for i in all_depots: data['ids'].insert(i, i)
    data['vehicle_capacities'] = tmp.capacity.to_list()
    data['num_vehicles'] = tmp.shape[0]
    data['starts'] = data['ends'] = tmp.parent_depot.to_list()

    data['vehicle_seed_id'] = tmp.vehicle_id.to_list()

    return data, uncollected


def print_solution(data, manager, routing, solution):
    total_distance = 0
    total_load = 0
    final_df = pd.DataFrame()
    count = 1

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_distance, route_load = 0, 0
        sequence, load_sequence, dist_from_prev_sequence = [], [], []

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            sequence.append(node_index)
            node_demand = data['demands'][node_index]
            print('vid:', vehicle_id, 'node_id', node_index, 'data id: ', data['ids'][node_index])
            print(node_demand, data['vehicle_seed_id'], index)
            load_sequence.append(node_demand)
            route_load += node_demand

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            print(previous_index, index, vehicle_id)
            ############### fix
            # route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route_distance += 637
            print(routing.GetArcCostForVehicle(previous_index, index, vehicle_id), route_distance)

        if route_distance > 0: count += 1
        if len(sequence) == 1: continue

        total_distance += route_distance
        total_load += route_load

        id_sequence = [data['ids'][i] for i in sequence]
        tmp_df = pd.concat([pd.DataFrame([id_sequence], columns=["poi" + str(sub) for sub in pd.DataFrame([id_sequence]).columns]),
                            pd.DataFrame([load_sequence], columns=["node_demand" + str(sub) for sub in pd.DataFrame([load_sequence]).columns])], axis=1)
        final_df = pd.concat([final_df, tmp_df])
        final_df = final_df.reset_index(drop=True)

        last_idx = final_df.shape[0] - 1
        final_df.loc[last_idx, 'seed_vid'] = data['vehicle_seed_id'][vehicle_id]
        final_df.loc[last_idx, 'total_distance'] = route_distance
        final_df.loc[last_idx, 'total_load'] = route_load
        final_df.loc[last_idx, 'color'] = hex_colours[last_idx]

    plot_df = pd.wide_to_long(final_df.reset_index(), ["poi", "node_demand"], i=['index', 'seed_vid', 'color', 'total_distance', 'total_load'], j="step").reset_index()
    plot_df = plot_df.rename(columns={"index": "vehicle_id"})
    plot_df = plot_df[plot_df['poi'].notnull()]
    plot_df['vehicle_id'] = plot_df['vehicle_id'] + 1

    return final_df, plot_df


def search_fill(optimized, remaining, gjson, final_df):

    not_collected = remaining['identity'].to_list()
    additional_visits = []

    for i in range(0, max(optimized['vehicle_id'].astype(int))):
        remaining_cap = 500 - final_df['total_load'][i]
        all_bins, collect = [], []

        if remaining_cap > min(remaining['occupancy']):
            for cord in gjson[i]['features'][0]['geometry']['coordinates']:
                t1 = (cord[1], cord[0])
                for bin in not_collected:
                    t2 = locations['cordsj'][bin]
                    distance = geopy.distance.geodesic(t1, t2).meters
                    if distance <= 300: all_bins.append(bin)

        fetched_nodes = remaining[remaining['identity'].isin(all_bins)].sort_values(by='occupancy', ascending=False)
        for bin in fetched_nodes['identity'].to_list():
            load = np.select(fetched_nodes['identity'] == bin, fetched_nodes['occupancy'])
            if remaining_cap > load:
                collect.append(bin)
                not_collected.pop(not_collected.index(bin))
                remaining_cap = remaining_cap - load
            elif remaining_cap < min(fetched_nodes['occupancy']):
                break

        additional_visits.append(collect)

    return additional_visits


def create_fill_data(updated_nodes, time, seed_vid):

    used_depot = np.select(vehicle_info['vehicle_id'] == seed_vid, vehicle_info['parent_depot'])

    data_fill = {}
    data_fill['distance_matrix'] = dm.loc[updated_nodes, updated_nodes].values.tolist()
    updated_nodes.pop(0)
    data_fill['demands'] = occupancy[(occupancy['time'] == time) & (occupancy['identity'].isin(updated_nodes))]['occupancy'].tolist()
    data_fill['demands'].insert(0, 0)
    data_fill['ids'] = occupancy[(occupancy['time'] == time) & (occupancy['identity'].isin(updated_nodes))]['identity'].tolist()
    data_fill['ids'].insert(0, used_depot)
    data_fill['vehicle_capacities'] = [np.select(vehicle_info['vehicle_id']==seed_vid, vehicle_info['capacity'])]
    print(data_fill['vehicle_capacities'])
    data_fill['num_vehicles'] = 1
    data_fill['starts'] = data_fill['ends'] = [0]
    data_fill['vehicle_seed_id'] = [seed_vid]

    return data_fill


def cvrp(shift, active_depots=[], seed_vid=-1, updated_nodes=[], flag=False):

    active_depots = [int(i) for i in active_depots]
    # if updated_nodes is None:
    #     updated_nodes = []
    uncollected = []
    break_reason = ""

    if flag == False:
        data, uncollected = create_data_model(time=shift, active_depots=active_depots)
        if len(data['demands']) == 1:
            break_reason = "All garbage bins' occupancy under collection threshold"

    elif flag == True:
        data = create_fill_data(updated_nodes, time=shift, seed_vid=seed_vid)

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['starts'], data['ends'])
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_callback_index,
                                            0,  # null capacity slack
                                            data['vehicle_capacities'],  # vehicle maximum capacities
                                            True,  # start cumul to zero
                                            'Capacity')

    # to prevent route from including a depot that didnt release a vehicle
    penalty = 100
    for depot in [0, 1, 2]: # active depots
        routing.AddDisjunction([manager.NodeToIndex(depot)], penalty)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(1)

    solution = routing.SolveWithParameters(search_parameters)

    final_df, plot_df = pd.DataFrame(), pd.DataFrame()
    gjson_list = []
    if solution and break_reason != "All garbage bins' occupancy under collection threshold":
        final_df, plot_df = print_solution(data, manager, routing, solution)

        # plot_df['cords_lat'], plot_df['cords_lng'] = float(), float()
        for i, j in plot_df.iterrows():
            poi = plot_df['poi'][i]
            if plot_df['step'][i] == 0:
                vehicle_depot = data['starts'][plot_df['vehicle_id'][i]-1]
                plot_df.loc[i, 'cords_lat'] = locations['location_lat'][vehicle_depot]
                plot_df.loc[i, 'cords_lng'] = locations['location_lng'][vehicle_depot]
            else:
                plot_df.loc[i, 'cords_lat'] = locations['location_lat'][poi]
                plot_df.loc[i, 'cords_lng'] = locations['location_lng'][poi]

        plot_df['marker_col'] = '#101DB9'
        plot_df.loc[plot_df['step'] == 0, 'marker_col'] = '#332929'

        gjson_list = []
        nofv = int(max(plot_df['vehicle_id']))
        for i in range(1, nofv + 1):
            temp = plot_df[plot_df['vehicle_id'] == i]
            cords_seq = list(temp[['cords_lng', 'cords_lat']].apply(list, axis=1))
            gjson_list.append(ors.directions(**{
                'coordinates': cords_seq,
                'profile': 'driving-hgv',
                'instructions': 'false',
                'format_out': 'geojson'
            }))

    elif not solution:
        break_reason = "Please increase available vehicles"

    return final_df, plot_df, gjson_list, break_reason, uncollected


def fill_route(plot_df, final_df, uncollected, gjson_list, time):

    additional = search_fill(plot_df, uncollected, gjson_list, final_df)

    vehicles_final = final_df.shape[0]

    final_df_new, plot_df_new = pd.DataFrame(), pd.DataFrame()
    gjson_list_new = []

    for i in range(0, vehicles_final):

        if len(additional[i]) != 0:
            seed_vid = final_df['seed_vid'][i]
            nodes = plot_df[plot_df['vehicle_id'] == i + 1]['poi'].tolist()
            nodes.extend(additional[i])
            final_df_stg, plot_df_stg, gjson_list_stg, break_re, uncollected_stg = cvrp(updated_nodes=nodes, shift=time, flag=True, seed_vid=seed_vid)

        else:
            final_df_stg = final_df.loc[i:i, :].copy()
            plot_df_stg = plot_df[plot_df['vehicle_id']==i+1].copy()
            gjson_list_stg = gjson_list[i]

        final_df_stg['color'] = hex_colours[i]
        final_df_new = pd.concat([final_df_new, final_df_stg])
        plot_df_stg["vehicle_id"] = plot_df_stg["vehicle_id"] = i + 1
        plot_df_stg['color'] = hex_colours[i]
        plot_df_new = pd.concat([plot_df_new, plot_df_stg])
        gjson_list_new.append(gjson_list_stg)

    plot_df_new.loc[~plot_df_new.poi.isin(plot_df.poi), ['marker_col']] = '#ED5555'
    final_df_new = final_df_new.reset_index(drop=True)

    return final_df_new, plot_df_new, gjson_list_new


# final_df, plot_df, gjson, r, uncollected = cvrp(shift=14, active_depots=['0', '2'])
# final_df_n, plot_df_n, gjson_n = fill_route(plot_df, final_df, uncollected, gjson, time=14)
