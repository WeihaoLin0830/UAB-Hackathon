from rtree import index
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import LineString
from shapely.geometry import Point
import osmnx as ox
from shapely.geometry import Polygon
import networkx as nx
import folium
import math


"""def load_crimes_geojson(file_path):
    return gpd.read_file(file_path)

buffer = load_crimes_geojson('crimes.geojson')"""
def get_intersecting_crimes(route_coords, crime_buffers_gdf):
    """
    Find crime buffers that intersect with a route
    
    Args:
        route_coords: List of coordinate tuples [(lat, lon), ...]
        crime_buffers_gdf: GeoDataFrame with crime buffer data
    
    Returns:
        List of crime records that intersect with the route
    """
    # Create a LineString from the route coordinates
    # Note: route_coords is (lat, lon) format but LineString expects (lon, lat)
    route_points = [(lon, lat) for lat, lon in route_coords]
    route_line = LineString(route_points)
    
    # Find intersecting crime buffers
    intersecting_buffers = crime_buffers_gdf[crime_buffers_gdf.intersects(route_line)]
    # Return the relevant crime information
    crime_list = []
    for _, crime in intersecting_buffers.iterrows():

        print(crime.head())
        if 'delito' in crime:
            crime_list.append(crime['delito'])
    
    return crime_list

def combine_node_edge_weights(graph, node_weight_attribute='node_weight', edge_weight_attribute='edge_weight',
                             output_attribute='combined_weight', alpha=0.5):
    """
    Combina los pesos de nodos y aristas para crear un peso combinado para cada arista
    
    Args:
        graph: Grafo de NetworkX
        node_weight_attribute: Atributo que contiene los pesos de los nodos
        edge_weight_attribute: Atributo que contiene los pesos de las aristas
        output_attribute: Nombre del atributo de salida para el peso combinado
        alpha: Factor que controla la importancia relativa (0-1)
               0 = solo pesos de aristas, 1 = solo pesos de nodos
    
    Returns:
        Grafo con el atributo de peso combinado añadido a cada arista
    """
    # Crear una copia del grafo para no modificar el original
    G = graph.copy()

    # Verificar que los atributos existen
    for node in G.nodes():
        if node_weight_attribute not in G.nodes[node]:
            G.nodes[node][node_weight_attribute] = 0.0

    # Combinar los pesos para cada arista
    for u, v, key, data in G.edges(data=True, keys=True):
        # Obtener peso de la arista
        edge_weight = data.get(edge_weight_attribute, 1.0)

        # Obtener peso de los nodos en ambos extremos de la arista
        u_weight = G.nodes[u].get(node_weight_attribute, 0.0)
        v_weight = G.nodes[v].get(node_weight_attribute, 0.0)

        # Promedio de los pesos de los nodos
        avg_node_weight = (u_weight + v_weight) / 2

        # Calcular peso combinado (ajustar la fórmula según necesites)
        # Factor exponencial para aumentar el impacto de los pesos de buffer
        node_impact = np.exp(avg_node_weight) - 1 if avg_node_weight > 0 else 0

        # Combinar usando alfa como factor de importancia
        combined = edge_weight * (1 + alpha * node_impact)

        # Almacenar el peso combinado
        G[u][v][key][output_attribute] = combined

    print(f"Pesos combinados calculados y guardados como '{output_attribute}'")
    return G

def custom_weight_strategy(edge_data, node_u_data, node_v_data, buffer_weight):
    """
    Calculate custom edge weight combining length and crime risk factors
    
    Args:
        edge_data: Edge attributes dictionary
        node_u_data: Source node attributes
        node_v_data: Target node attributes
        buffer_weight: Sum of crime buffer weights intersecting the edge
    
    Returns:
        float: Combined risk-aware weight
    """
    base_length = edge_data.get('length', 0)
    # Average buffer weights of the connected nodes
    node_weight = (node_u_data.get('buffer_weight', 0) + node_v_data.get('buffer_weight', 0)) / 2

    # Calculate combined weight - logarithmic scaling to avoid extreme values
    # Higher crime weights will increase the effective "cost" of the edge
    return base_length * (1 + math.log(1 + node_weight + buffer_weight))

