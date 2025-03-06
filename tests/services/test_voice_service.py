import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
import io
from datetime import datetime
from app.services.voice_service import VoiceService, VoiceServiceSettings, VALID_SERVICES

# Mock settings
@pytest.fixture
def mock_settings():
    return {
        "WHISPER_MODEL": "tiny",
        "TTS_LANGUAGE": "en",
        "TTS_PROVIDER": "gtts",
        "STT_PROVIDER": "whisper",
        "GOOGLE_CLOUD_CREDENTIALS": None
    }

# Mock all external dependencies
@pytest.fixture
def mock_dependencies(mock_settings):
    with patch.multiple(
        "app.services.voice_service",
        speech_v1=Mock(),
        texttospeech_v1=Mock(),
        SessionsClient=Mock(),
        whisper=Mock(),
        sr=Mock(),
        gTTS=Mock(),
        os=Mock(),
        Path=Mock(),
        certifi=Mock(),
        settings=Mock(**mock_settings)
    ) as mocks:
        yield mocks

@pytest.fixture
def voice_service(mock_dependencies):
    service = VoiceService()
    # Mock the whisper model
    service.whisper_model = Mock()
    service.whisper_model.transcribe.return_value = {"text": "test transcription"}
    
    # Add DialogFlow required attributes
    service.project_id = "test-project"
    service.location = "global"
    service.agent_id = "test-agent"
    service.language_code = "en"
    service.dialogflow_client = Mock()
    
    return service

@pytest.fixture
def sample_audio():
    return io.BytesIO(b"fake audio content")

# Test service validation
@pytest.mark.parametrize("input_service,expected_result", [
    ("haircut", ("haircut", True)),
    ("cut", ("haircut", True)),
    ("invalid service", ("invalid service", False)),
    (None, (None, False)),
    ("HAIRCUT", ("haircut", True)),
    ("massage", ("massage", True)),
])
async def test_validate_service(voice_service, input_service, expected_result):
    result = voice_service.validate_service(input_service)
    assert result == expected_result

# Test speech to text conversion
@pytest.mark.asyncio
async def test_whisper_speech_to_text_success(voice_service, sample_audio):
    voice_service.settings.STT_PROVIDER = "whisper"
    result = await voice_service.speech_to_text(sample_audio)
    assert result == "test transcription"
    voice_service.whisper_model.transcribe.assert_called_once()

@pytest.mark.asyncio
async def test_google_speech_to_text_success(voice_service, sample_audio):
    # Setup Google Cloud mock
    voice_service.settings.STT_PROVIDER = "google_cloud"
    voice_service.speech_client = Mock()
    mock_response = Mock()
    mock_response.results = [Mock(alternatives=[Mock(transcript="google transcription")])]
    voice_service.speech_client.recognize.return_value = mock_response

    result = await voice_service.speech_to_text(sample_audio)
    assert result == "google transcription"
    voice_service.speech_client.recognize.assert_called_once()

@pytest.mark.asyncio
async def test_speech_to_text_no_provider(voice_service, sample_audio):
    voice_service.settings.STT_PROVIDER = None
    with pytest.raises(ValueError, match="No speech-to-text service available"):
        await voice_service.speech_to_text(sample_audio)

# Test text to speech conversion
@pytest.mark.asyncio
async def test_gtts_text_to_speech_success(voice_service):
    voice_service.settings.TTS_PROVIDER = "gtts"
    mock_file = mock_open(read_data=b"fake audio")
    with patch("app.services.voice_service.gTTS") as mock_gtts, \
         patch("builtins.open", mock_file):
        mock_gtts.return_value = Mock()
        result = await voice_service.text_to_speech("test text")
        assert isinstance(result, bytes)
        mock_gtts.assert_called_once_with(text="test text", lang="en")

