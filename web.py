import streamlit as st
import folium
from streamlit_folium import folium_static
import datetime
import random

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
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: row;
    }
    .chat-message.user {
        background-color: #e6f2ff;
        text-align: right;
        margin-left: 30%;
    }
    .chat-message.bot {
        background-color: #f2f2f2;
        margin-right: 30%;
    }
    .chat-bubble {
        padding: 8px;
        border-radius: 8px;
    }
    /* Nuevo estilo para el contenedor de chat con desplazamiento */
    .chat-container {
        height: 400px;
        overflow-y: auto;
        display: flex;
        flex-direction: column-reverse;
        padding-right: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- TÍTULO ---
st.markdown("<h1 class='title'>🌍 Mapa Interactivo con Streamlit y Folium</h1>", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "bot", "content": "Hola 👋 Soy tu asistente para el mapa. ¿En qué puedo ayudarte?"}
    ]

if 'markers' not in st.session_state:
    st.session_state.markers = []

if 'map_center' not in st.session_state:
    st.session_state.map_center = [40.4168, -3.7038]

if 'chat_submitted' not in st.session_state:
    st.session_state.chat_submitted = False

# --- FUNCIONES PARA EL CHATBOT ---
def process_message(user_input):
    # Palabras clave para respuestas predefinidas
    keywords = {
        'hola': "¡Hola! ¿En qué puedo ayudarte con el mapa?",
        'ayuda': "Puedes hacer clic en el mapa para añadir marcadores, cambiar la hora del día o preguntarme sobre ubicaciones.",
        'marcador': "Para añadir un marcador, utiliza el botón 'Capturar Marcadores'.",
        'limpiar': "Para limpiar los marcadores, puedes usar el botón 'Limpiar Marcadores' o el comando '/limpiar'.",
        'madrid': "Madrid está en las coordenadas [40.4168, -3.7038]. ¿Quieres que centre el mapa allí?",
        'barcelona': "Barcelona está en las coordenadas [41.3851, 2.1734]. ¿Quieres que centre el mapa allí?",
        'sevilla': "Sevilla está en las coordenadas [37.3891, -5.9845]. ¿Quieres que centre el mapa allí?",
        'valencia': "Valencia está en las coordenadas [39.4699, -0.3763]. ¿Quieres que centre el mapa allí?",
        'bilbao': "Bilbao está en las coordenadas [43.2630, -2.9350]. ¿Quieres que centre el mapa allí?"
    }
    
    # Comandos especiales
    if user_input.startswith('/'):
        command = user_input[1:].lower()
        if command == 'limpiar':
            st.session_state.markers = []
            return "He limpiado todos los marcadores del mapa."
        elif command.startswith('centro'):
            try:
                # Extraer coordenadas del comando
                parts = command.split(' ')
                if len(parts) > 1:
                    coords = parts[1].split(',')
                    lat, lon = float(coords[0]), float(coords[1])
                    st.session_state.map_center = [lat, lon]
                    return f"Centrando el mapa en las coordenadas [{lat}, {lon}]."
                else:
                    return "Formato incorrecto. Usa '/centro lat,lon'. Ejemplo: '/centro 40.4168,-3.7038'"
            except:
                return "Formato incorrecto. Usa '/centro lat,lon'. Ejemplo: '/centro 40.4168,-3.7038'"
        else:
            return "Comando no reconocido. Prueba con '/limpiar' o '/centro lat,lon'."
    
    # Revisar palabras clave
    for key, response in keywords.items():
        if key in user_input.lower():
            return response
    
    # Respuesta genérica si no hay coincidencias
    generic_responses = [
        "No estoy seguro de cómo ayudarte con eso en relación al mapa.",
        "¿Puedes ser más específico sobre lo que necesitas?",
        "Puedo ayudarte con el mapa. Prueba a preguntar por marcadores o ciudades.",
        "Si necesitas ayuda con el mapa, puedes preguntarme por comandos como '/limpiar'."
    ]
    return random.choice(generic_responses)

def on_submit_chat():
    user_input = st.session_state.chat_input
    if user_input:
        # Añadir mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Procesar la respuesta
        bot_response = process_message(user_input)
        
        # Añadir respuesta del bot al historial
        st.session_state.messages.append({"role": "bot", "content": bot_response})
        
        # Limpiar el campo de entrada
        st.session_state.chat_input = ""
        st.session_state.chat_submitted = True

def add_marker():
    # Simular la adición de un marcador cerca del centro del mapa
    new_marker = [
        st.session_state.map_center[0] + random.uniform(-0.01, 0.01),
        st.session_state.map_center[1] + random.uniform(-0.01, 0.01)
    ]
    st.session_state.markers.append(new_marker)
    st.session_state.last_marker = new_marker

