import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mapa Interactivo", page_icon="🌍", layout="wide")

# --- ESTILOS CSS PARA MEJORAR EL DISEÑO ---
st.markdown(
    """
    <style>
    body {
        background-color: #F5F5F5;
    }
    .title {
        color: #3366cc;
        text-align: center;
    }
    .stButton > button {
        background-color: #3366cc;
        color: white;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- TÍTULO ---
st.markdown("<h1 class='title'>🌍 Mapa Interactivo con Streamlit y Folium</h1>", unsafe_allow_html=True)

# --- SELECCIÓN DE TIEMPO ---
st.sidebar.header("📅 Selección de Hora y Chatbot")
selected_time = st.sidebar.selectbox("Selecciona la hora:", ["Madrugada", "Mañana", "Mediodía", "Tarde", "Noche", "Medianoche"])
st.sidebar.write(f"⌚ Hora seleccionada: **{selected_time}**")

# --- CHATBOT ---
st.sidebar.markdown("### 🤖 Chatbot")
user_input = st.sidebar.text_input("Escribe tu pregunta aquí:")
if user_input:
    st.sidebar.write("💬 Respuesta del chatbot: (próximamente)")

st.markdown("---")  # Línea divisoria

# --- SESIÓN PARA ALMACENAR MARCADORES ---
if "markers" not in st.session_state:
    st.session_state.markers = []

# ---- MAPA INTERACTIVO ----
st.markdown("### 📍 Mapa Interactivo")

# Crear un mapa centrado en Madrid
m = folium.Map(location=[40.4168, -3.7038], zoom_start=12)

# Agregar marcadores guardados en la sesión
for marker in st.session_state.markers:
    folium.Marker(
        location=marker,
        popup="📍 Marcador personalizado",
        tooltip="Haz clic para ver más"
    ).add_to(m)

# Mostrar el mapa interactivo y detectar clics
map_data = st_folium(m, width=700, height=500)

# --- DETECTAR CLIC Y AGREGAR MARCADORES ---
if map_data and map_data.get("last_clicked"):
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]

    # Agregar nueva coordenada y limitar a 5 marcadores
    if len(st.session_state.markers) >= 5:
        st.session_state.markers.pop(0)  # Elimina el más antiguo

    st.session_state.markers.append((lat, lon))
    st.experimental_rerun()  # Recargar la app para actualizar el mapa

st.success("🖱️ Haz clic en el mapa para agregar un marcador. Se guardarán hasta 5.")


