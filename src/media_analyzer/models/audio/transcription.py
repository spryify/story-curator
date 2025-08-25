"""Audio transcription models."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AudioInput:
    """Represents an audio input file with metadata."""
    file_path: str
    format: str
    duration: float
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


@dataclass
class TranscriptionResult:
    """Result of audio transcription and processing.
    
    This is the canonical transcription result model used throughout the application.
    It combines functionality from the previous separate implementations and adds
    proper typing and documentation.
    """
    text: str
    language: str
    segments: List[Dict]
    confidence: float
    metadata: Dict
    summary: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation."""
        return f"TranscriptionResult(text='{self.text[:50]}...', language={self.language}, confidence={self.confidence:.2f})"
