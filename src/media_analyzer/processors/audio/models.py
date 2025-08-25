"""Models for audio processing."""

from typing import Dict, List, Optional


class TranscriptionResult:
    """Result from audio transcription."""

    def __init__(self, text: str, language: str, segments: List[Dict], 
                 confidence: float, metadata: Dict):
        """Initialize transcription result.

        Args:
            text: Transcribed text
            language: Detected language code
            segments: List of segments with timestamps and text
            confidence: Confidence score between 0 and 1
            metadata: Additional metadata about transcription
        """
        self.text = text
        self.language = language
        self.segments = segments
        self.confidence = confidence
        self.metadata = metadata

    def __str__(self) -> str:
        """Return string representation."""
        return f"TranscriptionResult(text='{self.text[:50]}...', language={self.language}, confidence={self.confidence:.2f})"
