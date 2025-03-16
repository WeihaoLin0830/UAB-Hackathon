import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox
from shapely.geometry import Polygon

def load_crimes_geojson(file_path):
    return gpd.read_file(file_path)

crimes_gdf = load_crimes_geojson('crimes.geojson')

def mid_point(origin, destination):
        # Calculate the L2 distance between origin and destination
    l2_distance = np.linalg.norm(np.array(origin) - np.array(destination))
    # Calculate the midpoint between origin and destination
    midpoint = ((origin[0] + destination[0]) / 2, (origin[1] + destination[1]) / 2)

    midpoint_point = Point(midpoint[1], midpoint[0]) 
    midpoint_geom = gpd.GeoSeries([midpoint_point], crs=buffer_gdf.crs)
    buffer_radius = l2_distance

    midpoint_buffer = midpoint_geom.buffer(buffer_radius)

    return midpoint_buffer

def crop_buffers(origin, destination, buffer_gdf):

    midpoint_buffer = mid_point(origin, destination)

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

def buscar_ruta(origin, destination, time, graph):
    if time in crimes_gdf['time'].unique():
        crimes_df = crimes_gdf[crimes_gdf['time'] == time]
    else:
        crimes_df = crimes_gdf.copy()

    origin_node = ox.get_nearest_node(graph, origin)
    destination_node = ox.get_nearest_node(graph, destination)

    region = crop_graph(origin, destination, graph)

    route = ox.shortest_path(graph, origin_node, destination_node, weight='length')

    return route



filtered_buffers = crop_buffers(origin, destination, buffer_gdf)
filtered_graph = crop_graph(origin, destination, graph)
#clusters = pd.read_csv('CMX_2024.csv')

prova = pd.read_csv('CMX_noche.csv')

print(prova.head())


def 