def fast_edge_weight_calculation(graph, buffer_gdf, weight_col='weight'):
    """
    Calculate edge weights based on intersecting crime buffers using R-tree for spatial indexing
    
    Args:
        graph: NetworkX graph
        buffer_gdf: GeoDataFrame with crime buffers
        weight_col: Name of the weight column in buffer_gdf
    
    Returns:
        NetworkX graph with updated edge attributes
    """
    print(f"Processing {len(graph.edges())} edges against {len(buffer_gdf)} buffers...")

    # Create spatial index for buffers
    buffer_idx = index.Index()
    buffer_data = []

    # Populate the R-tree index
    for i, (_, row) in enumerate(buffer_gdf.iterrows()):
        buffer_idx.insert(i, row.geometry.bounds)
        buffer_data.append((row.geometry, row[weight_col]))

    # Process each edge
    edge_count = 0
    edges_with_buffers = 0

    for u, v, k, data in graph.edges(data=True, keys=True):
        edge_count += 1

        # Get or create edge geometry
        if 'geometry' in data:
            line = data['geometry']
        else:
            u_geom = Point(graph.nodes[u]['x'], graph.nodes[u]['y'])
            v_geom = Point(graph.nodes[v]['x'], graph.nodes[v]['y'])
            line = LineString([u_geom, v_geom])

        # Find potential buffer intersections using R-tree
        buffer_ids = list(buffer_idx.intersection(line.bounds))
        total_buffer_weight = 0
        buffer_count = 0

        # Check for precise intersections
        for buf_id in buffer_ids:
            geom, weight = buffer_data[buf_id]
            if line.intersects(geom):
                total_buffer_weight += weight
                buffer_count += 1

        if buffer_count > 0:
            edges_with_buffers += 1

        # Get node data
        node_u_data = graph.nodes[u]
        node_v_data = graph.nodes[v]

        # Calculate edge weight using custom strategy
        data['edge_weight'] = custom_weight_strategy(
            data, node_u_data, node_v_data, total_buffer_weight
        )

        # Store metrics for analysis
        data['buffer_count'] = buffer_count
        data['buffer_influence'] = total_buffer_weight

    print(f"Processed {edge_count} edges, {edges_with_buffers} have buffer intersections")
    return graph

def get_path(origin_node,destination_node,filtered_graph):

    shortest_route = nx.shortest_path(filtered_graph, origin_node, destination_node, weight='length')
    route_coords = [(filtered_graph.nodes[node]['y'], filtered_graph.nodes[node]['x']) for node in shortest_route]

    safest_route = nx.shortest_path(filtered_graph, origin_node, destination_node, weight='combined_weight')

    safest_route_coords = [(filtered_graph.nodes[node]['y'], filtered_graph.nodes[node]['x']) for node in safest_route]

    return safest_route_coords, route_coords 
    
    #folium.PolyLine(safest_route_coords, color='green', weight=4, opacity=0.7).add_to(crime_map)

def mid_point(origin, destination):
        # Calculate the L2 distance between origin and destination
    l2_distance = np.linalg.norm(np.array(origin) - np.array(destination))
    # Calculate the midpoint between origin and destination
    midpoint = ((origin[0] + destination[0]) / 2, (origin[1] + destination[1]) / 2)

    midpoint_point = Point(midpoint[1], midpoint[0]) 
    midpoint_geom = gpd.GeoSeries([midpoint_point])
    buffer_radius = l2_distance

    midpoint_buffer = midpoint_geom.buffer(buffer_radius)

    return midpoint_buffer

def crop_buffers(origin, destination, buffer_gdf):

    midpoint_buffer = mid_point(origin, destination, buffer_gdf)

    filtered_buffers = buffer_gdf[buffer_gdf.intersects(midpoint_buffer.unary_union)]

    return filtered_buffers

def crop_graph(origin, destination, graph):

    midpoint_buffer = mid_point(origin, destination)

    buffer_polygon = midpoint_buffer.geometry[0]

    subgraph = ox.truncate.truncate_graph_polygon(
        graph, 
        buffer_polygon, 
        truncate_by_edge=True)
    
    return subgraph

def buscar_ruta(origin, destination, time, graph, buffer):
    if time in buffer['time_zones'].unique():
        crimes_df = buffer[buffer['time_zones'] == time]
    else:
        crimes_df = buffer.copy()

    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    destination_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])

    region = crop_graph(origin, destination, graph)

    #route = ox.shortest_path(graph, origin_node, destination_node, weight='length')

    labeled_graph = fast_edge_weight_calculation(region, crimes_df)

    final_graph = combine_node_edge_weights(labeled_graph)

    return get_path(origin_node, destination_node, labeled_graph)
"""


filtered_buffers = crop_buffers(origin, destination, buffer_gdf)
filtered_graph = crop_graph(origin, destination, graph)
#clusters = pd.read_csv('CMX_2024.csv')

prova = pd.read_csv('CMX_noche.csv')

print(prova.head())"""
"""
import random
from math import cos, sin

crime_buffers = gpd.read_file('crime_buffers.geojson')

print(crime_buffers.head())

def random_point_within_radius(center, radius_km):
    radius_deg = radius_km / 111  # Rough conversion from km to degrees
    u = random.uniform(0, 1)
    v = random.uniform(0, 1)
    w = radius_deg * (u ** 0.5)
    t = 2 * 3.141592653589793 * v
    x = w * cos(t)
    y = w * sin(t)
    return [center[0] + x, center[1] + y]

punto2 = random_point_within_radius([19.294918, -99.175004], 2)

graph = ox.load_graphml('cache_MexicoCity_walk.graphml')
ruta = buscar_ruta([19.294918, -99.175004], punto2, "Madrugada", graph,crime_buffers)

print(ruta)"""