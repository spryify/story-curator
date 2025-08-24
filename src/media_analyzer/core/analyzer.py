"""
Core module containing the main analyzer interface and configuration management.
"""

from pathlib import Path
from typing import Dict, Optional, Union

from media_analyzer.models.data_models import AudioInput, TranscriptionResult
from media_analyzer.processors.audio.processor import AudioProcessor
from media_analyzer.processors.text.processor import TextProcessor


class Analyzer:
    """Main interface for media analysis operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with optional configuration."""
        self.config = config or {}
        self.audio_processor = AudioProcessor(self.config)
        self.text_processor = TextProcessor(self.config)

    def process_file(self, file_path: Union[str, Path], options: Optional[Dict] = None) -> TranscriptionResult:
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
            AudioProcessingError: If audio processing fails
            SummarizationError: If text summarization fails
        """
        options = options or {}
        
        # Validate and load audio file
        path = self.audio_processor.validate_file(file_path)
        audio_data = self.audio_processor.load_audio(path)
        
        # Extract text from audio
        extraction_result = self.audio_processor.extract_text(audio_data, options)
        
        # Generate summary
        summary = self.text_processor.summarize(
            extraction_result["text"],
            max_length=options.get("max_summary_length")
        )
        
        # Create result object
        return TranscriptionResult(
            full_text=extraction_result["text"],
            summary=summary,
            confidence=extraction_result["confidence"],
            metadata=extraction_result["metadata"]
        )
