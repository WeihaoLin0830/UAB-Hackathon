import pandas as pd
import geopandas as gpd
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from shapely.geometry import Point, LineString
import re
from datetime import datetime
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

print(API_KEY)

client = genai.Client(api_key = API_KEY)


def get_routes(origin, destination, hour):
    """
    External function to get the safest and fastest routes.
    
    Args:
        origin: Starting location
        destination: Ending location
        hour: Time of day
        
    Returns:
        dict: Dictionary containing the safest and fastest routes
    """
    # Mock implementation, replace with actual logic
    safest_route = {
        'route_id': 'safest_route',
        'safety_score': 90,
        'time': 30,  # in minutes
        'avoided_areas': ['Area1', 'Area2'],
        'avoided_crime_types': ['Robo', 'Asalto']
    }
    
    fastest_route = {
        'route_id': 'fastest_route',
        'safety_score': 70,
        'time': 20,  # in minutes
        'avoided_areas': ['Area3'],
        'avoided_crime_types': ['Vandalismo']
    }
    
    return {
        'safest_route': safest_route,
        'fastest_route': fastest_route
    }

#  Adaptar las llamadas a diferentes funciones dependiendo de la hora del día.

class SafeRouteChatbot:

    def generate_response(self, user_message):
    # Process user input
        params = self.process_user_input(user_message)
        # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ==> lista de delitos, frecuencia, hora_más_alta
        route_data = 
        
        # Check if we have enough information
        if not params['origin'] or not params['destination']:
            return "Necesito saber tu origen y destino para recomendarte una ruta segura. Por favor, indícame desde dónde y hasta dónde quieres ir."
        
        # Get routes from external function
        routes = get_routes(params['origin'], params['destination'], params['hour'])
        
        # Generate explanation for both routes
        safest_route_explanation = self.get_route_explanation(routes['safest_route'], params)
        
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
    
    def get_route_explanation(self, route_data, params):
        """
        Generate explanation for why a specific route was chosen
        
        Args:
            route_id: Identifier for the route
            params: Dictionary with route parameters
            
        Returns:
            String explanation of route safety considerations
        """
        # Get route data (in practice, this would come from routing engine)
        route_data = route_data
        
        # Build prompt for LLM
        prompt = self._build_explanation_prompt(route_data, params)
        
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
        avoided_crime_types = route_data.get('avoided_crime_types', [])
        crime_types_str = ", ".join(avoided_crime_types) if avoided_crime_types else "ningún tipo de delito específico"
        
        
        # Build prompt
        prompt = f"""
        Origen: {origin}
        Destino: {destination}
        Hora del día: {time_description} ({hour}:00 horas)
        Nivel de riesgo por horario: {time_risk}
        Tipos de delitos comunes en áreas evitadas: {crime_types_str}
        
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
    
        