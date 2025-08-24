"""
Core module containing the main analyzer interface and configuration management.
"""

from pathlib import Path
from typing import Dict, Optional, Union
import time

from media_analyzer.core.exceptions import ValidationError
from media_analyzer.processors.text.processor import TextProcessor
from media_analyzer.processors.audio.processor import AudioProcessor
from media_analyzer.models.data_models import TranscriptionResult


class Analyzer:
    """Main interface for media analysis operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize analyzer with optional configuration."""
        self.config = config or {}
        self.audio_processor = AudioProcessor(self.config.get("audio", {}))
        self.text_processor = TextProcessor(self.config.get("text", {}))

    def _validate_file_path(self, file_path: Union[str, Path]) -> Path:
        """Validate file path for security."""
        path = Path(file_path)
        abs_path = path.resolve()

        # Check for path traversal attempts
        if ".." in str(path):
            raise ValidationError("Invalid file path - path traversal not allowed")

        # Convert paths to strings for comparison
        abs_str = str(abs_path)
        
        # Allow current directory, /tmp, /var/folders (macOS), and pytest temp dirs
        allowed = [
            str(Path.cwd()),  # Current directory
            "/tmp",           # Linux/Unix temp
            "/var/folders",   # macOS temp
            "/private/var/folders"  # macOS private temp
        ]

        # Check if path is in allowed directories
        if not any(abs_str.startswith(prefix) for prefix in allowed):
            raise ValidationError("Invalid file path - access outside allowed directories")

        return abs_path

    def _validate_options(self, options: Dict) -> None:
        """Validate processing options."""
        # Validate language
        if "language" in options:
            allowed_languages = {"en", "es", "fr", "de", "it", "pt", "nl", "pl", "tr", "ru", "ar", "hi", "zh", "ja", "ko"}
            if options["language"] not in allowed_languages:
                raise ValidationError(f"Invalid language: {options['language']}")
        
        # Validate summary length
        if "max_summary_length" in options:
            max_length = options["max_summary_length"]
            if not isinstance(max_length, int) or max_length < 1 or max_length > 10000:
                raise ValidationError("Invalid summary length - must be between 1 and 10000 characters")

    def process_file(self, file_path: Union[str, Path], options: Optional[Dict] = None) -> TranscriptionResult:
        """
        Process an audio file and return transcription with summary.
        
        Args:
            file_path: Path to the audio file
            options: Optional parameters for recognition
            
        Returns:
            TranscriptionResult object containing transcription and summary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
            ValidationError: If options are invalid
        """
        options = options or {}
        
        # Validate inputs
        self._validate_options(options)
        path = self._validate_file_path(file_path)
        
        # Validate format first to get the appropriate error
        try:
            self.audio_processor.validate_file(path)
        except ValueError:
            raise ValueError(f"Unsupported audio format: {path.suffix}")
        
        # Now check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        
        start_time = time.time()
        
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
