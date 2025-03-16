import streamlit as st

# Set page config as the FIRST Streamlit command
st.set_page_config(page_title="Chatbot con Mapa", layout="wide")

# Now import other libraries
import folium
from streamlit_folium import folium_static
import random
from principal_functions import buscar_ruta
import geopandas as gpd
import osmnx as ox
from math import cos, sin, pi
from folium.plugins import Draw
from streamlit_folium import st_folium

# Function for generating random points
def random_point_within_radius(center, radius_km):
    radius_deg = radius_km / 111  # Rough conversion from km to degrees
    u = random.uniform(0, 1)
    v = random.uniform(0, 1)
    w = radius_deg * (u ** 0.5)
    t = 2 * pi * v
    x = w * cos(t)
    y = w * sin(t)
    return [center[0] + x, center[1] + y]

# Define functions for data loading
@st.cache_resource
def load_crime_data():
    return gpd.read_file('crime_buffers.geojson')

@st.cache_resource
def load_graph_data():
    return ox.load_graphml('cache_MexicoCity_walk.graphml')

# Load data after page config
crime_buffers = load_crime_data()
graph = load_graph_data()

# Custom CSS to make columns look better
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Page title
st.title("Chatbot Interactivo con Mapa")

# Create two columns: left for chatbot, right for map
col_chat, col_map = st.columns([0.4, 0.6])

# In the left column - Chatbot
with col_chat:
    st.header("Chatbot")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("¿En qué puedo ayudarte?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simple bot response logic
        bot_responses = [
            "¡Interesante! ¿Puedes contarme más?",
            "Puedo ayudarte a encontrar ubicaciones en el mapa. ¡Solo pregunta!",
            "Soy un chatbot simple. Mi amigo mapa a la derecha puede mostrarte lugares.",
            "¡Hola! Soy tu asistente virtual. ¿Cómo puedo ayudarte hoy?",
            "Puedes preguntarme sobre diferentes ubicaciones para ver en el mapa."
        ]
        
        response = random.choice(bot_responses)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)

# In the right column - Map
# En la columna del mapa (parte corregida)
with col_map:
    st.header("Mapa Interactivo")
    
    # Inicializar puntos seleccionados en el session_state
    if "selected_points" not in st.session_state:
        st.session_state.selected_points = []
    
    # Función para crear mapa base CON los marcadores actuales
    def create_base_map(with_draw=True):
        m = folium.Map(location=[19.294918, -99.175004], zoom_start=10)
        
        if with_draw:
            # Añadir el plugin de dibujo
            draw = Draw(
                draw_options={'marker': True, 'polyline': False, 'polygon': False, 'circle': False, 'rectangle': False},
                export=False
            )
            draw.add_to(m)
        
        # Añadir marcadores existentes
        for i, point in enumerate(st.session_state.selected_points):
            label = "Origen" if i == 0 else "Destino"
            folium.Marker(
                location=point,
                popup=label,
                tooltip=label,
                icon=folium.Icon(color='green' if i == 0 else 'red')
            ).add_to(m)
        
        return m

    # Inicializar/actualizar mapa en session_state
    if "map" not in st.session_state:
        st.session_state.map = create_base_map()
    
    # Mostrar puntos seleccionados
    st.write("Puntos seleccionados:")
    if not st.session_state.selected_points:
        st.write("Ninguno - Selecciona hasta 2 puntos en el mapa")
    else:
        for i, point in enumerate(st.session_state.selected_points, 1):
            st.write(f"Punto {i}: Lat: {point[0]:.6f}, Lon: {point[1]:.6f}")
    
    # Renderizar el mapa y capturar eventos
    map_data = st_folium(
        st.session_state.map,
        width=700,
        height=500,
        key="interactive_map",
        center=[19.41, -99.133209],  # Coordenadas del centro de la Ciudad de México
        zoom=12  # Nivel de zoom más cercano
        # returned_objects=["last_clicked", "all_drawings"]
    )
    
    # Procesar clics del mapa
    if map_data and map_data.get("last_clicked"):
        new_point = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
        
        if len(st.session_state.selected_points) < 2:
            st.session_state.selected_points.append(new_point)
            # Actualizar mapa manteniendo los marcadores
            st.session_state.map = create_base_map()
            st.experimental_rerun()
    
    # Botones de control
    col_reset, col_calc = st.columns(2)
    with col_reset:
        if st.button("Reiniciar Puntos"):
            st.session_state.selected_points = []
            st.session_state.map = create_base_map()
            st.rerun()
    
    with col_calc:
    # Crear UN solo botón y manejar su estado
        calc_button = st.button(
            "Calcular Ruta", 
            disabled=len(st.session_state.selected_points) != 2
        )

    # Periodo del día para la ruta
    periodo = st.selectbox(
        "Período del día para calcular la ruta:",
        ["Madrugada", "Mañana", "Tarde", "Noche"]
    )

    # Calcular ruta cuando se presiona el botón
    if calc_button and len(st.session_state.selected_points) == 2:
        # Crear nuevo mapa base con los marcadores existentes
        new_map = create_base_map()
        
        # Añadir marcadores para origen y destino
        folium.Marker(
            location=st.session_state.selected_points[0],
            popup="Origen",
            tooltip="Origen",
            icon=folium.Icon(color='green')
        ).add_to(new_map)
        
        folium.Marker(
            location=st.session_state.selected_points[1],
            popup="Destino",
            tooltip="Destino",
            icon=folium.Icon(color='red')
        ).add_to(new_map)
        
        # Calcular ruta
        ruta = None
        with st.spinner("Calculando ruta..."):
            try:
                ruta = buscar_ruta(
                    st.session_state.selected_points[0],
                    st.session_state.selected_points[1],
                    periodo,
                    graph,
                    crime_buffers
                )
                
                if ruta:
                    ruta_segura, ruta_rapida = ruta
                    
                    # Añadir rutas al mapa
                    folium.PolyLine(ruta_segura, color="green", weight=4, opacity=1, 
                                tooltip="Ruta más segura").add_to(new_map)
                    folium.PolyLine(ruta_rapida, color="blue", weight=4, opacity=1,
                                tooltip="Ruta más rápida").add_to(new_map)

                    # Añadir leyenda
                    legend_html = '''
                    <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 150px; height: 90px; 
                        background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                        padding: 10px; border-radius: 5px;">
                        &nbsp; <b>Leyenda</b> <br>
                        &nbsp; <i class="fa fa-circle" style="color:green"></i>&nbsp; Ruta más segura <br>
                        &nbsp; <i class="fa fa-circle" style="color:blue"></i>&nbsp; Ruta más rápida <br>
                    </div>
                    '''
                    new_map.get_root().html.add_child(folium.Element(legend_html))

                    # Calcular los límites de la ruta
                    todas_coordenadas = []
                    todas_coordenadas.extend(ruta_segura)
                    todas_coordenadas.extend(ruta_rapida)
                
                    lats = [coord[0] for coord in todas_coordenadas]
                    lons = [coord[1] for coord in todas_coordenadas]
                
                    # Añadir margen de 0.005 grados (aproximadamente 500 metros)
                    bounds = [
                        [min(lats) - 0.005, min(lons) - 0.005],
                        [max(lats) + 0.005, max(lons) + 0.005]
                    ]
                
                    # Ajustar la vista del mapa a los límites calculados
                    new_map.fit_bounds(bounds)

                    # Actualizar el mapa en session_state
                    st.session_state.map = new_map
                    
                    # Mostrar estadísticas de la ruta
                    st.subheader("Estadísticas de Ruta")
                    col_safe, col_fast = st.columns(2)
                    
                    with col_safe:
                        st.write("**Ruta Más Segura**")
                        st.write(f"Distancia: {len(ruta_segura) * 0.01:.2f} km")
                        st.write(f"Tiempo estimado: {len(ruta_segura) * 0.2:.1f} min")
                        
                    with col_fast:
                        st.write("**Ruta Más Rápida**")
                        st.write(f"Distancia: {len(ruta_rapida) * 0.01:.2f} km")
                        st.write(f"Tiempo estimado: {len(ruta_rapida) * 0.2:.1f} min")
                    
            except Exception as e:
                st.error(f"Error al calcular la ruta: {e}")
        
    # Información contextual
    st.info("Selecciona dos puntos en el mapa y haz clic en 'Calcular Ruta' para ver rutas seguras y rápidas entre ellos.")

