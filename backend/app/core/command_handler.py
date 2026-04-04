# backend/app/core/command_handler.py
import os
import json
from openai import OpenAI
from app.core.system_prompt import SYSTEM_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conversation_history = []

def parse_command(file_id: str, command: str, drawing_context: dict = None) -> dict:
    global conversation_history

    # Build context message if drawing info available
    context_note = ""
    if drawing_context:
        context_note = f"\nCurrent drawing context: {json.dumps(drawing_context)}"

    conversation_history.append({
        "role": "user",
        "content": command + context_note
    })

    # Keep last 10 messages to avoid token overflow
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *conversation_history
            ]
        )

        reply = response.choices[0].message.content
        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

        return json.loads(reply)

    except Exception as e:
        return {
            "action": "error",
            "message": str(e),
            "draw": []
        }


def get_drawing_summary(entities: list) -> dict:
    return {
        "total_entities": len(entities),
        "layers": list(set(e.get("layer", "0") for e in entities))
    }