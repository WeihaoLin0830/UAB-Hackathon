import streamlit as st
import folium
import random
import geopandas as gpd
import osmnx as ox
from math import cos, sin, pi
from folium.plugins import Draw
from streamlit_folium import st_folium
from principal_functions import buscar_ruta, get_intersecting_crimes
from safe import SafeRouteChatbot

# Configuración inicial de la página
chat = SafeRouteChatbot()
st.set_page_config(page_title="Chatbot con Mapa", layout="wide")

# Función para carga de datos
@st.cache_resource
def load_data():
    return {
        'crime': gpd.read_file('crime_buffers.geojson'),
        'graph': ox.load_graphml('cache_MexicoCity_walk.graphml')
    }

# Cargar datos una sola vez
data = load_data()

# Estilos CSS personalizados
st.markdown("""
<style>
    /* Chat container */
    .stChatMessage {
        padding: 10px 0;
    }
    
    /* Make the chat input stick to the bottom */
    section[data-testid="stChatMessageInputContainer"] {
        position: relative !important;
        bottom: 0 !important;
        left: 0 !important;
        padding: 1rem !important;
        z-index: 1000 !important;
        background-color: white !important;
        border-top: 1px solid #e0e0e0 !important;
        width: 38% !important; /* Match the column width */
    }
    
    /* Ensure chat messages are visible above the fixed input */
    [data-testid="stChatMessageContainer"] {
        margin-bottom: 70px !important; /* Space for the fixed input */
        position: relative !important;
        bottom: 0 !important;
    }
    
    /* Style the chat input field */
    .stChatInput input, div[data-testid="stChatInput"] input {
        position: relative !important;
        bottom: 0 !important;
        border: 1px solid #ddd !important;
        border-radius: 20px !important;
        padding: 8px 15px !important;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.05) !important;
    }
    
    /* Map container */
    .map-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }

    /* Fix chat container to prevent unnecessary divs */
    .element-container:has(.stChatMessageContainer) {
        height: auto !important;
        overflow: visible !important;
    }
</style>
""", unsafe_allow_html=True)

# Estado de sesión inicial
if 'messages' not in st.session_state:
    st.session_state.messages = []
    
if 'map_state' not in st.session_state:
    # Coordenadas del centro de la Ciudad de México
    default_center = [19.424918, -99.175004]
    st.session_state.map_state = {
        'points': [],
        'show_crime': False,
        'center': default_center,
        'zoom': 12,
        'routes': None
    }

# Función para crear mapa base
def create_base_map(center, zoom):
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
    Draw(draw_options={'marker': True, 'polyline': False}, export=False).add_to(m)
    return m

# Función para calcular bounds para ajustar el zoom a las rutas
def get_route_bounds(routes):
    if not routes:
        return None
    
    # Extraer todas las coordenadas de ambas rutas
    all_points = []
    for route in routes:
        all_points.extend(route)
    
    # Calcular los límites
    min_lat = min(point[0] for point in all_points)
    max_lat = max(point[0] for point in all_points)
    min_lng = min(point[1] for point in all_points)
    max_lng = max(point[1] for point in all_points)
    
    # Agregar un pequeño margen
    margin = 0.005  # aproximadamente 500m
    return [[min_lat - margin, min_lng - margin], [max_lat + margin, max_lng + margin]]

# Función para actualizar el mapa
def update_map():
    # Usar los mismos coordenadas predeterminadas consistentemente
    default_center = [19.424918, -99.175004]
    center = st.session_state.map_state.get('center', default_center)
    zoom = st.session_state.map_state.get('zoom', 12)
    
    # Crear mapa base
    m = create_base_map(center, zoom)
    
    # Añadir marcadores
    for i, point in enumerate(st.session_state.map_state['points']):
        folium.Marker(
            location=point,
            icon=folium.Icon(color='green' if i == 0 else 'red'),
            tooltip="Origen" if i == 0 else "Destino"
        ).add_to(m)
    
    # Añadir rutas existentes
    if st.session_state.map_state['routes']:
        ruta_segura, ruta_rapida = st.session_state.map_state['routes']
        folium.PolyLine(ruta_segura, color='green', weight=3).add_to(m)
        folium.PolyLine(ruta_rapida, color='red', weight=3).add_to(m)
        
        # Ajustar el zoom para mostrar toda la ruta
        bounds = get_route_bounds(st.session_state.map_state['routes'])
        if bounds:
            m.fit_bounds(bounds)
    
    # Añadir capa de crimen si está activa
    if st.session_state.map_state['show_crime']:
        folium.GeoJson(
            data['crime'],
            name="Zonas de Riesgo",
            style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'fillOpacity': 0.3},
            tooltip=folium.GeoJsonTooltip(fields=['periodo_de', 'tipo_delic'])
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

