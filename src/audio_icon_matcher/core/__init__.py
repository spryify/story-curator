"""Core package for audio icon matcher."""

from .exceptions import (
    AudioIconError,
    AudioIconValidationError,
    AudioIconProcessingError,
    IconMatchingError,
    SubjectIdentificationError
)

__all__ = [
    "AudioIconError",
    "AudioIconValidationError", 
    "AudioIconProcessingError",
    "IconMatchingError",
    "SubjectIdentificationError"
]
