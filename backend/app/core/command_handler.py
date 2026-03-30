# command_handler.py - Chat Command Parser
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from app.utils.helpers import log_info, log_error

class CommandHandler:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.operations = ["buffer", "shift", "merge", "rotate", "dimension"]

    def parse_command(self, command_text: str) -> Optional[Dict[str, Any]]:
        try:
            log_info(f"Parsing command: {command_text}")

            prompt = f"""
            Parse this AutoCAD command and return JSON:
            Command: "{command_text}"

            Return ONLY JSON with:
            - operation: one of {self.operations}
            - element_type: what to modify
            - parameters: dictionary of parameters

            Example:
            {{"operation": "buffer", "element_type": "corridor", "parameters": {{"distance": 2.0}}}}
            """

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            if result.get("operation") not in self.operations:
                log_error(f"Invalid operation: {result.get('operation')}")
                return None

            log_info(f"Parsed operation: {result.get('operation')}")
            return result

        except Exception as e:
            log_error("Command parsing failed", e)
            return None

    def validate_parameters(self, operation: str, params: Dict) -> bool:
        if operation == "buffer":
            return "distance" in params and isinstance(params["distance"], (int, float))
        elif operation == "shift":
            return "direction" in params and "distance" in params
        elif operation == "merge":
            return "elements" in params and len(params["elements"]) >= 2
        elif operation == "rotate":
            return "angle" in params and isinstance(params["angle"], (int, float))
        elif operation == "dimension":
            return "element1" in params and "element2" in params
        return False


def parse_command(command_text: str, api_key: str) -> Optional[Dict[str, Any]]:
    handler = CommandHandler(api_key)
    return handler.parse_command(command_text)
