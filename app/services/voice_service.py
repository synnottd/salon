from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from app.core.config import settings
import io

class VoiceService:
    def __init__(self):
        self.speech_client = speech_v1.SpeechClient()
        self.tts_client = texttospeech_v1.TextToSpeechClient()

    async def speech_to_text(self, audio_content: bytes) -> str:
        """
        Convert speech to text using Google Cloud Speech-to-Text API
        """
        audio = speech_v1.RecognitionAudio(content=audio_content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=settings.DIALOGFLOW_LANGUAGE_CODE,
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

    async def process_voice_command(self, audio_content: bytes) -> dict:
        """
        Process a voice command and return structured data
        """
        text = await self.speech_to_text(audio_content)
        # Here you would integrate with DialogFlow to process the text
        # and return structured data about the command
        return {
            "text": text,
            "intent": "booking",  # This would come from DialogFlow
            "entities": {}  # This would come from DialogFlow
        }

    async def generate_response(self, text: str) -> bytes:
        """
        Generate a voice response for the given text
        """
        return await self.text_to_speech(text) 