# Botón sorpresa ahora aparecerá debajo del mapa
if st.button("Haz clic aquí para una sorpresa"):
    # Crear nuevo mapa base
    new_map = create_base_map()
    
    # Generar punto destino
    punto2 = random_point_within_radius([19.294918, -99.175004], 2)
    
    # Calcular ruta
    ruta = None
    with st.spinner("Calculando ruta..."):
        try:
            ruta = buscar_ruta(
                [19.294918, -99.175004],
                punto2,
                "Madrugada",
                graph,
                crime_buffers
            )
        except Exception as e:
            st.error(f"Error al calcular la ruta: {e}")
    
    if ruta:
        ruta_segura, ruta_rapida = ruta
        
        # Añadir elementos al nuevo mapa
        folium.PolyLine(ruta_segura, color="green", weight=2.5, opacity=1).add_to(new_map)
        folium.PolyLine(ruta_rapida, color="blue", weight=2.5, opacity=1).add_to(new_map)
        folium.Marker(punto2, popup="Destino", tooltip="Punto Destino").add_to(new_map)

        # Calcular los límites de la ruta
        todas_coordenadas = []
        todas_coordenadas.extend(ruta_segura)
        todas_coordenadas.extend(ruta_rapida)
        
        lats = [coord[0] for coord in todas_coordenadas]
        lons = [coord[1] for coord in todas_coordenadas]
        
        # Añadir margen de 0.005 grados (aproximadamente 500 metros)
        bounds = [
            [min(lats) - 0.005, min(lons) - 0.005],
            [max(lats) + 0.005, max(lons) + 0.005]
        ]
        
        # Ajustar la vista del mapa a los límites calculados
        new_map.fit_bounds(bounds)

        # Actualizar el mapa en session_state
        st.session_state.map = new_map
    
    # Actualizar el placeholder con el nuevo mapa
    with map_placeholder:
        folium_static(st.session_state.map, width=700)

    # Información contextual
    st.info("Este mapa muestra una ubicación predeterminada. ¡El chatbot podría programarse para mostrar diferentes ubicaciones según tu conversación!")
