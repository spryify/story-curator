"""Unit tests for the audio processor module.

This module contains unit tests for the AudioProcessor class, which handles core
audio processing functionality including loading, validation, and text extraction.

Test Categories:
1. Initialization
   - Default initialization
   - Configuration handling

2. Audio File Handling
   - Format validation
   - File loading
   - Metadata extraction

3. Text Extraction
   - Basic text extraction
   - Language support
   - Confidence scoring

4. Error Handling
   - Invalid formats
   - Loading failures
   - Processing errors
   - Language validation

5. Audio Information
   - Sample rate validation
   - Channel information
   - Duration calculation

Dependencies:
- pydub: For audio file handling
- whisper: For speech recognition
- conftest.py: Provides test fixtures

Usage:
    pytest tests/unit/processors/audio/test_audio_processor.py
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
from unittest.mock import Mock, patch

from media_analyzer.processors.audio.audio_processor import AudioProcessor
from media_analyzer.core.exceptions import AudioProcessingError
from media_analyzer.models.audio import TranscriptionResult


def test_audio_processor_initialization():
    """Test that audio processor can be initialized with default config."""
    processor = AudioProcessor()
    assert processor.config == {}


def test_audio_processor_initialization_with_config(test_config):
    """Test that audio processor can be initialized with custom config."""
    processor = AudioProcessor(test_config.get("audio", {}))
    assert processor.config == test_config.get("audio", {})


def test_validate_file_format(test_audio_file):
    """Test audio format validation."""
    processor = AudioProcessor()
    
    # Test valid formats
    processor.validate_file(test_audio_file)  # Should not raise
    
    # Test invalid format
    with pytest.raises(ValueError) as exc_info:
        processor.validate_file(Path("invalid.txt"))
    assert "Unsupported audio format" in str(exc_info.value)


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


def test_extract_text(test_audio_file):
    """Test text extraction from audio."""
    processor = AudioProcessor()
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


def test_error_handling(test_audio_file):
    """Test error handling in audio processing."""
    processor = AudioProcessor()

    # Create a processor with mock model config
    processor = AudioProcessor(config={"mock_model": True})
    
    # Set up mock model with empty text response
    mock_model = Mock()
    mock_model.transcribe.return_value = {"text": "", "segments": []}
    processor._model = mock_model
    
    # Create a test audio file
    audio = AudioSegment.silent(duration=100)
    
    # Test error handling for empty transcription
    with pytest.raises(AudioProcessingError) as exc_info:
        processor.extract_text(audio)
        
    # Check that error is due to empty transcription
    assert "No transcription returned" in str(exc_info.value)# Test with invalid options
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


def test_story_text_extraction(sample_story_wav):
    """Test text extraction from children's story audio.
    
    Tests that the processor can accurately handle:
    - Story narrative structure
    - Character dialogue
    - Story-specific vocabulary
    """
    processor = AudioProcessor()
    audio_data = processor.load_audio(sample_story_wav)
    
    result = processor.extract_text(audio_data)
    
    # Verify basic transcription
    assert isinstance(result.text, str)
    assert len(result.text) > 0
    
    # Check for key story elements in the text
    text = result.text.lower()
    assert "once upon a time" in text, "Story opening not detected"
    assert "hoppy" in text, "Main character name not detected"
    assert "owl" in text, "Supporting character not detected"
    
    # Check segments for dialogue structure
    segments = result.segments
    assert len(segments) > 0, "No segments detected"
    
    # Look for dialogue markers in segments
    dialogue_found = False
    for segment in segments:
        if any(marker in segment["text"].lower() 
               for marker in ["'", "said", "warned"]):
            dialogue_found = True
            break
    assert dialogue_found, "No dialogue detected in segments"


def test_story_audio_quality(sample_story_wav, story_speech_options):
    """Test audio quality checks for children's story content.
    
    Verifies that the audio meets quality requirements for:
    - Sample rate appropriate for clear speech
    - Channel configuration
    - Speech rate appropriate for children's content
    """
    processor = AudioProcessor()
    audio_data = processor.load_audio(sample_story_wav)
    info = processor.get_audio_info(audio_data)
    
    # Verify audio properties match story requirements
    assert info["sample_rate"] == story_speech_options["sample_rate"], \
        "Incorrect sample rate for story audio"
    assert info["channels"] == story_speech_options["channels"], \
        "Incorrect channel count for story audio"
    
    # Check duration is appropriate for the story content
    assert 5.0 <= info["duration"] <= 30.0, \
        f"Story duration {info['duration']}s outside expected range"
    
    # Process audio and check segment lengths
    result = processor.extract_text(audio_data)
    
    # Calculate average segment duration
    segment_durations = [
        seg["end"] - seg["start"] 
        for seg in result.segments
    ]
    avg_duration = sum(segment_durations) / len(segment_durations)
    
    # Story segments should be appropriate length for children's comprehension
    assert 1.0 <= avg_duration <= 5.0, \
        f"Average segment duration {avg_duration}s not suitable for children's content"
