import os
import json
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables (API KEY)
load_dotenv()

class AIAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-nano") 
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def is_configured(self) -> bool:
        return self.client is not None

    def parse_instruction(self, user_input: str) -> Dict[str, Any]:
        """
        Analyzes the user's instruction and determines which tool to use and with what parameters.
        """
        if not self.client:
            return {"error": "API Key not configured"}

        # Tool definitions for the LLM
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_dataset",
                    "description": "Use when the user wants to download images, create a dataset, search for photos in openverse, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search term (e.g. 'red cats')"},
                            "num": {"type": "integer", "description": "Number of images"},
                            "name": {"type": "string", "description": "Dataset name"},
                            "train_ratio": {"type": "number", "description": "Training ratio (0.0-1.0)"},
                            "val_ratio": {"type": "number", "description": "Validation ratio"},
                            "test_ratio": {"type": "number", "description": "Test ratio"},
                            "size": {"type": "integer", "description": "Size in pixels"},
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
                    "description": "Use when the user wants to scrape a specific website, use the crawler or custom search engine.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "Search keyword"},
                            "num_pages": {"type": "integer", "description": "Number of pages to crawl"},
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
                    {"role": "system", "content": "You are an expert assistant in data engineering and ML. Your job is to interpret natural language commands to configure CLI tools."},
                    {"role": "user", "content": user_input}
                ],
                tools=tools,
                tool_choice="auto"
            )

            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                # Process the function call
                function_name = tool_calls[0].function.name
                function_args = json.loads(tool_calls[0].function.arguments)
                
                # Explicitly inject the tool identifier
                if function_name == "generate_dataset":
                    function_args['tool'] = 'dataset_generator'
                    # Smart default values if the LLM doesn't infer them
                    if 'train_ratio' not in function_args: 
                        function_args.update({'train_ratio': 0.7, 'val_ratio': 0.15, 'test_ratio': 0.15})
                    if 'size' not in function_args: 
                        function_args['size'] = 256
                    
                elif function_name == "run_web_crawler":
                    function_args['tool'] = 'web_crawler'
                    if 'num_pages' not in function_args: 
                        function_args['num_pages'] = 5

                return function_args
            else:
                return {"tool": "chat", "message": response.choices[0].message.content}

        except Exception as e:
            return {"error": str(e)}
