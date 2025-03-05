from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from google.cloud.dialogflow_cx_v3 import SessionsClient, types
from app.core.config import settings
import io
import json

class VoiceService:
    def __init__(self):
        self.speech_client = speech_v1.SpeechClient()
        self.tts_client = texttospeech_v1.TextToSpeechClient()
        self.dialogflow_client = SessionsClient()
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = "us-central1"  # Default location, can be configured in settings
        self.agent_id = settings.DIALOGFLOW_PROJECT_ID
        self.language_code = settings.DIALOGFLOW_LANGUAGE_CODE

    async def speech_to_text(self, audio_content: bytes) -> str:
        """
        Convert speech to text using Google Cloud Speech-to-Text API
        """
        audio = speech_v1.RecognitionAudio(content=audio_content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language_code,
            enable_automatic_punctuation=True
        )

        response = await self.speech_client.recognize(config=config, audio=audio)
        if not response.results:
            return ""

        return response.results[0].alternatives[0].transcript

    async def text_to_speech(self, text: str, language_code: str = "en-US") -> bytes:
        """
        Convert text to speech using Google Cloud Text-to-Speech API
        """
        synthesis_input = texttospeech_v1.SynthesisInput(text=text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3
        )

        response = await self.tts_client.synthesize_speech(
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
        text = await self.speech_to_text(audio_content)
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
        return await self.text_to_speech(text, language_code)

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