@pytest.mark.asyncio
async def test_google_text_to_speech_success(voice_service):
    voice_service.settings.TTS_PROVIDER = "google_cloud"
    voice_service.tts_client = Mock()
    mock_response = Mock(audio_content=b"fake audio")
    voice_service.tts_client.synthesize_speech.return_value = mock_response

    result = await voice_service.text_to_speech("test text")
    assert result == b"fake audio"
    voice_service.tts_client.synthesize_speech.assert_called_once()

@pytest.mark.asyncio
async def test_text_to_speech_invalid_provider(voice_service):
    voice_service.settings.TTS_PROVIDER = "invalid"
    with pytest.raises(ValueError, match="Unsupported TTS provider"):
        await voice_service.text_to_speech("test text")

# Test handle_invalid_service
@pytest.mark.asyncio
async def test_handle_invalid_service(voice_service):
    # Create a mock rasa_service module
    mock_rasa = AsyncMock()
    mock_rasa.send_custom_event = AsyncMock()
    
    # Patch the import of rasa_service at the module level
    with patch.dict('sys.modules', {'app.services.rasa_service': Mock(rasa_service=mock_rasa)}):
        result = await voice_service.handle_invalid_service("test_session", "invalid_service")
        
        assert "invalid_service" in result["text"]
        assert all(service in result["text"] for service in VALID_SERVICES.keys())
        assert result["intent"]["name"] == "invalid_service"
        mock_rasa.send_custom_event.assert_called_once()

# Test extract_service_from_rasa
def test_extract_service_from_rasa(voice_service):
    rasa_response = {
        "entities": [
            {"entity": "service", "value": "haircut"},
            {"entity": "date", "value": "tomorrow"}
        ]
    }
    result = voice_service.extract_service_from_rasa(rasa_response)
    assert result == "haircut"

def test_extract_service_from_rasa_no_service(voice_service):
    rasa_response = {
        "entities": [
            {"entity": "date", "value": "tomorrow"}
        ]
    }
    result = voice_service.extract_service_from_rasa(rasa_response)
    assert result is None

# Test process_voice_command
@pytest.mark.asyncio
async def test_process_voice_command_success(voice_service):
    # Set up STT provider and mock
    voice_service.settings.STT_PROVIDER = "whisper"
    voice_service.whisper_model.transcribe.return_value = {"text": "book appointment"}
    
    # Set up DialogFlow mock response
    mock_response = Mock()
    mock_response.query_result.intent.display_name = "booking"
    mock_response.query_result.parameters = []
    mock_response.query_result.intent_detection_confidence = 0.9
    mock_response.query_result.fulfillment_text = "Booking confirmed"
    voice_service.dialogflow_client.detect_intent = AsyncMock(return_value=mock_response)
    
    # Mock session path
    voice_service.dialogflow_client.session_path = Mock(return_value="test/session/path")

    # Mock the TextInput and QueryInput creation
    with patch('google.cloud.dialogflowcx_v3.types.TextInput') as mock_text_input, \
         patch('google.cloud.dialogflowcx_v3.types.QueryInput') as mock_query_input:
        # Configure the mocks
        mock_text_input.return_value = Mock()
        mock_query_input.return_value = Mock()

        result = await voice_service.process_voice_command(b"fake audio", "test_session")
        
        # Verify the result
        assert result["intent"] == "booking"
        assert result["confidence"] == 0.9
        assert result["fulfillment_text"] == "Booking confirmed"

        # Verify TextInput was created correctly with both text and language_code
        mock_text_input.assert_called_once_with(
            text="book appointment",
            language_code="en"
        )

# Test handle_conversation
@pytest.mark.asyncio
async def test_handle_conversation_success(voice_service):
    # Mock process_voice_command
    voice_service.process_voice_command = AsyncMock(return_value={
        "intent": "booking",
        "fulfillment_text": "Booking confirmed",
        "confidence": 0.9,
        "entities": {}
    })
    
    # Mock generate_response
    voice_service.generate_response = AsyncMock(return_value=b"fake audio response")

    result = await voice_service.handle_conversation(b"fake audio", "test_session")
    
    assert "Booking confirmed" in result["text"]
    assert result["audio"] == b"fake audio response"
    assert "command_data" in result 