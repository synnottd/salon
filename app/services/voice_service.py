from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from google.cloud.dialogflowcx_v3 import SessionsClient, types
from app.core.config import settings
import io
import json
from typing import Optional, BinaryIO, Tuple
import tempfile
import os
from pathlib import Path
import speech_recognition as sr
from gtts import gTTS
import whisper
from pydantic import BaseSettings
import ssl
import certifi
import urllib.request
import logging

class VoiceServiceSettings(BaseSettings):
    WHISPER_MODEL: str = "tiny"  # Can be "tiny", "base", "small", "medium", "large"
    TTS_LANGUAGE: str = "en"
    TTS_PROVIDER: str = "gtts"  # Can be "gtts" or "google_cloud"
    STT_PROVIDER: str = "whisper"  # Can be "whisper" or "google_cloud"
    GOOGLE_CLOUD_CREDENTIALS: Optional[str] = None

    class Config:
        env_file = ".env"

# Valid services offered by the salon
VALID_SERVICES = {
    'haircut': ['haircut', 'cut', 'trim'],
    'massage': ['massage', 'body massage', 'therapeutic massage'],
    'facial': ['facial', 'face treatment', 'facial treatment'],
    'manicure': ['manicure', 'nails', 'nail care'],
    'pedicure': ['pedicure', 'foot care'],
    'hair coloring': ['color', 'hair color', 'hair coloring', 'dye', 'hair dye'],
    'styling': ['style', 'hair style', 'styling', 'hair styling']
}

