import os
import json
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno (API KEY)
load_dotenv()

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        # Nota: Usamos gpt-4o-mini como placeholder funcional para "gpt-5-nano" 
        # hasta que el modelo exacto esté disponible públicamente.
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-nano") 
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def is_configured(self) -> bool:
        return self.client is not None

    def parse_instruction(self, user_input: str) -> Dict[str, Any]:
        """
        Analiza la instrucción del usuario y determina qué herramienta usar y con qué parámetros.
        """
        if not self.client:
            return {"error": "API Key no configurada"}

        # Definición de herramientas para el LLM
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_dataset",
                    "description": "Utilizar cuando el usuario quiere descargar imagenes, crear un dataset, buscar fotos en openverse, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Término de búsqueda (ej. 'gatos rojos')"},
                            "num": {"type": "integer", "description": "Número de imágenes"},
                            "name": {"type": "string", "description": "Nombre del dataset"},
                            "train_ratio": {"type": "number", "description": "Ratio de entrenamiento (0.0-1.0)"},
                            "val_ratio": {"type": "number", "description": "Ratio de validación"},
                            "test_ratio": {"type": "number", "description": "Ratio de prueba"},
                            "size": {"type": "integer", "description": "Tamaño en pixeles"},
                            "tool": {"type": "string", "enum": ["dataset_generator"], "const": "dataset_generator"}
                        },
                        "required": ["query", "num", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_web_crawler",
                    "description": "Utilizar cuando el usuario quiere scrapear una web específica, usar el crawler o buscador personalizado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "Keyword para búsqueda"},
                            "num_pages": {"type": "integer", "description": "Número de páginas a crawlear"},
                            "tool": {"type": "string", "enum": ["web_crawler"], "const": "web_crawler"}
                        },
                        "required": ["keyword"]
                    }
                }
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en ingeniería de datos y ML. Tu trabajo es interpretar comandos de lenguaje natural para configurar herramientas de CLI."},
                    {"role": "user", "content": user_input}
                ],
                tools=tools,
                tool_choice="auto"
            )

            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                # Procesar la llamada a función
                function_name = tool_calls[0].function.name
                function_args = json.loads(tool_calls[0].function.arguments)
                
                # Inyectar el identificador de herramienta explícitamente
                if function_name == "generate_dataset":
                    function_args['tool'] = 'dataset_generator'
                    # Valores por defecto inteligentes si el LLM no los deduce
                    if 'train_ratio' not in function_args: function_args.update({'train_ratio': 0.7, 'val_ratio': 0.15, 'test_ratio': 0.15})
                    if 'size' not in function_args: function_args['size'] = 256
                    
                elif function_name == "run_web_crawler":
                    function_args['tool'] = 'web_crawler'
                    if 'num_pages' not in function_args: function_args['num_pages'] = 5

                return function_args
            else:
                return {"tool": "chat", "message": response.choices[0].message.content}

        except Exception as e:
            return {"error": str(e)}