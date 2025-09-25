"""Unit tests for the audio processor module."""

import pytest
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from unittest.mock import Mock, patch

from media_analyzer.processors.audio.audio_processor import AudioProcessor
from media_analyzer.core.exceptions import AudioProcessingError
from media_analyzer.models.audio import TranscriptionResult

# Skip tests that require 'say' command only in CI environments
skip_audio_tests = pytest.mark.skipif(
    os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true',
    reason="Requires macOS 'say' command for audio generation - skipped in CI environments"
)

@pytest.fixture
def test_config():
    """Return test configuration."""
    return {
        "audio": {
            "model": "base",
            "device": "cpu", 
            "sample_rate": 16000,
            "chunk_size": 30,
            "supported_formats": ["wav", "mp3"],
            "max_duration": 3600
        }
    }

def test_audio_processor_initialization():
    """Test that audio processor can be initialized with default config."""
    processor = AudioProcessor()
    assert processor.config == {}


def test_audio_processor_initialization_with_config(test_config):
    """Test that audio processor can be initialized with custom config."""
    processor = AudioProcessor(test_config.get("audio", {}))
    assert processor.config == test_config.get("audio", {})


@skip_audio_tests
def test_validate_file_format(test_audio_file):
    """Test audio format validation."""
    processor = AudioProcessor()
    
    # Test valid formats
    processor.validate_file(test_audio_file)  # Should not raise
    
    # Test invalid format
    with pytest.raises(ValueError) as exc_info:
        processor.validate_file(Path("invalid.txt"))
    assert "Unsupported audio format" in str(exc_info.value)


@skip_audio_tests
def test_load_audio(test_audio_file):
    """Test loading audio file."""
    processor = AudioProcessor()
    
    # Test successful load
    audio_data = processor.load_audio(test_audio_file)
    assert isinstance(audio_data, AudioSegment)
    assert len(audio_data) > 0
    
    # Test load failure
    with pytest.raises(AudioProcessingError):
        processor.load_audio(Path("nonexistent.wav"))


@skip_audio_tests
def test_get_audio_info(test_audio_file):
    """Test retrieving audio metadata."""
    processor = AudioProcessor()
    audio_data = processor.load_audio(test_audio_file)
    
    info = processor.get_audio_info(audio_data)
    assert isinstance(info, dict)
    assert "sample_rate" in info
    assert isinstance(info["sample_rate"], int)
    assert info["sample_rate"] > 0
    assert "channels" in info
    assert isinstance(info["channels"], int)
    assert info["channels"] > 0
    assert "duration" in info
    assert isinstance(info["duration"], float)
    assert info["duration"] > 0


@skip_audio_tests
def test_extract_text(test_audio_file, mock_whisper):
    """Test text extraction from audio with mocked Whisper model."""
    # Create processor with mock configuration
    processor = AudioProcessor(config={"mock_model": True})
    processor._model = mock_whisper
    
    audio_data = processor.load_audio(test_audio_file)
    
    # Test with default options
    result = processor.extract_text(audio_data)
    assert hasattr(result, 'text')
    assert isinstance(result.text, str)
    assert len(result.text) > 0
    assert hasattr(result, 'segments')
    assert isinstance(result.segments, list)
    for segment in result.segments:
        assert isinstance(segment, dict)
        assert "text" in segment
        assert "start" in segment
        assert "end" in segment
        assert isinstance(segment["text"], str)
        assert isinstance(segment["start"], (int, float))
        assert isinstance(segment["end"], (int, float))
        assert segment["end"] >= segment["start"]
    
    # Test with custom language
    result = processor.extract_text(audio_data, {"language": "en"})
    assert result.text
    assert hasattr(result, 'metadata')
    assert result.metadata.get("language") == "en"


@skip_audio_tests
def test_error_handling(test_audio_file, mock_whisper):
    """Test error handling in audio processing."""
    # Create a processor with mock model config
    processor = AudioProcessor(config={"mock_model": True})
    
    # Set up mock model with empty text response for error testing
    mock_whisper.transcribe.return_value = {"text": "", "segments": []}
    processor._model = mock_whisper
    
    # Create a test audio file
    audio = AudioSegment.silent(duration=100)
    
    # Test error handling for empty transcription
    with pytest.raises(AudioProcessingError) as exc_info:
        processor.extract_text(audio)
        
    # Check that error is due to empty transcription
    assert "No transcription returned" in str(exc_info.value)
    
    # Reset mock for next test
    mock_whisper.transcribe.return_value = {
        "text": "Valid transcription text",
        "segments": [{"text": "Valid transcription text", "start": 0.0, "end": 2.0}]
    }
    processor._model = mock_whisper
    
    # Test with invalid options
    with pytest.raises(ValueError) as exc_info:
        processor.extract_text(
            processor.load_audio(test_audio_file),
            {"language": "invalid"}
        )
    assert "Unsupported language" in str(exc_info.value)


def test_supported_formats():
    """Test that processor declares supported formats correctly."""
    processor = AudioProcessor()
    assert "wav" in processor.SUPPORTED_FORMATS
    assert "mp3" in processor.SUPPORTED_FORMATS
    for fmt in processor.SUPPORTED_FORMATS:
        assert isinstance(fmt, str)
        # Format may include numbers (e.g., mp3)
        assert all(c.isalnum() for c in fmt)
