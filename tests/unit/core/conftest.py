"""Core analyzer test fixtures."""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import os
import tempfile
import subprocess
from pydub import AudioSegment


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
            "max_duration": 3600  # 1 hour
        },
        "text": {
            "max_summary_length": 1000,
            "min_confidence": 0.8,
            "language": "en"
        }
    }


@pytest.fixture(autouse=True)
def mock_whisper():
    """Mock whisper.load_model for core analyzer tests."""
    with patch('whisper.load_model') as mock_load_model:
        # Create a mock model
        mock_model = Mock()
        
        # Mock transcription result with proper structure
        mock_result = {
            'text': 'Once upon a time there was a test audio file for format testing that demonstrates speech recognition capabilities.',
            'language': 'en',
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.0,
                    'text': 'This is a test audio file that demonstrates',
                    'avg_logprob': -0.2
                },
                {
                    'start': 3.0,
                    'end': 6.0,
                    'text': 'speech recognition capabilities.',
                    'avg_logprob': -0.3
                }
            ]
        }
        
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        yield mock_model


def generate_speech_audio(text, **kwargs):
    """Generate speech audio using macOS say command.
    
    Args:
        text: Text to convert to speech
        **kwargs: Additional options (voice, rate, sample_rate, channels)
    
    Returns:
        AudioSegment: Generated audio
    """
    # Default parameters
    voice = kwargs.get('voice', 'Samantha')
    rate = kwargs.get('rate', 200)
    
    with tempfile.NamedTemporaryFile(suffix='.aiff') as temp_aiff:
        # Generate speech with say command
        cmd = ['say', '-v', voice, '-r', str(rate), '-o', temp_aiff.name, text]
        subprocess.run(cmd, check=True)
        
        # Load generated audio with pydub
        audio = AudioSegment.from_file(temp_aiff.name)
        
        # Set target parameters
        sample_rate = kwargs.get('sample_rate', 16000)
        channels = kwargs.get('channels', 1)
        
        # Apply audio parameters if different from original
        if audio.frame_rate != sample_rate or audio.channels != channels:
            audio = audio.set_frame_rate(sample_rate).set_channels(channels)
            
        return audio

@pytest.fixture
def test_audio_file(tmp_path):
    """Create a temporary audio file with test content."""
    test_text = "This is a test audio file for speech recognition testing"
    audio = generate_speech_audio(test_text)
    test_file = tmp_path / "test_audio.wav"
    audio.export(test_file, format="wav")
    return test_file

@pytest.fixture
def test_formats(tmp_path):
    """Create sample audio files in different formats."""
    test_text = "This is a sample audio for format testing"
    audio = generate_speech_audio(test_text)
    
    files = {}
    for fmt in ["wav", "mp3"]:
        test_file = tmp_path / f"sample.{fmt}"
        audio.export(test_file, format=fmt)
        files[fmt] = test_file
    
    return files
