import httpx
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class RasaService:
    def __init__(self):
        self.rasa_url = os.getenv("RASA_URL", "http://localhost:5005")
        self.logger = logging.getLogger(__name__)
    
    async def detect_intent(self, message: str, sender_id: str) -> Dict[Any, Any]:
        """
        Send a message to Rasa for intent detection and response generation
        
        Args:
            message (str): The user's message
            sender_id (str): Unique identifier for the conversation
            
        Returns:
            Dict: Rasa's response containing intent, entities, and response text
        """
        async with httpx.AsyncClient() as client:
            # First get the parsed intent and entities
            parse_response = await client.post(
                f"{self.rasa_url}/model/parse",
                json={"text": message}
            )
            
            if parse_response.status_code != 200:
                raise Exception(f"Error from Rasa parse: {parse_response.status_code} - {parse_response.text}")
                
            parse_data = parse_response.json()
            
            # Then get the bot response
            response = await client.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={
                    "sender": sender_id,
                    "message": message
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error from Rasa webhook: {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            # Combine the parse data with the response
            return {
                "intent": parse_data.get("intent", {}),
                "entities": parse_data.get("entities", []),
                "text": response_data[0].get("text", "") if response_data else "",
                "confidence": parse_data.get("intent_ranking", [{}])[0].get("confidence", 0)
            }

    async def send_custom_event(self, session_id: str, event_type: str, event_data: dict) -> None:
        """
        Send a custom event to Rasa to update the conversation state.
        """
        url = f"{self.rasa_url}/conversations/{session_id}/tracker/events"
        
        event = {
            "event": event_type,
            "timestamp": None,  # Rasa will set the timestamp
            "name": event_type,  # Required for custom events
            "data": event_data  # Put the data in the data field
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=[event])
                response.raise_for_status()
                self.logger.info(f"Sent custom event to Rasa: {event_type}")
        except httpx.HTTPError as e:
            self.logger.error(f"Failed to send event to Rasa: {str(e)}")
            # Don't raise the error - just log it and continue
            # This prevents the voice conversation from failing if event sending fails

rasa_service = RasaService() 