# Interfaz principal
col1, col2 = st.columns([0.4, 0.6])

# Columna del Chatbot (izquierda)
with col1:
    st.header("Asistente Virtual")
    
    # Contenedor único para el chat (evita divs innecesarios)
    chat_container = st.container(height=600)
    
    # Historial de mensajes
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Entrada de usuario (fija abajo)
        if prompt := st.chat_input("Escribe tu mensaje..."):
            # Añadir mensaje de usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Simular respuesta del bot

            respuesta = chat.free(prompt)
            
            # Añadir respuesta del bot
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
            
            # Forzar actualización del chat
            st.rerun()

# Columna del Mapa (derecha)
with col2:
    st.header("Mapa Inteligente")
    
    # Renderizar mapa
    with st.container(height=600):
        map_data = st_folium(
            update_map(),
            width=850,
            height=550,
            key="main_map",
            returned_objects=["last_clicked", "bounds", "zoom"]
        )
        
        # Actualizar estado del mapa
        if map_data:
            # Verificar si existen los bounds y tienen los campos necesarios
            if map_data.get('bounds') and all(key in map_data['bounds'] for key in ['north', 'south', 'east', 'west']):
                st.session_state.map_state['center'] = [
                    (map_data['bounds']['north'] + map_data['bounds']['south']) / 2,
                    (map_data['bounds']['east'] + map_data['bounds']['west']) / 2
                ]
            # No cambiar center si bounds no está disponible
            
            if map_data.get('zoom'):
                st.session_state.map_state['zoom'] = map_data['zoom']

    # Manejar clics en el mapa
    if map_data and map_data.get("last_clicked"):
        new_point = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
        if len(st.session_state.map_state['points']) < 2:
            st.session_state.map_state['points'].append(new_point)
            st.session_state.map_state['routes'] = None
            st.rerun()

    # Controles del mapa
    with st.container():
        cols = st.columns([1,1,2])
        with cols[0]:
            if st.button("🗑️ Reiniciar puntos", use_container_width=True):
                st.session_state.map_state['points'] = []
                st.session_state.map_state['routes'] = None
                st.rerun()
                
        with cols[1]:
            crime_toggle = st.session_state.map_state['show_crime']
            btn_label = "🔴 Ocultar crimen" if crime_toggle else "🔵 Mostrar crimen"
            if st.button(btn_label, use_container_width=True):
                st.session_state.map_state['show_crime'] = not crime_toggle
                st.rerun()

    # Calculo de rutas
    if len(st.session_state.map_state['points']) == 2:
        periodo = st.selectbox("Seleccionar período:", ["Mediodia", "Mañana", "Tarde", "Noche","Medianoche","Madrugada","Todo"])
        
        if st.button("🚀 Calcular rutas", use_container_width=True):
            with st.spinner("Calculando mejores rutas..."):
                try:
                    origen = st.session_state.map_state['points'][0]
                    destino = st.session_state.map_state['points'][1]
                    
                    rutas = buscar_ruta(
                        origen, destino, periodo, 
                        data['graph'], data['crime']
                    )

                    msg_lst = get_intersecting_crimes(rutas[1], data['crime'])
                    print(msg_lst)
                    answer = chat.generate_response(origen, destino, msg_lst)

                    st.session_state.messages.append(answer)
                    
                    st.session_state.map_state['routes'] = rutas
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Mostrar estadísticas
    if st.session_state.map_state['routes']:
        st.success("Rutas calculadas:")
        ruta_segura, ruta_rapida = st.session_state.map_state['routes']
        cols = st.columns(2)
        with cols[0]:
            st.metric("Ruta Segura", f"{len(ruta_segura)*0.01:.2f} km", "±25% menos riesgo")
        with cols[1]:
            st.metric("Ruta Rápida", f"{len(ruta_rapida)*0.01:.2f} km", "±35% más rápida")