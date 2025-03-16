import pandas as pd
import geopandas as gpd
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from shapely.geometry import Point, LineString
import re
from datetime import datetime
from geopy.geocoders import Nominatim
import os
import json
from google import genai
from dotenv import load_dotenv
from principal_functions import *
load_dotenv()

API_KEY = os.getenv("API_KEY")

print(API_KEY)

client = genai.Client(api_key = API_KEY)
geolocator = Nominatim(user_agent="geoapiExercises")

# Buscar una ubicació


#  Adaptar las llamadas a diferentes funciones dependiendo de la hora del día.

class SafeRouteChatbot:

    def free(self, user_message):
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[user_message]
        )        
        return response
        
    
    def generate_response(self, user_message):
    # Process user input
        params = self.process_user_input(user_message)
        # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ==> lista de delitos, frecuencia, hora_más_alta
        '''orig = geolocator.geocode(params['origin'])
        dest = geolocator.geocode(params['destination'])
        
        if not orig or not dest:
            return "No se pudo encontrar la ubicación de origen o destino. Por favor, verifica las direcciones proporcionadas."
        
        orig_point = Point(orig.longitude, orig.latitude)
        dest_point = Point(dest.longitude, dest.latitude)
        
        # Load crime buffer data
        crime_data = gpd.read_file('crime_buffer.geojson')
        
        # Filter zones (buffers) that are between origin and destination
        line = LineString([orig_point, dest_point])
        filtered_zones = crime_data[crime_data.geometry.intersects(line)]
        
        if filtered_zones.empty:
            return "No se encontraron zonas de crimen entre el origen y el destino."
        
        # Extract relevant information from filtered zones
        # Calculate 'crime_type' and 'highest_hour'
        filtered_zones['crime_type'] = filtered_zones['crime_data'].apply(lambda x: max(x, key=x.get))
        filtered_zones['highest_hour'] = filtered_zones['crime_data'].apply(lambda x: max(x.values()))
        
        crime_info = filtered_zones[['crime_type', 'highest_hour']].to_dict(orient='records')
        
        # Add crime info to route data
        route_data = {
            "shortest": "ruta más corta",
            "safest": "ruta más segura",
            "crime_info": crime_info
        }
        '''
        # Check if we have enough information
        if not params['origin'] or not params['destination']:
            return "Necesito saber tu origen y destino para recomendarte una ruta segura. Por favor, indícame desde dónde y hasta dónde quieres ir."
        
        # Get routes from external function
        
        
        # Generate explanation for both routes
        safest_route_explanation = self.get_route_explanation(params)
        
        # Combine explanations
           
        return safest_route_explanation
        
        # Load routing data if available
        
    # NECESITO =====> HOTINFO (delito, frecuencia, hora_más_alta), RouteData (rutas, seguridad, horarios)
    
    def process_user_input(self, user_message):
        """
        Process user input to extract route information
        
        Args:
            user_message: String containing user request
            
        Returns:
            dict: Extracted parameters including origin, destination, time
        """
        # Extract locations using regex patterns
        origin_match = re.search(r'desde\s+([^,]+)', user_message, re.IGNORECASE) or \
                      re.search(r'en\s+([^,]+)', user_message, re.IGNORECASE)
        
        dest_match = re.search(r'hasta\s+([^,]+)', user_message, re.IGNORECASE) or \
                    re.search(r'a\s+([^,]+)', user_message, re.IGNORECASE) or \
                    re.search(r'ir\s+a\s+([^,]+)', user_message, re.IGNORECASE)
        
        # Extract time information
        time_match = re.search(r'a las\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', user_message, re.IGNORECASE) or \
                    re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|horas?)', user_message, re.IGNORECASE)
        
        # Process origin
        origin = origin_match.group(1).strip() if origin_match else None
        
        # Process destination  
        destination = dest_match.group(1).strip() if dest_match else None
        
        # Process time
        hour = None
        if time_match:
            hour = int(time_match.group(1))
            # Convert to 24-hour format if needed
            if time_match.group(3) and time_match.group(3).lower() == 'pm' and hour < 12:
                hour += 12
            elif time_match.group(3) and time_match.group(3).lower() == 'am' and hour == 12:
                hour = 0
        
        # Create parameter dictionary
        params = {
            'origin': origin,
            'destination': destination,
            'hour': hour,
        }
        
        return params
    
    def get_route_explanation(self, params):
        """
        Generate explanation for why a specific route was chosen
        
        Args:
            route_id: Identifier for the route
            params: Dictionary with route parameters
            
        Returns:
            String explanation of route safety considerations
        """
        
        # Build prompt for LLM
        prompt = self._build_explanation_prompt(params)
        
        # Generate explanation
        explanation = self._generate_explanation(prompt)
        
        return explanation
    
    def _build_explanation_prompt(self, route_data, params):
        """Create prompt for the LLM to generate route explanation"""
        # Extract route information
        origin = params.get('origin', 'origen')
        destination = params.get('destination', 'destino')
        hour = params.get('hour')
        
        # Time context
        time_description = "desconocida"
        time_risk = "normal"
        if hour is not None:
            if 0 <= hour < 5:
                time_description = "madrugada"
                time_risk = "alto"
            elif 5 <= hour < 10:
                time_description = "mañana"
                time_risk = "bajo"
            elif 10 <= hour < 13:
                time_description = "mediodía"
                time_risk = "moderado"
            elif 13 <= hour < 17:
                time_description = "tarde"
                time_risk = "moderado"
            elif 17 <= hour < 21:
                time_description = "noche"
                time_risk = "alto"
            else:
                time_description = "medianoche"
                time_risk = "alto"
        
        # Avoided areas information
        #avoided_areas = route_data.get('avoided_areas', [])
        #avoided_areas_str = ", ".join(avoided_areas) if avoided_areas else "ninguna área de alto riesgo"
        
        # Crime types in avoided areas
        '''avoided_crime_types = route_data.get('avoided_crime_types', [])
        crime_types_str = ", ".join(avoided_crime_types) if avoided_crime_types else "ningún tipo de delito específico"
        '''
        # Build prompt
        prompt = f"""
        Origen: {origin}
        Destino: {destination}
        Hora del día: {time_description} ({hour}:00 horas)
        Nivel de riesgo por horario: {time_risk}
        
        Explica por qué esta ruta es la más segura comparando con la otra ruta más rápida, mencionando las áreas peligrosas que se evitaron y por qué son peligrosas (tipos de crímenes, horarios). Menciona también cómo el horario de viaje afecta la seguridad. La explicación debe ser clara, informativa y escrita en español.
        """
        #Áreas evitadas: {avoided_areas_str}
        
        return prompt
    
    def _generate_explanation(self, prompt):
        """Generate explanation using LLM"""
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[prompt]
        )        
            
        return response

# Modo     
def conect():
    chatbot = SafeRouteChatbot()
    
    print("Modo interactivo. Escribe 'salir' para terminar.")
    while True:
        try:
            user_input = input("\n¿Qué ruta quieres consultar? > ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                break
                
            # Process user input
            response = chatbot.generate_response(user_input)
            print("\nRespuesta:")
            print(response)
            
        except KeyboardInterrupt:
            print("\nSesión terminada.")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    if False:
        user_input = input("\n¿Qué ruta quieres consultar? > ")
        response = chatbot.free(user_input)
        print("\nRespuesta:")
        print(response)

    
        