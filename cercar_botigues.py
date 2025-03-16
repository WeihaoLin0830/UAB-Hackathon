
import requests
import json
from math import radians, sin, cos, sqrt, atan2
from geopy.distance import geodesic
import geocoder
import re

from fuzzywuzzy import fuzz

def calcular_puntuacion_fuzzy(nombre, busqueda):
    """
    Calcula una puntuación basada en coincidencias aproximadas usando Fuzzy Matching.
    """
    return fuzz.partial_ratio(nombre.lower(), busqueda.lower())  # Devuelve un score de 0 a 100


def determinar_tipo_lugar(tags):
    """
    Determina un tipo de lugar descriptivo basado en los tags
    
    Args:
        tags (dict): Diccionario de tags de OSM
        
    Returns:
        str: Descripción del tipo de lugar
    """
    # Priorizar la información más descriptiva
    if "cuisine" in tags:
        if tags["cuisine"] == "pizza":
            return "Pizzería"
        elif tags["cuisine"] == "burger":
            return "Hamburguesería"
        elif tags["cuisine"] == "mexican":
            return "Restaurante Mexicano"
        elif tags["cuisine"] == "japanese":
            return "Restaurante Japonés"
        elif tags["cuisine"] == "chinese":
            return "Restaurante Chino"

def buscar_lugares_cercanos(busqueda, lat, lon, radio=5000):
    """
    Busca lugares cercanos usando la API de Overpass (OpenStreetMap) con filtros mejorados
    
    Args:
        busqueda (str): Término de búsqueda (restaurante, tienda, producto, etc.)
        lat (float): Latitud de la ubicación
        lon (float): Longitud de la ubicación
        radio (int): Radio de búsqueda en metros
        
    Returns:
        list: Lista de lugares encontrados ordenados por distancia
    """
    # Convertimos la búsqueda a minúsculas para hacer la comparación insensible a mayúsculas
    termino_busqueda = busqueda.lower()
    palabras_clave = re.split(r'[\s,]+', termino_busqueda)  # Dividir en palabras clave
    
    # Categorías y tags para buscar
    categorias = identificar_categorias(termino_busqueda)
    
    # Construimos la consulta Overpass más completa
    overpass_query = f"""
    [out:json][timeout:25];
    (
    """
    
    # Añadir búsquedas específicas según categorías identificadas
    for categoria in categorias:
        overpass_query += f"""
        // Buscar {categoria["nombre"]}
        node["{categoria["key"]}"="{categoria["value"]}"](around:{radio},{lat},{lon});
        way["{categoria["key"]}"="{categoria["value"]}"](around:{radio},{lat},{lon});
        relation["{categoria["key"]}"="{categoria["value"]}"](around:{radio},{lat},{lon});
        """
    
    # Añadir búsquedas genéricas
    overpass_query += f"""
      // Buscar restaurantes generales
      node["amenity"="restaurant"](around:{radio},{lat},{lon});
      way["amenity"="restaurant"](around:{radio},{lat},{lon});
      
      // Buscar cafeterías
      node["amenity"="cafe"](around:{radio},{lat},{lon});
      way["amenity"="cafe"](around:{radio},{lat},{lon});
      
      // Buscar tiendas (shops)
      node["shop"](around:{radio},{lat},{lon});
      way["shop"](around:{radio},{lat},{lon});
      
      // Buscar supermercados
      node["shop"="supermarket"](around:{radio},{lat},{lon});
      way["shop"="supermarket"](around:{radio},{lat},{lon});
      
      // Buscar farmacias
      node["amenity"="pharmacy"](around:{radio},{lat},{lon});
      way["amenity"="pharmacy"](around:{radio},{lat},{lon});
      
      // Buscar mercados
      node["amenity"="marketplace"](around:{radio},{lat},{lon});
      way["amenity"="marketplace"](around:{radio},{lat},{lon});
      
      // Buscar puntos de interés con nombres
      node["name"](around:{radio},{lat},{lon});
      way["name"](around:{radio},{lat},{lon});

      node["brand"](around:{radio},{lat},{lon});
        way["brand"](around:{radio},{lat},{lon});
        node["opening_hours"](around:{radio},{lat},{lon});
        way["opening_hours"](around:{radio},{lat},{lon});
        node["phone"](around:{radio},{lat},{lon});
        way["phone"](around:{radio},{lat},{lon});
        node["website"](around:{radio},{lat},{lon});
        way["website"](around:{radio},{lat},{lon});
        node["review:count"](around:{radio},{lat},{lon});
        way["review:count"](around:{radio},{lat},{lon});
        node["review:rating"](around:{radio},{lat},{lon});
        way["review:rating"](around:{radio},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    
    # URL de la API de Overpass
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    try:
        # Realizar la consulta a la API
        response = requests.post(
            overpass_url, 
            data={"data": overpass_query},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        response.raise_for_status()  # Lanzar excepción si hay error HTTP
        data = response.json()

        '''import pprint
        pprint.pprint(data)'''
        
        # Filtrar los resultados según el término de búsqueda con un algoritmo de puntuación
        resultados = []
        for elemento in data.get("elements", []):
            tags = elemento.get("tags", {})
            
            # Verificar si hay suficientes datos para considerarlo
            if not tags:
                continue
                
            # Extraer información relevante
            nombre = tags.get("name", "").lower()
            cuisine = tags.get("cuisine", "").lower()
            tipo_tienda = tags.get("shop", "").lower()
            amenity = tags.get("amenity", "").lower()
            description = tags.get("description", "").lower()
            brand = tags.get("brand", "").lower()
            
            # Calcular puntuación de relevancia
            puntuacion = calcular_puntuacion(
                nombre, cuisine, tipo_tienda, amenity, description, brand,
                palabras_clave, termino_busqueda
            )
            puntuacion += calcular_puntuacion_fuzzy(nombre, termino_busqueda) // 2  # Agregar peso basado en fuzzy search

            
            # Si tiene una puntuación mínima, incluirlo en resultados
            if puntuacion > 0:
                # Extraer coordenadas según el tipo de elemento
                if elemento["type"] == "node":
                    lugar_lat = elemento.get("lat")
                    lugar_lon = elemento.get("lon")
                elif elemento["type"] in ["way", "relation"]:
                    # Para ways y relations, podemos aproximar usando el centro del bounds
                    bounds = elemento.get("bounds", {})
                    if bounds:
                        lugar_lat = (bounds.get("minlat", 0) + bounds.get("maxlat", 0)) / 2
                        lugar_lon = (bounds.get("minlon", 0) + bounds.get("maxlon", 0)) / 2
                    else:
                        continue  # Sin coordenadas, saltamos
                else:
                    continue  # Saltar si no podemos determinar coordenadas
                
                # Calcular distancia
                distancia = calcular_distancia(lat, lon, lugar_lat, lugar_lon)
                
                # Determinar el tipo de lugar para mostrar
                tipo_mostrar = determinar_tipo_lugar(tags)
                
                resultados.append({
                "nombre": tags.get("name", "Sin nombre"),
                "marca": tags.get("brand", "Desconocida"),
                "tipo_lugar": determinar_tipo_lugar(tags),
                "horarios": tags.get("opening_hours", "Horario no disponible"),
                "teléfono": tags.get("phone", "No disponible"),
                "web": tags.get("website", "No disponible"),
                "reseñas_count": tags.get("review:count", "0"),  # Número de reseñas
                "calificación": tags.get("review:rating", "No disponible"),  # Calificación promedio
                "dirección": obtener_direccion(tags),
                "latitud": lugar_lat,
                "longitud": lugar_lon,
                "distancia": distancia,
                "puntuacion": puntuacion,
                "tags": tags  # Guardar todos los tags para depuración
            })

        
        # Ordenar por puntuación (primero) y distancia (segundo criterio)
        resultados.sort(key=lambda x: (-x["puntuacion"], x["distancia"]))
        return resultados
        
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return []
    except Exception as e:
        print(f"Error general: {e}")
        return []

def calcular_puntuacion(nombre, cuisine, tipo_tienda, amenity, description, brand, palabras_clave, termino_busqueda):
    """
    Calcula una puntuación de relevancia para el lugar
    
    Args:
        nombre, cuisine, tipo_tienda, amenity, description, brand: Atributos del lugar
        palabras_clave: Lista de palabras clave de la búsqueda
        termino_busqueda: Término de búsqueda completo
    
    Returns:
        float: Puntuación de relevancia (0-100)
    """
    puntuacion = 0
    
    # Coincidencia exacta con el nombre (mayor peso)
    if nombre == termino_busqueda:
        puntuacion += 100
    elif termino_busqueda in nombre:
        puntuacion += 80
    
    # Coincidencia por palabras clave en el nombre
    for palabra in palabras_clave:
        if len(palabra) > 2 and palabra in nombre:
            puntuacion += 40
    
    # Coincidencia con la marca
    if termino_busqueda in brand:
        puntuacion += 70
    
    # Coincidencia con el tipo de cocina (restaurantes)
    if termino_busqueda in cuisine:
        puntuacion += 60
    
    # Coincidencia con el tipo de tienda
    if termino_busqueda in tipo_tienda:
        puntuacion += 50
    elif any(palabra in tipo_tienda for palabra in palabras_clave if len(palabra) > 2):
        puntuacion += 30
    
    # Coincidencia con el tipo de amenity
    if termino_busqueda in amenity:
        puntuacion += 40
    
    # Coincidencia con la descripción
    if termino_busqueda in description:
        puntuacion += 30
    
    # Limitar la puntuación máxima a 100
    return min(puntuacion, 100)

def identificar_categorias(termino):
    """
    Identifica categorías OSM relacionadas con el término de búsqueda
    
    Args:
        termino (str): Término de búsqueda
    
    Returns:
        list: Lista de diccionarios con categorías relevantes
    """
    categorias = []
    
    # Mapeo de términos comunes a categorías OSM
    mappings = [
        # Comidas y restaurantes
        {"terminos": ["taco", "tacos", "taqueria", "taquerias"], "key": "amenity", "value": "restaurant", "nombre": "taquerías"},
        {"terminos": ["taco", "tacos", "taqueria", "taquerias"], "key": "cuisine", "value": "mexican", "nombre": "comida mexicana"},
        {"terminos": ["pizza", "pizzeria", "pizzería"], "key": "cuisine", "value": "pizza", "nombre": "pizzerías"},
        {"terminos": ["burger", "hamburguesa", "hamburgueseria"], "key": "cuisine", "value": "burger", "nombre": "hamburguesas"},
        {"terminos": ["sushi", "japones", "japonesa"], "key": "cuisine", "value": "japanese", "nombre": "comida japonesa"},
        {"terminos": ["china", "chino", "chinos"], "key": "cuisine", "value": "chinese", "nombre": "comida china"},
        {"terminos": ["cafe", "café", "cafeteria"], "key": "amenity", "value": "cafe", "nombre": "cafeterías"},
        {"terminos": ["restaurante", "restaurant"], "key": "amenity", "value": "restaurant", "nombre": "restaurantes"},
        {"terminos": ["bar", "cantina", "pub"], "key": "amenity", "value": "bar", "nombre": "bares"},
        {"terminos": ["pasteleria", "pastelería", "panaderia"], "key": "shop", "value": "bakery", "nombre": "panaderías"},
        
        # Tiendas y comercios
        {"terminos": ["super", "supermercado", "supermarket"], "key": "shop", "value": "supermarket", "nombre": "supermercados"},
        {"terminos": ["farmacia", "botica", "medicina"], "key": "amenity", "value": "pharmacy", "nombre": "farmacias"},
        {"terminos": ["ropa", "vestido", "pantalones", "camisas"], "key": "shop", "value": "clothes", "nombre": "tiendas de ropa"},
        {"terminos": ["zapato", "zapatos", "calzado"], "key": "shop", "value": "shoes", "nombre": "zapaterías"},
        {"terminos": ["joyeria", "joyería"], "key": "shop", "value": "jewelry", "nombre": "joyerías"},
        {"terminos": ["electronica", "electrónica"], "key": "shop", "value": "electronics", "nombre": "tiendas de electrónica"},
        {"terminos": ["ferreteria", "ferretería"], "key": "shop", "value": "hardware", "nombre": "ferreterías"},
        {"terminos": ["libro", "libros", "libreria"], "key": "shop", "value": "books", "nombre": "librerías"},
        {"terminos": ["flor", "flores", "floristeria"], "key": "shop", "value": "florist", "nombre": "florerías"},
        {"terminos": ["mueble", "muebles", "muebleria"], "key": "shop", "value": "furniture", "nombre": "mueblerías"},
        
        # Servicios
        {"terminos": ["banco", "cajero", "atm"], "key": "amenity", "value": "bank", "nombre": "bancos"},
        {"terminos": ["gasolina", "gasolinera", "combustible"], "key": "amenity", "value": "fuel", "nombre": "gasolineras"},
        {"terminos": ["hotel", "motel", "hostal"], "key": "tourism", "value": "hotel", "nombre": "hoteles"},
        {"terminos": ["policia", "policía"], "key": "amenity", "value": "police", "nombre": "estaciones de policía"},
        {"terminos": ["escuela", "colegio", "universidad"], "key": "amenity", "value": "school", "nombre": "escuelas"},
        {"terminos": ["hospital", "clinica", "clínica"], "key": "amenity", "value": "hospital", "nombre": "hospitales"},
        {"terminos": ["doctor", "médico", "medico"], "key": "amenity", "value": "doctors", "nombre": "consultorios médicos"},
        {"terminos": ["dentista", "dental"], "key": "amenity", "value": "dentist", "nombre": "dentistas"},
        {"terminos": ["peluqueria", "peluquería", "salon", "salón"], "key": "shop", "value": "hairdresser", "nombre": "peluquerías"},
        {"terminos": ["lavanderia", "lavandería"], "key": "shop", "value": "laundry", "nombre": "lavanderías"},
    ]
    
    # Comprobar si el término coincide con alguna de las categorías
    for mapping in mappings:
        if any(term in termino.lower() for term in mapping["terminos"]):
            categorias.append(mapping)
    
    # Si no hay categorías identificadas, añadir búsqueda genérica
    if not categorias:
        categorias = [
            {"key": "name", "value": termino, "nombre": "lugares con este nombre"},
            {"key": "amenity", "value": "restaurant", "nombre": "restaurantes"},
            {"key": "shop", "value": "yes", "nombre": "tiendas"}
        ]
    
    return categorias

def obtener_direccion(tags):
    """
    Obtiene la dirección formateada de los tags
    
    Args:
        tags (dict): Diccionario de tags de OSM
        
    Returns:
        str: Dirección formateada
    """
    # Intentar obtener dirección completa
    if "addr:full" in tags:
        return tags["addr:full"]
    
    # Construir dirección a partir de componentes
    componentes = []
    
    # Calle y número
    calle = tags.get("addr:street", "")
    numero = tags.get("addr:housenumber", "")
    if calle and numero:
        componentes.append(f"{calle} {numero}")

    
def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando geopy
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
        
    Returns:
        float: Distancia en kilómetros, redondeada a 3 decimales
    """
    try:
        punto1 = (lat1, lon1)
        punto2 = (lat2, lon2)
        distancia = geodesic(punto1, punto2).kilometers
        return round(distancia, 3)
    except:
        # Fallback al cálculo manual usando la fórmula de Haversine
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distancia = R * c
        
        return round(distancia, 3)

