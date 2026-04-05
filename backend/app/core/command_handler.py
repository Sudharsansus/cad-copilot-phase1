# backend/app/core/command_handler.py
import os
import json
import logging
from openai import OpenAI, RateLimitError

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conversation_history = []

SYSTEM_PROMPT = """You are an AutoCAD AI Copilot for Tamil Nadu LPS (Land Plan Schedule) drawings.
You help civil engineers draw transmission line corridors, tower markers, SF land parcels, and boundary labels.

When the user gives a drawing command, respond ONLY with valid JSON in this format:
{
  "action": "draw_corridor",
  "message": "Human-readable description of what was done",
  "draw": [
    {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 0, "layer": "LPS_CORRIDOR"},
    {"type": "text", "x": 50, "y": 5, "content": "SF 10/2", "layer": "LPS_INFOBOX"},
    {"type": "circle", "cx": 50, "cy": 0, "radius": 2, "layer": "LPS_TOWER"}
  ]
}

Supported draw types: line, polyline, polygon, circle, text, rectangle
Layers: LPS_CORRIDOR, LPS_TOWER, LPS_INFOBOX, LPS_BOUNDARY
Use AutoCAD units (1 unit = 1 meter unless specified).
"""


def parse_command(file_id: str, command: str, drawing_context: dict = None) -> dict:
    global conversation_history

    user_msg = command
    if drawing_context:
        user_msg += f"\n\n[Drawing context: {json.dumps(drawing_context)}]"

    conversation_history.append({"role": "user", "content": user_msg})

    # Keep last 10 messages to avoid token overflow
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            response_format={"type": "json_object"},
            max_tokens=1024,
        )
        result = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": result})
        logger.info(f"Command executed: {command}")
        return json.loads(result)

    except RateLimitError:
        logger.warning("OpenAI 429 - quota exceeded")
        # Return a structured response so the plugin shows a proper error message
        return {
            "action": "error",
            "message": (
                "⚠️ OpenAI quota exceeded.\n\n"
                "To fix this:\n"
                "1. Go to platform.openai.com\n"
                "2. Add a payment method under Billing\n"
                "3. Add at least $5 credit\n\n"
                "GPT-4o-mini costs ~₹0.01 per message — very cheap."
            ),
            "draw": []
        }

    except Exception as ex:
        logger.error(f"Command error: {ex}", exc_info=True)
        return {
            "action": "error",
            "message": f"AI command failed: {str(ex)}",
            "draw": []
        }