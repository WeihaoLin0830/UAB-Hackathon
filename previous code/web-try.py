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
with col_map:
    st.header("Mapa Interactivo")

    # Create a map centered at a default location
    m = folium.Map(location=[19.294918, -99.175004], zoom_start=10)
    
    # Add a marker for demonstration - FIX: correct order for coordinates (lat, lon)
    folium.Marker(
        location=[19.294918, -99.175004],  # Correct order: [latitude, longitude]
        popup="CMX", 
        tooltip="CMX"
    ).add_to(m)
    
    # Display the map
    folium_static(m, width=700)
    
    # Add some context
    st.info("Este mapa muestra una ubicación predeterminada. ¡El chatbot podría programarse para mostrar diferentes ubicaciones según tu conversación!")

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

# Route planning section
if st.button("Haz clic aquí para una sorpresa"):
    st.write("¡Sorpresa! Has hecho clic en el botón.")

    punto = [19.294918, -99.175004]
    
    # Add the point to the map (correct coordinate order)
    folium.Marker(
        location=punto,
        popup="Punto Inicial",
        tooltip="Punto Inicial"
    ).add_to(m)

    # Generate a random point within 2 km radius
    punto2 = random_point_within_radius([19.294918, -99.175004], 2)

    # Calculate route
    with st.spinner("Calculando ruta..."):
        try:
            ruta = buscar_ruta([19.294918, -99.175004], punto2, "Madrugada", graph, crime_buffers)
            
            # Add the route to the map
            folium.PolyLine(ruta, color="red", weight=2.5, opacity=1).add_to(m)
            
            # Add destination marker
            folium.Marker(
                location=punto2,
                popup="Destino",
                tooltip="Punto Destino"
            ).add_to(m)
            
            # Display the map with route
            folium_static(m, width=700)
        except Exception as e:
            st.error(f"Error al calcular la ruta: {e}")