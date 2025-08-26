"""Audio utilities for testing.

This module provides centralized utilities for creating test audio files using speech synthesis.
All tests that need sample audio files should use these utilities instead of implementing
their own audio generation logic.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


def create_speech_audio(
    text: str,
    voice: str = "Samantha",
    rate: int = 200,
    sample_rate: int = 16000,
    channels: int = 1,
) -> AudioSegment:
    """Create a speech audio segment using macOS 'say' command.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (defaults to "Samantha")
        rate: Speaking rate (words per minute)
        sample_rate: Output sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        
    Returns:
        AudioSegment: The generated audio segment
    """
    # Create temp file with a unique suffix to avoid conflicts in parallel tests
    import tempfile
    temp_fd, temp_aiff = tempfile.mkstemp(suffix=".aiff")
    os.close(temp_fd)
    
    try:
        # Generate speech with macOS say command
        subprocess.run(
            ["say", "-r", str(rate), "-v", voice, "-o", temp_aiff, text],
            check=True
        )
        
        # Load and convert to standard format
        audio = AudioSegment.from_file(temp_aiff, format="aiff")
        audio = audio.set_frame_rate(sample_rate).set_channels(channels)
        
        return audio
    finally:
        # Clean up temp file
        if os.path.exists(temp_aiff):
            os.unlink(temp_aiff)


def create_wav_file(
    text: str,
    output_path: Path,
    voice: str = "Samantha",
    rate: int = 200,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Create a WAV file with speech audio.
    
    Args:
        text: The text to convert to speech
        output_path: Where to save the WAV file
        voice: The voice to use (defaults to "Samantha")
        rate: Speaking rate (words per minute)
        sample_rate: Output sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        
    Returns:
        Path: Path to the generated WAV file
    """
    audio = create_speech_audio(
        text=text,
        voice=voice,
        rate=rate,
        sample_rate=sample_rate,
        channels=channels
    )
    
    # Export to WAV format
    audio.export(str(output_path), format="wav")
    return output_path


def export_audio(
    audio: AudioSegment,
    output_path: Path,
    format: str,
    **kwargs
) -> Path:
    """Export an audio segment to a file.
    
    Args:
        audio: The audio segment to export
        output_path: Where to save the file
        format: The format to export to (e.g. "wav", "mp3", "ipod", "adts")
        **kwargs: Additional arguments to pass to pydub.AudioSegment.export()
        
    Returns:
        Path: Path to the exported file
    """
    audio.export(str(output_path), format=format, **kwargs)
    return output_path
