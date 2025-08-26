"""Audio test fixtures.

This module provides pytest fixtures for audio testing that can be shared
across the entire test suite. These fixtures integrate with pytest's tmp_path
fixture and use the audio utilities to generate test files.
"""

import pytest
from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment

from utils.audio import create_speech_audio, create_wav_file, export_audio

@pytest.fixture
def audio_samples_dir() -> Path:
    """Return the path to the audio samples directory.
    
    This directory contains pre-recorded audio samples used in tests.
    """
    return Path(__file__).parent.parent.parent / "data" / "audio"


@pytest.fixture
def speech_options() -> Dict[str, Any]:
    """Return default options for speech generation."""
    return {
        "voice": "Samantha",
        "rate": 200,
        "sample_rate": 16000,
        "channels": 1
    }


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
    
    return create_wav_file(
        text=text,
        output_path=file_path,
        voice=speech_options["voice"],
        rate=speech_options["rate"],
        sample_rate=speech_options["sample_rate"],
        channels=speech_options["channels"]
    )


@pytest.fixture
def sample_speech(speech_options):
    """Create a base speech audio segment for format testing.
    
    Args:
        speech_options: Speech generation options
        
    Returns:
        AudioSegment: Audio segment containing speech
    """
    text = "This is a test audio file for format conversion testing."
    return create_speech_audio(
        text=text,
        voice=speech_options["voice"],
        rate=speech_options["rate"],
        sample_rate=speech_options["sample_rate"],
        channels=speech_options["channels"]
    )


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
    export_audio(sample_speech, file_path, format="mp3")
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
    export_audio(sample_speech, file_path, format="ipod")  # ipod = AAC in M4A container
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
    export_audio(sample_speech, file_path, format="adts")  # adts = raw AAC
    yield file_path
    # Cleanup
    if file_path.exists():
        file_path.unlink()
