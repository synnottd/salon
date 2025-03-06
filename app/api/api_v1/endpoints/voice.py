import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.voice_service import VoiceService, voice_service
from app.services.appointment_service import AppointmentService
from app.models import Customer
from fastapi.responses import StreamingResponse, JSONResponse, Response
import io
from app.services.rasa_service import rasa_service
import uuid
import json
from typing import Optional, List, Tuple

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-command")
async def process_voice_command(
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Process a voice command and return appropriate response
    """
    try:
        audio_content = await audio_file.read()
        voice_service = VoiceService()
        appointment_service = AppointmentService(db)

        # Process the voice command
        command_data = await voice_service.process_voice_command(audio_content)
        
        # Here you would implement the logic to handle different intents
        # For example, booking an appointment, checking availability, etc.
        # This is a simplified example
        if command_data["intent"] == "booking":
            response_text = "I understand you want to book an appointment. Could you please specify the service you're interested in?"
        else:
            response_text = "I'm not sure I understand. Could you please repeat that?"

        # Generate voice response
        response_audio = await voice_service.generate_response(response_text)

        return {
            "text": response_text,
            "audio": response_audio,
            "command_data": command_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text-to-speech")
async def text_to_speech(
    text: str,
    language_code: str = "en-US"
):
    """
    Convert text to speech
    """
    try:
        voice_service = VoiceService()
        audio_content = await voice_service.generate_response(text, language_code)
        return {"audio": audio_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speech-to-text")
async def convert_speech_to_text(audio: UploadFile = File(...)):
    """
    Convert speech audio to text.
    Accepts WAV audio file and returns the transcribed text.
    """
    try:
        contents = await audio.read()
        text = await voice_service.speech_to_text(io.BytesIO(contents))
        return {"text": text}
    except Exception as e:
        logger.error(f"Speech-to-text conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text-to-speech")
async def convert_text_to_speech(text: str):
    """
    Convert text to speech.
    Returns an audio file (MP3 format) of the synthesized speech.
    """
    try:
        audio_content = await voice_service.text_to_speech(text)
        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/mp3"
        )
    except Exception as e:
        logger.error(f"Text-to-speech conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class AudioJSONResponse(Response):
    def __init__(self, audio_content: bytes, json_data: dict):
        # Create multipart boundary
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        
        # Create multipart content
        content = (
            f"--{boundary}\r\n"
            "Content-Type: audio/mp3\r\n"
            "Content-Disposition: attachment; filename=response.mp3\r\n\r\n"
        ).encode()
        content += audio_content
        content += f"\r\n--{boundary}\r\n".encode()
        content += (
            "Content-Type: application/json\r\n\r\n"
            f"{json.dumps(json_data)}\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        
        super().__init__(
            content=content,
            media_type=f"multipart/mixed; boundary={boundary}"
        )

@router.post("/conversation")
async def voice_conversation(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Query(None, description="Session ID for maintaining conversation context")
):
    """
    Handle voice conversation with the salon assistant.
    If session_id is not provided, a new one will be generated.
    """
    logger.info("Starting voice conversation processing")
    
    # Use provided session_id or generate a new one
    conversation_id = session_id if session_id else str(uuid.uuid4())
    logger.info(f"Using session ID: {conversation_id}")

    try:
        # Read the audio content
        audio_content = await audio.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio content")

        # Convert speech to text
        text = await voice_service.speech_to_text(io.BytesIO(audio_content))
        logger.info(f"Transcribed text: {text}")

        # Get response from Rasa
        rasa_response = await rasa_service.detect_intent(text, conversation_id)
        logger.info(f"Rasa response: {rasa_response}")

        # Extract and validate service if present
        service = voice_service.extract_service_from_rasa(rasa_response)
        if service:
            normalized_service, is_valid = voice_service.validate_service(service)
            if not is_valid:
                # Handle invalid service with Rasa
                rasa_response = await voice_service.handle_invalid_service(conversation_id, service)
        
        # Convert response to speech
        audio_response = await voice_service.text_to_speech(rasa_response['text'])

        # Prepare the multipart response
        response_data = {
            'session_id': conversation_id,
            'user_text': text,
            'bot_text': rasa_response['text'],
            'rasa_response': rasa_response,
            'service_validation': {
                'service': service,
                'normalized_service': normalized_service if service else None,
                'is_valid': is_valid if service else None
            } if service else None
        }

        # Create a multipart response with both audio and JSON
        boundary = 'boundary123'
        
        def generate():
            # JSON part
            yield f'--{boundary}\r\n'
            yield 'Content-Type: application/json\r\n\r\n'
            yield f'{json.dumps(response_data)}\r\n'
            
            # Audio part
            yield f'--{boundary}\r\n'
            yield 'Content-Type: audio/mp3\r\n\r\n'
            yield audio_response
            
            # End boundary
            yield f'\r\n--{boundary}--\r\n'

        return StreamingResponse(
            generate(),
            media_type=f'multipart/mixed; boundary={boundary}'
        )

    except Exception as e:
        logger.error(f"Error in voice conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 