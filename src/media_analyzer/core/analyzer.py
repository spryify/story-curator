"""
Core module containing the main analyzer interface and configuration management.
"""

import time
from pathlib import Path
from typing import Dict, Optional, Union

from media_analyzer.core.exceptions import ValidationError
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

    def _validate_options(self, options: Dict) -> None:
        """Validate processing options for security and correctness."""
        if "language" in options and options["language"] not in ["en", "es", "fr", "de", "it"]:
            raise ValidationError("Invalid language specified")
            
        if "max_summary_length" in options:
            length = options["max_summary_length"]
            if not isinstance(length, int) or length <= 0 or length > 100000:
                raise ValidationError("Invalid summary length - must be between 1 and 100000")

    def _validate_file_path(self, file_path: Union[str, Path]) -> Path:
        """Validate file path for security."""
        try:
            path = Path(file_path).resolve()
            if ".." in str(path) or not path.is_file():
                raise ValidationError("Invalid file path")
            return path
        except Exception as e:
            raise ValidationError(f"Invalid file path: {str(e)}")

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
            ValidationError: If options are invalid
        """
        options = options or {}
        start_time = time.time()
        
        # Validate inputs
        self._validate_options(options)
        path = self._validate_file_path(file_path)
        
        # Process audio file
        audio_data = self.audio_processor.load_audio(path)
        audio_info = self.audio_processor.get_audio_info(audio_data)
        
        # Extract text from audio
        extraction_result = self.audio_processor.extract_text(audio_data, options)
        
        # Generate summary
        summary = self.text_processor.summarize(
            extraction_result["text"],
            max_length=options.get("max_summary_length", 1000)
        )
        
        # Add performance metrics
        metadata = extraction_result.get("metadata", {})
        metadata.update({
            "processing_time": time.time() - start_time,
            "sample_rate": audio_info["sample_rate"],
            "channels": audio_info["channels"],
            "duration": audio_info["duration"],
            "language": options.get("language", "en")
        })
        
        # Create result object
        return TranscriptionResult(
            full_text=extraction_result["text"],
            summary=summary,
            confidence=extraction_result.get("confidence", 0.0),
            metadata=metadata
        )
