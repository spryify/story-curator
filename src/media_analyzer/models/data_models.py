"""Data models for the media analyzer."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class AudioInput:
    """Represents an audio input file with metadata."""
    
    file_path: str
    format: str
    duration: float


@dataclass
class TranscriptionResult:
    """Contains the results of audio transcription and analysis."""
    
    full_text: str
    summary: str
    confidence: float
    metadata: Dict


@dataclass
class ProcessingError:
    """Represents an error that occurred during processing."""
    
    error_code: str
    message: str
    details: Dict