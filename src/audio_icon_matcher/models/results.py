"""Result models for audio icon matching."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# Import icon model from existing component
from icon_extractor.models.icon import IconData


@dataclass
class IconMatch:
    """Represents a matched icon with confidence score."""
    icon: IconData
    confidence: float
    match_reason: str
    subjects_matched: List[str]


@dataclass
class AudioIconResult:
    """Result of audio-to-icon pipeline processing."""
    success: bool
    transcription: str
    transcription_confidence: float
    subjects: Dict[str, Any]
    icon_matches: List[IconMatch]
    processing_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