def clear_markers():
    st.session_state.markers = []

def clear_chat():
    st.session_state.messages = [{"role": "bot", "content": "Conversación reiniciada. ¿En qué puedo ayudarte?"}]

# --- SELECCIÓN DE TIEMPO EN SIDEBAR ---
st.sidebar.header("📅 Selección de Hora y Chatbot")

selected_time = st.sidebar.selectbox("Selecciona la hora:", ["madrugada", "mañana", "mediodia", "tarde", "noche", "medianoche"])
st.sidebar.write(f"⌚ Hora seleccionada: **{selected_time}**")

# --- SECCIÓN DE CHATBOT EN SIDEBAR ---
st.sidebar.markdown("### 🤖 Chatbot Asistente")

# Mostrar historial de mensajes con contenedor desplazable
st.sidebar.markdown("#### Historial de Conversación")
chat_container = st.sidebar.container()

# Crear el contenedor con clase CSS personalizada para desplazamiento
chat_container.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Mostrar mensajes - nota que los mostramos en orden inverso para column-reverse
for message in reversed(st.session_state.messages):
    if message["role"] == "user":
        chat_container.markdown(f'<div class="chat-message user"><div class="chat-bubble">👤 {message["content"]}</div></div>', unsafe_allow_html=True)
    else:
        chat_container.markdown(f'<div class="chat-message bot"><div class="chat-bubble">🤖 {message["content"]}</div></div>', unsafe_allow_html=True)

# Cerrar el contenedor
chat_container.markdown('</div>', unsafe_allow_html=True)

# Entrada de usuario con callback en lugar de rerun
st.sidebar.text_input("Escribe tu pregunta aquí:", key="chat_input", on_change=on_submit_chat)

# Botón para limpiar la conversación
if st.sidebar.button("Limpiar Conversación"):
    clear_chat()

st.markdown("---")  # Línea divisoria

# ---- MAPA INTERACTIVO ----
st.markdown("### 📍 Mapa Interactivo")

# Determinar el estilo del mapa según la hora seleccionada
map_styles = {
    "madrugada": "CartoDB dark_matter",
    "mañana": "OpenStreetMap",
    "mediodia": "CartoDB Positron",
    "tarde": "Stamen Terrain",
    "noche": "CartoDB dark_matter",
    "medianoche": "Stamen Toner"
}
selected_style = map_styles.get(selected_time, "OpenStreetMap")

# Crear un mapa centrado en la ubicación específica
m = folium.Map(location=st.session_state.map_center, zoom_start=12, tiles=selected_style)

# Añadir marcadores existentes
for marker in st.session_state.markers:
    folium.Marker(
        location=marker,
        popup=f"📍 Lat: {marker[0]:.6f}, Lng: {marker[1]:.6f}",
        tooltip="Marcador añadido"
    ).add_to(m)

# Mostrar el último marcador con un icono diferente si existe
if 'last_marker' in st.session_state:
    folium.Marker(
        location=st.session_state.last_marker,
        popup=f"📍 Último marcador añadido: Lat: {st.session_state.last_marker[0]:.6f}, Lng: {st.session_state.last_marker[1]:.6f}",
        tooltip="Último marcador añadido",
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)

# Agregar interactividad para añadir marcadores
m.add_child(folium.ClickForMarker(popup="📍 Haz clic en el mapa para añadir un marcador"))

# Mostrar el mapa
folium_static(m)

# Área para mostrar información sobre marcadores o interacción
col1, col2 = st.columns(2)

with col1:
    if st.button("Capturar Marcadores", on_click=add_marker):
        pass  # La acción real ocurre en la función add_marker

with col2:
    if st.button("Limpiar Marcadores", on_click=clear_markers):
        pass  # La acción real ocurre en la función clear_markers

# Mostrar información sobre el último marcador si existe
if 'last_marker' in st.session_state:
    st.success(f"Último marcador añadido en: Lat: {st.session_state.last_marker[0]:.6f}, Lng: {st.session_state.last_marker[1]:.6f}")

# Mostrar información sobre la conversación
if st.session_state.chat_submitted:
    st.session_state.chat_submitted = False  # Resetear para el próximo ciclo

# --- NOTA FINAL ---
st.success("✅ ¡Mapa generado con éxito!")

# Mostrar la fecha y hora actual
current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
st.markdown(f"<p style='text-align:center; color:gray;'>Actualizado el: {current_time}</p>", unsafe_allow_html=True)



