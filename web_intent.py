import streamlit as st
import folium
import random
import geopandas as gpd
import osmnx as ox
from math import cos, sin, pi
from folium.plugins import Draw
from streamlit_folium import st_folium
from principal_functions import buscar_ruta

# Configuración inicial de la página
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
    [data-testid="stSidebar"] {background-color: #f5f5f530;}
    .main .block-container {padding-top: 1rem;}
    .stButton button {width: 100%;}
    .stChatFloatingInputContainer {bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# Estado de sesión inicial
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'map_config' not in st.session_state:
    st.session_state.map_config = {
        'points': [],
        'show_crime': False,
        'base_map': None
    }

# Función para crear mapa base
def create_base_map():
    m = folium.Map(location=[19.294918, -99.175004], zoom_start=12)
    Draw(draw_options={'marker': True, 'polyline': False}, export=False).add_to(m)
    return m

# Función para actualizar el mapa
def update_map(show_crime=False):
    m = create_base_map()
    
    # Añadir marcadores
    for i, point in enumerate(st.session_state.map_config['points']):
        folium.Marker(
            location=point,
            icon=folium.Icon(color='green' if i == 0 else 'red'),
            tooltip="Origen" if i == 0 else "Destino"
        ).add_to(m)
    
    # Añadir capa de crimen si está activa
    if show_crime:
        folium.GeoJson(
            data['crime'],
            name="Zonas de Riesgo",
            style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'fillOpacity': 0.3},
            tooltip=folium.GeoJsonTooltip(fields=['periodo_de', 'tipo_delic'])
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

# Interfaz de usuario principal
st.title("Chatbot Interactivo con Mapa")
col_chat, col_map = st.columns([0.4, 0.6])

# Columna del chatbot
with col_chat:
    st.header("Asistente Virtual")
    
    # Historial de chat
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # Entrada de usuario
    if prompt := st.chat_input("¿Cómo puedo ayudarte hoy?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Respuesta automática
        respuestas = [
            "¡Interesante! ¿Necesitas ayuda con ubicaciones en el mapa?",
            "Puedo ayudarte a analizar rutas seguras, ¿qué necesitas?",
            "Cuéntame más sobre lo que buscas y te ayudaré con el mapa."
        ]
        respuesta = random.choice(respuestas)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.chat_message("assistant").write(respuesta)

# Columna del mapa
with col_map:
    st.header("Mapa Inteligente")
    
    # Actualizar configuración inicial del mapa
    if not st.session_state.map_config['base_map']:
        st.session_state.map_config['base_map'] = update_map()
    
    # Mostrar el mapa
    map_data = st_folium(
        st.session_state.map_config['base_map'],
        width=700,
        height=500,
        key="main_map",
        returned_objects=["last_clicked"]
    )
    
    # Manejar clics en el mapa
    if map_data.get("last_clicked"):
        new_point = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
        if len(st.session_state.map_config['points']) < 2:
            st.session_state.map_config['points'].append(new_point)
            st.session_state.map_config['base_map'] = update_map(
                st.session_state.map_config['show_crime']
            )
    
    # Controles del mapa
    with st.container():
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            if st.button("🗑️ Reiniciar puntos"):
                st.session_state.map_config['points'] = []
                st.session_state.map_config['base_map'] = update_map()
        with col2:
            if st.button("🔄 Toggle capa crimen"):
                st.session_state.map_config['show_crime'] = not st.session_state.map_config['show_crime']
                st.session_state.map_config['base_map'] = update_map(
                    st.session_state.map_config['show_crime']
                )
    
    # Información de puntos seleccionados
    if st.session_state.map_config['points']:
        st.info("Puntos seleccionados:")
        for i, p in enumerate(st.session_state.map_config['points'], 1):
            st.write(f"Punto {i}: [{p[0]:.5f}, {p[1]:.5f}]")
    
    # Cálculo de rutas
    if len(st.session_state.map_config['points']) == 2:
        periodo = st.selectbox("Período del día:", ["Madrugada", "Mañana", "Tarde", "Noche"])
        if st.button("🚀 Calcular rutas", help="Calcula rutas seguras y rápidas"):
            with st.spinner("Analizando mejores rutas..."):
                try:
                    origen = st.session_state.map_config['points'][0]
                    destino = st.session_state.map_config['points'][1]
                    
                    ruta_segura, ruta_rapida = buscar_ruta(
                        origen, destino, periodo, data['graph'], data['crime']
                    )
                    
                    # Actualizar mapa con rutas
                    m = update_map(st.session_state.map_config['show_crime'])
                    folium.PolyLine(ruta_segura, color='green', weight=3).add_to(m)
                    folium.PolyLine(ruta_rapida, color='blue', weight=3).add_to(m)
                    st.session_state.map_config['base_map'] = m
                    
                    # Mostrar estadísticas
                    st.success("Rutas calculadas:")
                    cols = st.columns(2)
                    with cols[0]:
                        st.metric("Ruta Segura", f"{len(ruta_segura)*0.01:.2f} km")
                    with cols[1]:
                        st.metric("Ruta Rápida", f"{len(ruta_rapida)*0.01:.2f} km")
                        
                except Exception as e:
                    st.error(f"Error en cálculo: {str(e)}")

# Botón sorpresa en sidebar
with st.sidebar:
    if st.button("🎁 Sorprende-me"):
        random_point = [
            19.294918 + random.uniform(-0.05, 0.05),
            -99.175004 + random.uniform(-0.05, 0.05)
        ]
        st.session_state.map_config['points'] = [random_point]
        st.session_state.map_config['base_map'] = update_map()
        st.rerun()