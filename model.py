import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import os
import time
from datetime import datetime
import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, FeatureGroupSubGroup, MiniMap, MeasureControl

# Load the Mexico City walking graph
graph_file = "cache_MexicoCity_walk.graphml"
G = ox.load_graphml(graph_file)

print("Cargando datos de crímenes...")
try:
    # Cargar datos de crímenes
    crimes = gpd.read_file("crimenes.geojson")

    # Verificar que tenemos geometrías válidas
    if crimes.empty:
        raise ValueError("El archivo de crímenes está vacío")
    print(f"Cargados {len(crimes)} registros de crímenes")
except Exception as e:
    print(f"Error al cargar datos: {e}")
    # Crear datos de ejemplo si falla la carga
    print("Generando datos de ejemplo para demostración...")
    # Coordenadas de CDMX centro
    lat, lon = 19.432608, -99.133209
    # Crear algunos puntos ficticios alrededor
    data = {
        'type': ['Robo', 'Asalto', 'Robo', 'Fraude', 'Asalto'],
        'geometry': [
            gpd.points_from_xy([lon], [lat])[0],
            gpd.points_from_xy([lon-0.01], [lat+0.01])[0],
            gpd.points_from_xy([lon+0.01], [lat-0.01])[0],
            gpd.points_from_xy([lon-0.02], [lat-0.01])[0],
            gpd.points_from_xy([lon+0.015], [lat+0.02])[0]
        ]
    }
    crimes = gpd.GeoDataFrame(data, crs="EPSG:4326")

# Create buffers around crime points
# First, check the current CRS
if crimes.crs is None:
    print("Warning: CRS is not defined for the crimes dataset.")
    print("Setting CRS to EPSG:4326 (WGS84) as a default.")
    crimes.set_crs(epsg=4326, inplace=True)

# Reproject to UTM for accurate distance measurements
# Mexico City is in UTM zone 14N (EPSG:32614)
crimes_projected = crimes.to_crs(epsg=32614)

# Create 100 meter buffers
buffer_distance = 100  # meters
crime_buffers = crimes_projected.copy()
crime_buffers['geometry'] = crimes_projected.buffer(buffer_distance)

# Reproject back to the original CRS
crime_buffers = crime_buffers.to_crs(crimes.crs)

print(f"Created {len(crime_buffers)} buffers of {buffer_distance} meters each.")

# Save the street network and crime buffers as an interactive HTML map

# Get the graph bounds to set the map center
graph_bounds = ox.graph_to_gdfs(G, nodes=False).total_bounds
center_lat = (graph_bounds[1] + graph_bounds[3]) / 2
center_lon = (graph_bounds[0] + graph_bounds[2]) / 2

# Create a Folium map
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='CartoDB positron')

# Create feature groups for layers
streets_group = folium.FeatureGroup(name="Streets", show=False)  # Default hidden
heatmap_group = folium.FeatureGroup(name="Crime Heatmap", show=True)
buffers_group = folium.FeatureGroup(name="Crime Buffers", show=False)  # Default hidden

# 1. SIMPLIFICACIÓN DE GEOMETRÍAS
# Extract edges and simplify geometries
edges = ox.graph_to_gdfs(G, nodes=False)
# Simplify the street network geometries to reduce points (tolerance in degrees)
print("Simplifying street geometries...")
edges['geometry'] = edges['geometry'].simplify(tolerance=0.0001)

# Add simplified streets to the map
folium.GeoJson(
    data=edges[['geometry']],
    style_function=lambda x: {
        'color': 'gray',
        'weight': 1,
        'opacity': 0.5
    },
).add_to(streets_group)

# 2. USAR HEATMAP PARA REPRESENTAR CONCENTRACIONES DE CRÍMENES
print("Creating heatmap from crime data...")
# Extract crime locations for heatmap
heat_data = [[point.y, point.x] for point in crimes.geometry]
# Add the heatmap to the heatmap group
HeatMap(heat_data,
        radius=15,
        blur=10,
        max_zoom=13,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}).add_to(heatmap_group)

# 3. OPTIMIZAR LOS BUFFERS (solo se mostrarán bajo demanda)
# Sample buffers if there are too many
max_buffers = 1000  # Limit number of buffers to improve performance
if len(crime_buffers) > max_buffers:
    print(f"Sampling {max_buffers} from {len(crime_buffers)} buffers for better performance...")
    crime_buffers = crime_buffers.sample(max_buffers)

# Simplify buffer geometries
print("Simplifying buffer geometries...")
crime_buffers['geometry'] = crime_buffers['geometry'].simplify(tolerance=0.0001)

# First convert any datetime columns to strings
for col in crime_buffers.select_dtypes(include=['datetime64']).columns:
    crime_buffers[col] = crime_buffers[col].astype(str)

