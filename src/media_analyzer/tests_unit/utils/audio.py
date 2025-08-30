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


def create_timed_speech_file(
    path: Path,
    duration: int = 1000,
    text: Optional[str] = None,
    filename: str = "test.wav",
    voice: str = "Samantha",
    rate: int = 200,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Create a test audio file with specified duration using text-to-speech.
    
    Args:
        path: Directory to create the file in
        duration: Duration in milliseconds (approximate)
        text: Text to speak. If None, will generate test text based on duration
        filename: Name of the file to create
        voice: The voice to use (defaults to "Samantha")
        rate: Speaking rate (words per minute)
        sample_rate: Output sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        
    Returns:
        Path to the created audio file
        
    Example:
        >>> # Create a 2-second WAV file
        >>> file_path = create_timed_speech_file(tmp_path, duration=2000)
        >>> # Create an MP3 file with specific text and voice options
        >>> file_path = create_timed_speech_file(
        ...     tmp_path,
        ...     text="Hello world",
        ...     filename="test.mp3",
        ...     rate=180,
        ...     sample_rate=16000
        ... )
    """
    # If no text provided, generate text based on duration
    if text is None:
        # Use varied phrases to avoid confusing Whisper with repetitive content
        base_phrases = [
            "This is a test of the audio system",
            "The weather is beautiful today",  
            "Technology continues to advance rapidly",
            "Natural speech recognition works well",
            "We are testing different audio formats",
            "Quality audio processing is important",
            "Machine learning helps with transcription",
            "Digital audio files contain speech data"
        ]
        
        # Calculate timing - each phrase takes roughly 2-3 seconds at normal rate
        words_per_minute = rate  # Use the actual rate parameter
        words_per_second = words_per_minute / 60
        avg_words_per_phrase = 6  # Average words in our phrases
        seconds_per_phrase = avg_words_per_phrase / words_per_second
        num_phrases = max(1, round((duration / 1000.0) / seconds_per_phrase))
        
        # Cycle through different phrases to create varied content
        phrases = [base_phrases[i % len(base_phrases)] for i in range(num_phrases)]
        text = ". ".join(phrases) + "."  # Add periods for natural pauses

    # Generate the audio segment
    audio = create_speech_audio(text, voice=voice, rate=rate, sample_rate=sample_rate, channels=channels)
    
    # Export to desired format
    file_path = path / filename
    audio.export(str(file_path), format=filename.split('.')[-1])
    
    return file_path
