from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from app.services.rasa_service import rasa_service

router = APIRouter()

class ConversationRequest(BaseModel):
    message: str
    session_id: str = None

class Intent(BaseModel):
    name: str
    confidence: float

class Entity(BaseModel):
    entity: str
    value: str
    start: int
    end: int
    confidence_entity: float
    extractor: str
    processors: List[str]

class ConversationResponse(BaseModel):
    session_id: str
    intent: Intent
    entities: List[Entity]
    text: str
    confidence: float

@router.post("/detect-intent", response_model=ConversationResponse)
async def detect_intent(request: ConversationRequest):
    """
    Detect intent from user message using Rasa
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get response from Rasa
        response = await rasa_service.detect_intent(
            message=request.message,
            sender_id=session_id
        )
        
        # Convert the raw response into our Pydantic models
        intent_data = response.get("intent", {})
        intent = Intent(
            name=intent_data.get("name", ""),
            confidence=intent_data.get("confidence", 0.0)
        )
        
        entities = [
            Entity(
                entity=e.get("entity", ""),
                value=e.get("value", ""),
                start=e.get("start", 0),
                end=e.get("end", 0),
                confidence_entity=e.get("confidence_entity", 1.0),
                extractor=e.get("extractor", ""),
                processors=e.get("processors", [])
            )
            for e in response.get("entities", [])
        ]
        
        return ConversationResponse(
            session_id=session_id,
            intent=intent,
            entities=entities,
            text=response.get("text", ""),
            confidence=response.get("confidence", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 