# Add buffers to map (deferred loading)
if 'type' in crime_buffers.columns:
    # Create a color map for crime types
    unique_types = crime_buffers['type'].unique()
    color_dict = {t: f"#{hash(t) % 0xffffff:06x}" for t in unique_types}

    folium.GeoJson(
        data=crime_buffers.__geo_interface__,
        style_function=lambda feature: {
            'fillColor': color_dict.get(feature['properties'].get('type', ''), 'red'),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=folium.GeoJsonTooltip(fields=['type'], aliases=['Crime Type:']),
    ).add_to(buffers_group)
else:
    folium.GeoJson(
        data=crime_buffers.__geo_interface__,
        style_function=lambda x: {
            'fillColor': 'red',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5
        },
    ).add_to(buffers_group)

# 4. AÑADIR GRUPOS POR DEMANDA
streets_group.add_to(m)
heatmap_group.add_to(m)
buffers_group.add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Add info box
info_html = f"""
<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
            background-color: white; padding: 10px; border: 1px solid grey;
            border-radius: 5px; max-width: 300px;">
    <h4>Mapa de Crímenes CDMX</h4>
    <p>Buffer: {buffer_distance}m alrededor de cada crimen</p>
    <p>Total crímenes: {len(crimes)}</p>
    <p>Usa los controles de capa para mostrar/ocultar información</p>
</div>
"""
m.get_root().html.add_child(folium.Element(info_html))

# Save the map as an HTML file
output_file = f"mexico_city_crime_map_{buffer_distance}m.html"
m.save(output_file)

print(f"Map saved as '{output_file}'")

# Centro del mapa (promedio de coordenadas)
center_lat = crimes.geometry.y.mean()
center_lon = crimes.geometry.x.mean()

# Crear un mapa base con diferentes opciones de tiles
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
    tiles='CartoDB Positron'  # Puedes probar: 'OpenStreetMap', 'Stamen Terrain', 'CartoDB dark_matter'
)

# Añadir selector de mapas base
folium.TileLayer('OpenStreetMap').add_to(m)
folium.TileLayer('CartoDB dark_matter').add_to(m)
folium.TileLayer('Stamen Terrain').add_to(m)
folium.TileLayer('Stamen Toner').add_to(m)

# Crear grupos para organizar la información
markers_group = folium.FeatureGroup(name='Crímenes Individuales', show=False)
heatmap_group = folium.FeatureGroup(name='Mapa de Calor', show=True)

# 1. Añadir clúster de marcadores para crímenes individuales
marker_cluster = MarkerCluster().add_to(markers_group)

# Colores según tipo de crimen
crime_colors = {
    'Robo': 'red',
    'Asalto': 'darkred',
    'Fraude': 'orange',
    'Homicidio': 'black',
    'Secuestro': 'purple',
    'Violencia': 'darkpurple',
    'Vandalismo': 'blue',
}

# Añadir marcadores para cada crimen
for idx, crime in crimes.iterrows():
    # Obtener coordenadas
    lat, lon = crime.geometry.y, crime.geometry.x

    # Determinar color según tipo
    crime_type = crime.get('type', 'Desconocido')
    color = crime_colors.get(crime_type, 'gray')

    # Crear popup con información
    popup_text = f"Crimen: {crime_type}"
    if 'fecha' in crime:
        popup_text += f"<br>Fecha: {crime['fecha']}"

    # Añadir marcador al clúster
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(marker_cluster)

# 2. Añadir mapa de calor para visualizar densidad de crímenes
print("Creando mapa de calor...")
heat_data = [[point.y, point.x] for point in crimes.geometry]
HeatMap(
    heat_data,
    radius=15,
    blur=10,
    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
).add_to(heatmap_group)

# Añadir los grupos al mapa
markers_group.add_to(m)
heatmap_group.add_to(m)

# Añadir control de capas
folium.LayerControl().add_to(m)

# Añadir mini mapa para orientación
minimap = MiniMap()
m.add_child(minimap)

# Añadir barra de escala
MeasureControl(position='bottomleft').add_to(m)

# Añadir información
info_html = f"""
<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
            background-color: white; padding: 10px; border: 1px solid grey;
            border-radius: 5px; max-width: 300px;">
    <h4>Mapa de Crímenes CDMX</h4>
    <p>Total crímenes: {len(crimes)}</p>
    <p>Usa los controles de capa para mostrar diferentes visualizaciones</p>
    <p>• El mapa de calor muestra concentraciones</p>
    <p>• Los marcadores muestran ubicaciones exactas</p>
</div>
"""
m.get_root().html.add_child(folium.Element(info_html))

# Guardar mapa
output_file = "mapa_crimenes_cdmx_simple.html"
m.save(output_file)
print(f"Mapa guardado como '{output_file}'")

# Añadir mensaje para abrir el mapa
print(f"Abre el archivo {output_file} en tu navegador para ver el mapa interactivo")
try:
    import webbrowser
    # Obtener la ruta completa al archivo
    full_path = os.path.abspath(output_file)
    # Abrir en el navegador predeterminado
    webbrowser.open('file://' + full_path, new=2)
    print("¡Mapa abierto en el navegador!")
except:
    pass