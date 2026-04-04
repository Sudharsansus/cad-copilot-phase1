# command_handler.py - AI Command Processing
import os
import json
from openai import OpenAI
from .system_prompt import SYSTEM_PROMPT

class CommandHandler:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Fast + cheap, perfect for commands
        self.conversation_history = []

    def process_command(self, command: str, file_id: str = None, context: dict = None) -> dict:
        """
        Process a natural language CAD command and return structured JSON response.
        Maintains conversation history for context-aware responses.
        """
        try:
            # Build context message if file/parcel data available
            context_msg = ""
            if context:
                context_msg = f"\nCurrent drawing context: {json.dumps(context)}"

            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": f"{command}{context_msg}"
            })

            # Keep history to last 10 messages to avoid token overflow
            recent_history = self.conversation_history[-10:]

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *recent_history
                ],
                temperature=0.1,  # Low temperature = consistent, precise responses
                max_tokens=500,
                response_format={"type": "json_object"}  # Force JSON response
            )

            # Extract response content
            content = response.choices[0].message.content

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })

            # Parse JSON response
            result = json.loads(content)

            # Ensure result field always exists
            if "result" not in result:
                result["result"] = "Command processed successfully"

            return result

        except json.JSONDecodeError as e:
            return {
                "action": "error",
                "result": f"AI response parsing failed: {str(e)}"
            }
        except Exception as e:
            return {
                "action": "error", 
                "result": f"Command processing failed: {str(e)}"
            }

    def clear_history(self):
        """Clear conversation history for new drawing session"""
        self.conversation_history = []

    def get_drawing_summary(self, parcels: list) -> str:
        """Generate a summary of the current drawing for AI context"""
        if not parcels:
            return "No parcels loaded"
        
        summary = f"Drawing has {len(parcels)} land parcels:\n"
        for p in parcels[:5]:  # First 5 parcels as context
            summary += f"- SF {p.get('sf_no', 'N/A')}: "
            summary += f"{p.get('village', 'N/A')}, "
            summary += f"Owner: {p.get('owner', 'N/A')}, "
            summary += f"Corridor: {p.get('corridor_sqm', 0)} sqm\n"
        
        if len(parcels) > 5:
            summary += f"... and {len(parcels) - 5} more parcels"
        
        return summary