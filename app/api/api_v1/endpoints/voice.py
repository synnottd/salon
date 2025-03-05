from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.voice_service import VoiceService
from app.services.appointment_service import AppointmentService
from app.core.auth import get_current_user
from app.db.models import Customer

router = APIRouter()

@router.post("/process-command")
async def process_voice_command(
    audio_file: UploadFile = File(...),
    current_user: Customer = Depends(get_current_user),
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