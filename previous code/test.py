
# Configurar la API de Azure OpenAI
from google import genai
import os
from dotenv import load_dotenv

# Carregar les variables d'entorn des del fitxer .env
load_dotenv()

# Llegir la clau API
API_KEY = os.getenv("API_KEY")

client = genai.Client(api_key=API_KEY)

# Formatear el prompt
prompt = f"""
Qué tiempo hace en Madrid hoy?
"""
response = client.models.generate_content(
    model="gemini-2.0-flash", contents=[prompt]
)

print(response)

'''
# Llamar a la API
response = openai.ChatCompletion.create(
    engine="gpt-4",  # O el deployment que hayas configurado
    messages=[
        {"role": "system", "content": "Eres un asistente experto en seguridad y rutas de viaje en España."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=500
)

# Imprimir la respuesta
print(response.choices[0].message.content)


'''
'''
prompt = f"""
        Origen: {'Madrid'}
        Destino: {'Barcelona'}
        Hora del día: {'Madrugada'} ({0}:00 horas)
        Nivel de riesgo por horario: {'alto'}
        Puntuación de seguridad: {50}/100
        Áreas evitadas: {'A1', 'A2'}
        Tipos de delitos comunes en áreas evitadas: {'DELITOS'}
        
        Explica por qué esta ruta es la más segura, mencionando las áreas peligrosas que se evitaron y por qué son peligrosas (tipos de crímenes, horarios). Menciona también cómo el horario de viaje afecta la seguridad. La explicación debe ser clara, informativa y escrita en español.
        """
from transformers import AutoTokenizer, AutoModelForCausalLM

# Cargar un modelo adecuado para generación en español
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2", is_decoder=True)
inputs = tokenizer(prompt, return_tensors="pt")

outputs = model.generate(
    inputs.input_ids,
    max_length=250,
    temperature=0.7,
    top_p=0.9,
    do_sample=True
)

decoded_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(decoded_text)

'''