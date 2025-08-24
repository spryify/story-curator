"""
Core module containing the main analyzer interface and configuration management.
"""

from pathlib import Path
from typing import Dict, Optional

from media_analyzer.models.data_models import AudioInput, TranscriptionResult


class Analyzer:
    """Main interface for media analysis operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with optional configuration."""
        self.config = config or {}

    def process_file(self, file_path: str | Path, options: Optional[Dict] = None) -> TranscriptionResult:
        """
        Process an audio file and return transcription with summary.
        
        Args:
            file_path: Path to the audio file
            options: Optional processing parameters
            
        Returns:
            TranscriptionResult object containing transcription and summary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        # Implementation will be added following TDD approach
        raise NotImplementedError
