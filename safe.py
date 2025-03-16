
import os
import re
import json
from google import genai
from dotenv import load_dotenv
from collections import Counter
from geopy.geocoders import Nominatim


load_dotenv()

API_KEY = os.getenv("API_KEY")

print(API_KEY)

client = genai.Client(api_key = API_KEY)

# Buscar una ubicació


#  Adaptar las llamadas a diferentes funciones dependiendo de la hora del día.

class SafeRouteChatbot:

    def free(self, user_message):
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=[user_message]
        )        
        return response
        
    
    def generate_response(self, origen, destino, context):
        # Configurar el geocodificador
        geolocator = Nominatim(user_agent="geoapiExercises")

        # Obtener la dirección
        orig = geolocator.reverse((origen[0], origen[1]), language="es") 
        dest = geolocator.reverse((destino[0], destino[1]), language="es")
    # Process user input
        params = self.process_user_input(origen, destino)
        # Get the most frequent terms in the context
        most_common_terms = Counter(context).most_common()
        
        # Check if we have enough information
        if not params['origin'] or not params['destination']:
            return "Necesito saber tu origen y destino para recomendarte una ruta segura. Por favor, indícame desde dónde y hasta dónde quieres ir."
        
        
        # Generate explanation for both routes
        safest_route_explanation = self.get_route_explanation(most_common_terms, params)
        
        # Combine explanations
           
        return safest_route_explanation
        
        # Load routing data if available
        
    # NECESITO =====> HOTINFO (delito, frecuencia, hora_más_alta), RouteData (rutas, seguridad, horarios)
    
    def process_user_input(self, origin, destination):
       
        # Create parameter dictionary
        params = {
            'origin': origin,
            'destination': destination,
            }
        
        return params
    
    def get_route_explanation(self, most_common_terms, params):
        """
        Generate explanation for why a specific route was chosen
        
        Args:
            route_id: Identifier for the route
            params: Dictionary with route parameters
            
        Returns:
            String explanation of route safety considerations
        """
        
        # Build prompt for LLM
        prompt = self._build_explanation_prompt(most_common_terms, params)
        
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
        El delicto más frecuente en la ruta es: {route_data}
    
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
    

'''
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

    
        '''