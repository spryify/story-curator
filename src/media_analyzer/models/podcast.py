"""Podcast episode data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from media_analyzer.models.subject.identification import Subject
from media_analyzer.models.audio.transcription import TranscriptionResult


@dataclass
class PodcastEpisode:
    """Represents a podcast episode with metadata."""
    platform: str
    episode_id: str
    url: str
    title: str
    description: str
    duration_seconds: Optional[int]
    publication_date: Optional[datetime]
    show_name: Optional[str]
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """Return string representation."""
        return f"PodcastEpisode('{self.title}' from {self.show_name}, {self.platform})"


@dataclass
class StreamingAnalysisResult:
    """Result of podcast episode analysis."""
    episode: PodcastEpisode
    transcription: TranscriptionResult
    subjects: List[Subject]
    matched_icons: List[Dict[str, Any]]  # Will be populated by icon matching
    processing_metadata: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation."""
        status = "successful" if self.success else "failed"
        return f"StreamingAnalysisResult({status}, {len(self.subjects)} subjects, {len(self.matched_icons)} icons)"


@dataclass
class AnalysisOptions:
    """Configuration options for podcast analysis."""
    language: str = "en"
    transcription_service: str = "whisper"  # "whisper", "assemblyai"
    subject_extraction: bool = True
    icon_matching: bool = True
    cache_results: bool = True
    max_duration_minutes: int = 180  # 3 hours
    segment_length_seconds: int = 300  # 5 minutes for chunked processing
    confidence_threshold: float = 0.5
    
    def __post_init__(self):
        """Validate options after initialization."""
        if self.max_duration_minutes <= 0:
            raise ValueError("max_duration_minutes must be positive")
        if self.segment_length_seconds <= 0:
            raise ValueError("segment_length_seconds must be positive")
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
