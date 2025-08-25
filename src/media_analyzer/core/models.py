"""Common models used across the application."""
from typing import Dict, List, Optional


class TranscriptionResult:
    """Result of audio transcription and processing."""

    def __init__(self, text: str, language: str, segments: List[Dict], 
                 confidence: float, metadata: Dict, summary: Optional[str] = None):
        """Initialize transcription result.

        Args:
            text: The transcribed text
            language: The detected language code
            segments: List of segments with timestamps and text
            confidence: Confidence score between 0 and 1
            metadata: Additional metadata about transcription and processing
            summary: Optional summary of the transcribed text
        """
        self.text = text
        self.language = language
        self.segments = segments
        self.confidence = confidence
        self.metadata = metadata
        self.summary = summary

    def __str__(self) -> str:
        """Return string representation."""
        return f"TranscriptionResult(text='{self.text[:50]}...', language={self.language}, confidence={self.confidence:.2f})"