class VoiceService:
    def __init__(self):
        self.settings = VoiceServiceSettings()
        
        # Initialize optional Google Cloud clients
        self.speech_client = None
        self.tts_client = None
        if self.settings.GOOGLE_CLOUD_CREDENTIALS and os.path.exists(self.settings.GOOGLE_CLOUD_CREDENTIALS):
            try:
                self.speech_client = speech_v1.SpeechClient()
                self.tts_client = texttospeech_v1.TextToSpeechClient()
            except Exception as e:
                print(f"Failed to initialize Google Cloud clients: {e}")
        
        # Initialize Whisper model
        if self.settings.STT_PROVIDER == "whisper":
            try:
                # Set SSL certificate verification for macOS
                if os.path.exists("/private/etc/ssl/cert.pem"):
                    os.environ["SSL_CERT_FILE"] = "/private/etc/ssl/cert.pem"
                else:
                    os.environ["SSL_CERT_FILE"] = certifi.where()
                
                # Start with tiny model for faster loading and testing
                self.whisper_model = whisper.load_model(self.settings.WHISPER_MODEL)
            except Exception as e:
                print(f"Failed to load Whisper model: {e}")
                # Fallback to using Google Cloud if available
                if self.speech_client:
                    print("Falling back to Google Cloud Speech-to-Text")
                    self.settings.STT_PROVIDER = "google_cloud"
                else:
                    print("WARNING: No speech-to-text service available")
                    self.settings.STT_PROVIDER = None
        
        self.recognizer = sr.Recognizer()
        self.logger = logging.getLogger(__name__)

    def validate_service(self, service_value: str) -> Tuple[Optional[str], bool]:
        """
        Validate if a service is offered by the salon.
        Returns (normalized_service, is_valid) tuple.
        """
        if not service_value:
            return None, False
            
        service_value = service_value.lower()
        
        # Check if the service matches any of our valid services or their aliases
        for service, aliases in VALID_SERVICES.items():
            if service_value == service or service_value in aliases:
                return service, True
                
        return service_value, False

    async def handle_invalid_service(self, session_id: str, invalid_service: str) -> dict:
        """
        Handle an invalid service by updating Rasa's conversation state
        and returning an appropriate response.
        """
        from app.services.rasa_service import rasa_service
        
        # Create a message to inform about invalid service
        message = (
            f"I apologize, but '{invalid_service}' is not a service we offer. "
            f"Our available services include: {', '.join(VALID_SERVICES.keys())}. "
            "Could you please choose from one of these?"
        )
        
        # Send a custom event to Rasa to update the conversation state
        await rasa_service.send_custom_event(
            session_id,
            "invalid_service",
            {
                "service": invalid_service,
                "valid_services": list(VALID_SERVICES.keys())
            }
        )
        
        return {
            "text": message,
            "intent": {"name": "invalid_service", "confidence": 1.0},
            "entities": []
        }

    def extract_service_from_rasa(self, rasa_response: dict) -> Optional[str]:
        """
        Extract service entity from Rasa response.
        """
        entities = rasa_response.get('entities', [])
        service_entities = [e for e in entities if e['entity'] == 'service']
        
        if not service_entities:
            return None
            
        return service_entities[0]['value']

    async def speech_to_text(self, audio_file: BinaryIO) -> str:
        """Convert speech to text using the configured provider."""
        if not self.settings.STT_PROVIDER:
            raise ValueError("No speech-to-text service available")
            
        if self.settings.STT_PROVIDER == "whisper":
            if not hasattr(self, 'whisper_model'):
                raise ValueError("Whisper model not initialized")
            return await self._whisper_speech_to_text(audio_file)
        elif self.settings.STT_PROVIDER == "google_cloud":
            if not self.speech_client:
                raise ValueError("Google Cloud Speech client not initialized")
            return await self._google_speech_to_text(audio_file)
        else:
            raise ValueError(f"Unsupported STT provider: {self.settings.STT_PROVIDER}")

    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using the configured provider."""
        if self.settings.TTS_PROVIDER == "gtts":
            return await self._gtts_text_to_speech(text)
        elif self.settings.TTS_PROVIDER == "google_cloud":
            if not self.tts_client:
                raise ValueError("Google Cloud Text-to-Speech client not initialized. Check your credentials.")
            return await self._google_text_to_speech(text)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.settings.TTS_PROVIDER}")

    async def _whisper_speech_to_text(self, audio_file: BinaryIO) -> str:
        """Use OpenAI's Whisper model for speech-to-text conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_file.read())
            temp_path = temp_file.name

        try:
            result = self.whisper_model.transcribe(temp_path)
            return result["text"].strip()
        finally:
            os.unlink(temp_path)

    async def _google_speech_to_text(self, audio_file: BinaryIO) -> str:
        """Use Google Cloud Speech-to-Text API."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_file.read())
            temp_path = temp_file.name

        try:
            with open(temp_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech_v1.RecognitionAudio(content=content)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",
                model="default"
            )

            response = self.speech_client.recognize(config=config, audio=audio)
            
            if not response.results:
                return ""
                
            return response.results[0].alternatives[0].transcript
        finally:
            os.unlink(temp_path)

    async def _gtts_text_to_speech(self, text: str) -> bytes:
        """Use gTTS (Google Text-to-Speech) for text-to-speech conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=self.settings.TTS_LANGUAGE)
            tts.save(temp_file.name)
            temp_path = temp_file.name

        try:
            with open(temp_path, "rb") as audio_file:
                return audio_file.read()
        finally:
            os.unlink(temp_path)

    async def _google_text_to_speech(self, text: str) -> bytes:
        """Use Google Cloud Text-to-Speech API."""
        synthesis_input = texttospeech_v1.SynthesisInput(text=text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=self.settings.TTS_LANGUAGE,
            ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3
        )

        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content

    async def process_voice_command(self, audio_content: bytes, session_id: str = None) -> dict:
        """
        Process a voice command and return structured data using Dialogflow CX
        """
        # First convert speech to text
        text = await self.speech_to_text(io.BytesIO(audio_content))
        if not text:
            return {
                "text": "",
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0
            }

        # Create a session path
        session_path = self.dialogflow_client.session_path(
            project=self.project_id,
            location=self.location,
            agent=self.agent_id,
            session=session_id or "default"
        )

        # Create the text input
        text_input = types.TextInput(
            text=text,
            language_code=self.language_code
        )

        # Create the query input
        query_input = types.QueryInput(
            text=text_input,
            language_code=self.language_code
        )

        # Detect intent
        response = await self.dialogflow_client.detect_intent(
            request={
                "session": session_path,
                "query_input": query_input
            }
        )

        # Extract intent and entities
        intent = response.query_result.intent.display_name
        entities = {}
        
        for param in response.query_result.parameters:
            if param.value:
                entities[param.name] = param.value

        return {
            "text": text,
            "intent": intent,
            "entities": entities,
            "confidence": response.query_result.intent_detection_confidence,
            "fulfillment_text": response.query_result.fulfillment_text
        }

    async def generate_response(self, text: str, language_code: str = "en-US") -> bytes:
        """
        Generate a voice response for the given text
        """
        return await self.text_to_speech(text)

    async def handle_conversation(self, audio_content: bytes, session_id: str = None) -> dict:
        """
        Handle a complete conversation turn, including intent detection and response generation
        """
        # Process the voice command
        command_data = await self.process_voice_command(audio_content, session_id)
        
        # Generate appropriate response based on intent
        if command_data["intent"] == "booking":
            response_text = command_data.get("fulfillment_text", 
                "I understand you want to book an appointment. Could you please specify the service you're interested in?")
        elif command_data["intent"] == "cancel":
            response_text = command_data.get("fulfillment_text",
                "I understand you want to cancel an appointment. Could you please provide your appointment details?")
        elif command_data["intent"] == "check_availability":
            response_text = command_data.get("fulfillment_text",
                "I'll help you check availability. What service and date are you interested in?")
        else:
            response_text = command_data.get("fulfillment_text",
                "I'm not sure I understand. Could you please repeat that?")

        # Generate voice response
        response_audio = await self.generate_response(response_text)

        return {
            "text": response_text,
            "audio": response_audio,
            "command_data": command_data
        }

voice_service = VoiceService() 