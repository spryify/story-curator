"""Audio Icon Matcher - Audio-to-Icon Pipeline Component.

This component implements FR-005: Audio-to-Icon Pipeline by providing
a complete pipeline that converts audio files into relevant icon suggestions.

The pipeline consists of:
1. Audio processing and transcription (using Whisper)
2. Subject identification from transcribed text
3. Icon matching from database
4. Result ranking and filtering

Example usage:
    from audio_icon_matcher import AudioIconPipeline
    
    pipeline = AudioIconPipeline()
    result = pipeline.process("audio.wav", max_icons=10)
    
    for match in result.icon_matches:
        print(f"{match.icon.name}: {match.confidence:.2f}")
"""

from .core.pipeline import AudioIconPipeline
from .models.results import AudioIconResult, IconMatch
from .core.exceptions import AudioIconError, AudioIconValidationError

__version__ = "1.0.0"
__all__ = [
    "AudioIconPipeline",
    "AudioIconResult", 
    "IconMatch",
    "AudioIconError",
    "AudioIconValidationError"
]
