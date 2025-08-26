"""Audio test configuration and fixtures."""

import os
import pytest
from pathlib import Path
import tempfile
import subprocess
from pydub import AudioSegment


@pytest.fixture
def test_audio_file(speech_options, tmp_path):
    """Create a temporary audio file for testing."""
    test_text = "This is a test audio file"
    audio = generate_speech_audio(test_text, **speech_options)
    test_file = tmp_path / "test_audio.wav"
    audio.export(test_file, format="wav")
    return test_file


@pytest.fixture
def speech_options():
    """Return default options for speech generation."""
    return {
        "voice": "Samantha",
        "rate": 200,
        "sample_rate": 16000,
        "channels": 1
    }


def generate_speech_audio(text, **kwargs):
    """Generate speech audio using macOS say command.
    
    Args:
        text: Text to convert to speech
        **kwargs: Additional options (voice, rate, sample_rate, channels)
    
    Returns:
        AudioSegment: Generated audio
    """
    with tempfile.NamedTemporaryFile(suffix=".aiff") as temp_aiff:
        # Generate speech
        subprocess.run([
            "say",
            "-r", str(kwargs.get("rate", 200)),
            "-v", kwargs.get("voice", "Samantha"),
            "-o", temp_aiff.name,
            text
        ], check=True)
        
        # Load and convert
        audio = AudioSegment.from_file(temp_aiff.name, format="aiff")
        return audio.set_frame_rate(kwargs.get("sample_rate", 16000)) \
                   .set_channels(kwargs.get("channels", 1))


@pytest.fixture
def sample_wav(tmp_path, speech_options):
    """Create a sample WAV file with speech for testing.
    
    Args:
        tmp_path: Temporary directory from pytest
        speech_options: Speech generation options
        
    Returns:
        Path: Path to generated WAV file
    """
    text = "This is a test audio file for speech recognition."
    file_path = tmp_path / "test.wav"
    
    audio = generate_speech_audio(text, **speech_options)
    audio.export(str(file_path), format="wav")
    return file_path


@pytest.fixture
def sample_speech(speech_options):
    """Create a base speech audio file that other fixtures will convert.
    
    Args:
        speech_options: Speech generation options
        
    Returns:
        AudioSegment: Audio segment containing speech
    """
    text = "This is a test audio file for format conversion testing."
    return generate_speech_audio(text, **speech_options)


@pytest.fixture
def sample_mp3(tmp_path, sample_speech):
    """Create a sample MP3 file for testing.
    
    Args:
        tmp_path: Temporary directory from pytest
        sample_speech: Base speech audio segment
        
    Returns:
        Path: Path to generated MP3 file
    """
    file_path = tmp_path / "test.mp3"
    sample_speech.export(str(file_path), format="mp3")
    yield file_path
    # Cleanup
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def sample_m4a(tmp_path, sample_speech):
    """Create a sample M4A file for testing.
    
    Args:
        tmp_path: Temporary directory from pytest
        sample_speech: Base speech audio segment
        
    Returns:
        Path: Path to generated M4A file
    """
    file_path = tmp_path / "test.m4a"
    sample_speech.export(str(file_path), format="ipod")  # ipod = AAC in M4A container
    yield file_path
    # Cleanup
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def sample_aac(tmp_path, sample_speech):
    """Create a sample AAC file for testing.
    
    Args:
        tmp_path: Temporary directory from pytest
        sample_speech: Base speech audio segment
        
    Returns:
        Path: Path to generated AAC file
    """
    file_path = tmp_path / "test.aac"
    sample_speech.export(str(file_path), format="adts")  # adts = raw AAC
    yield file_path
    # Cleanup
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def story_speech_options():
    """Return speech options optimized for children's stories."""
    return {
        "voice": "Samantha",  # Clear, friendly voice
        "rate": 170,  # Slightly slower for clarity
        "sample_rate": 16000,
        "channels": 1
    }


@pytest.fixture
def sample_story_wav(tmp_path, story_speech_options):
    """Create a sample children's story WAV file for testing.
    
    Creates an audio file with a short children's story snippet that includes:
    - Character dialog
    - Narrative elements
    - Simple story structure
    
    Args:
        tmp_path: Temporary directory from pytest
        story_speech_options: Speech generation options
        
    Returns:
        Path: Path to generated WAV file
    """
    story_text = (
        "Once upon a time, there was a little rabbit named Hoppy. "
        "'I love to hop and play!' said Hoppy. "
        "One day, Hoppy met a wise old owl in the forest. "
        "'Be careful where you hop,' warned the owl. "
        "Hoppy smiled and thanked the owl for the good advice."
    )
    
    file_path = tmp_path / "story_test.wav"
    audio = generate_speech_audio(story_text, **story_speech_options)
    audio.export(str(file_path), format="wav")
    return file_path
