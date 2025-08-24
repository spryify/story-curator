"""Audio processing module for handling audio file operations."""

from pathlib import Path
from typing import Optional, Dict, Union

import speech_recognition as sr
from pydub import AudioSegment
from media_analyzer.core.exceptions import AudioProcessingError, ValidationError


class AudioProcessor:
    """Handles audio file processing and speech recognition."""

    SUPPORTED_FORMATS = {"wav", "mp3"}

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the audio processor with optional configuration."""
        self.config = config or {}
        self.recognizer = sr.Recognizer()

    def validate_file(self, file_path: Union[str, Path]) -> Path:
        """
        Validate that the file exists and has a supported format.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Path object of the validated file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
            
        if path.suffix[1:].lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {path.suffix}")
            
        return path

    def load_audio(self, file_path: Path) -> AudioSegment:
        """
        Load an audio file into memory.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioSegment object containing the audio data
            
        Raises:
            AudioProcessingError: If the file cannot be loaded
        """
        try:
            return AudioSegment.from_file(str(file_path))
        except Exception as e:
            raise AudioProcessingError(f"Failed to load audio file: {e}")

    def extract_text(self, audio_data: AudioSegment, options: Optional[Dict] = None) -> Dict:
        """
        Extract text from audio data using speech recognition.
        
        Args:
            audio_data: AudioSegment containing the audio
            options: Optional parameters for recognition
            
        Returns:
            Dictionary containing:
                - text: The transcribed text
                - confidence: Confidence score (0-1)
                - metadata: Additional recognition metadata
                
        Raises:
            AudioProcessingError: If text extraction fails
        """
        options = options or {}
        
        try:
            # Export to WAV for speech recognition
            audio_data.export("temp.wav", format="wav")
            
            with sr.AudioFile("temp.wav") as source:
                audio = self.recognizer.record(source)
                
                # Use Whisper by default
                result = self.recognizer.recognize_whisper(
                    audio,
                    language=options.get("language", "en"),
                    show_dict=True
                )
                
                return {
                    "text": result["text"],
                    "confidence": result.get("confidence", 0.0),
                    "metadata": {
                        "duration": len(audio_data) / 1000.0,  # Convert to seconds
                        "language": result.get("language", "en"),
                        "segments": result.get("segments", [])
                    }
                }
                
        except Exception as e:
            raise AudioProcessingError(f"Failed to extract text: {e}")
        finally:
            # Clean up temporary file
            Path("temp.wav").unlink(missing_ok=True)