def obtener_ubicacion_actual():
    """
    Obtiene la ubicación actual usando geocoder (principalmente para uso en servidor)
    
    Returns:
        tuple: (latitud, longitud) de la ubicación actual
    """
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng[0], g.latlng[1]
        else:
            raise Exception("No se pudo obtener la geolocalización")
    except Exception as e:
        print(f"Error al obtener ubicación: {e}")
        # Coordenadas predeterminadas (Zócalo de Ciudad de México)
        return 19.4326, -99.1332

def buscar_con_ubicacion_actual(busqueda, radio=1000):
    """
    Busca lugares cercanos a la ubicación actual
    
    Args:
        busqueda (str): Término de búsqueda
        radio (int): Radio de búsqueda en metros
        
    Returns:
        list: Lista de lugares encontrados
    """
    lat, lon = obtener_ubicacion_actual()
    print(f"Ubicación actual: {lat}, {lon}")
    
    return buscar_lugares_cercanos(busqueda, lat, lon, radio)

def buscar_con_coordenadas(busqueda, lat, lon, radio=5000):
    """
    Busca lugares cercanos a unas coordenadas específicas
    
    Args:
        busqueda (str): Término de búsqueda
        lat (float): Latitud
        lon (float): Longitud
        radio (int): Radio de búsqueda en metros
        
    Returns:
        list: Lista de lugares encontrados
    """
    return buscar_lugares_cercanos(busqueda, lat, lon, radio)

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo con coordenadas fijas (Ciudad de México - Zócalo)
    lat_cdmx = 19.4326
    lon_cdmx = -99.1332
    
    print("Buscando hamburguesa en Ciudad de México...")
    hamburguesas = buscar_con_coordenadas("hamburguesa", lat_cdmx, lon_cdmx, 5000)
    hamburguesas_top5 = hamburguesas[:5]  # Obtener solo los cinco más altos
    
    for i, hamburguesa in enumerate(hamburguesas_top5, 1):
        print(f"{i}. Nombre: {hamburguesa['nombre']}")
        print(f"   Marca: {hamburguesa['marca']}")
        print(f"   Tipo de lugar: {hamburguesa['tipo_lugar']}")
        print(f"   Horarios: {hamburguesa['horarios']}")
        print(f"   Teléfono: {hamburguesa['teléfono']}")
        print(f"   Web: {hamburguesa['web']}")
        print(f"   Reseñas_Count: {hamburguesa['reseñas_count']}")
        print(f"   Calificación: {hamburguesa['calificación']}")
        print(f"   Dirección: {hamburguesa['dirección']}")
        print(f"   Latitud: {hamburguesa['latitud']}")
        print(f"   Longitud: {hamburguesa['longitud']}")
        print(f"   Distancia: {hamburguesa['distancia']} km")
        print(f"   Puntuación: {hamburguesa['puntuacion']}")
        print(f"   Tags: {hamburguesa['tags']}")
        print()
    
    # Ejemplo con geolocalización por IP
    print("\nBuscando cafeterías cerca de tu ubicación actual...")
    cafeterias = buscar_con_ubicacion_actual("cafe", 1500)
    cafeterias_top5 = cafeterias[:5]  # Obtener solo los cinco más altos

# También puedes tomar los top 5 después de filtrar
    
    for i, cafe in enumerate(cafeterias_top5, 1):
        print(f"{i}. Nombre: {cafe['nombre']}")
        print(f"   Marca: {cafe['marca']}")
        print(f"   Tipo de lugar: {cafe['tipo_lugar']}")
        print(f"   Horarios: {cafe['horarios']}")
        print(f"   Teléfono: {cafe['teléfono']}")
        print(f"   Web: {cafe['web']}")
        print(f"   Reseñas_Count: {cafe['reseñas_count']}")
        print(f"   Calificación: {cafe['calificación']}")
        print(f"   Dirección: {cafe['dirección']}")
        print(f"   Latitud: {cafe['latitud']}")
        print(f"   Longitud: {cafe['longitud']}")
        print(f"   Distancia: {cafe['distancia']} km")
        print(f"   Puntuación: {cafe['puntuacion']}")
        print(f"   Tags: {cafe['tags']}")
        print()

