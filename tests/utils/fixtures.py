"""Audio fixtures for testing.

This module provides pytest fixtures for audio testing that can be reused across
different test modules. These fixtures use the audio utilities to generate
test audio files in various formats.
"""

import pytest
from pathlib import Path

from .audio import create_speech_audio, create_wav_file, export_audio


@pytest.fixture
def sample_wav(tmp_path):
    """Create a sample WAV file with speech for testing.
    
    Args:
        tmp_path: Temporary directory from pytest
        
    Returns:
        Path: Path to generated WAV file
    """
    text = "This is a test audio file for speech recognition."
    file_path = tmp_path / "test.wav"
    
    return create_wav_file(
        text=text,
        output_path=file_path,
        sample_rate=16000,
        channels=1
    )


@pytest.fixture
def sample_speech(tmp_path):
    """Create a base speech audio file that other fixtures will convert.
    
    Args:
        tmp_path: Temporary directory from pytest
        
    Returns:
        AudioSegment: Audio segment containing speech
    """
    text = "This is a test audio file for format conversion testing."
    return create_speech_audio(
        text=text,
        sample_rate=16000,
        channels=1
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
