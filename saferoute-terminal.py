#!/usr/bin/env python3
import sys
import argparse
from safe import SafeRouteChatbot

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SafeRouteChatbot - Consulta rutas seguras desde la terminal')
    parser.add_argument('--crime-data', required=True, help='Ruta al archivo CSV con datos de crímenes')
    parser.add_argument('--route-data', help='Ruta al archivo JSON con datos de rutas precalculadas')
    parser.add_argument('--model-path', help='Ruta al modelo de lenguaje preentrenado')
    parser.add_argument('--query', help='Consulta directa (opcional)')
    
    args = parser.parse_args()
    
    # Initialize the chatbot
    try:
        chatbot = SafeRouteChatbot(
            crime_data_path=args.crime_data,
            route_data_path=args.route_data,
            model_path=args.model_path
        )
        print("SafeRouteChatbot inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar el chatbot: {e}")
        sys.exit(1)
    
    # Process direct query if provided
    if args.query:
        response = chatbot.generate_response(args.query)
        print("\nRespuesta:")
        print(response)
        sys.exit(0)
    
    # Interactive mode
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

if __name__ == "__main__":
    main()
