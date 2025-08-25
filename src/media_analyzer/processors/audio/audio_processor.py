"""Audio processing module for handling audio file operations."""

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Dict, Union, Any

import whisper
from pydub import AudioSegment

from media_analyzer.core.exceptions import AudioProcessingError, ValidationError
from media_analyzer.core.validator import AudioFileValidator
from media_analyzer.core.models import TranscriptionResult

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio file processing and speech recognition."""

    SUPPORTED_FORMATS = {"wav", "mp3", "m4a", "aac"}

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the audio processor with optional configuration."""
        self.config = config or {}
        self._model = None
        self.validator = AudioFileValidator()

    @property
    def model(self):
        """Lazy load the whisper model."""
        if self._model is None and not self.config.get("mock_model"):
            try:
                self._model = whisper.load_model("base")
            except Exception as e:
                raise AudioProcessingError(f"Failed to load Whisper model: {str(e)}")
        return self._model

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

        suffix = path.suffix[1:].lower() if path.suffix else ""
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {path.suffix}")

        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

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

    def extract_text(self, audio_file: Union[Path, AudioSegment], options: Optional[Dict[str, Any]] = None) -> TranscriptionResult:
        """Extract text from audio file using Whisper.

        Args:
            audio_file: Path to audio file or AudioSegment to transcribe
            options: Optional configuration for transcription:
                language: Language code
                word_timestamps: Whether to include word timestamps
                task: Transcription task ('transcribe' or 'translate')

        Returns:
            A dictionary containing the transcribed text and metadata:
                text: The transcribed text
                language: Detected language code
                segments: List of transcription segments with timestamps

        Raises:
            AudioProcessingError: If transcription fails or returns invalid format
            ValueError: If invalid options are provided
        """
        try:
            model = whisper.load_model("base.en")  # Use English model for better accuracy
            # Initialize with English-specific options
            transcribe_kwargs = {
                "language": "en",  # Force English language
                "task": "transcribe",  # Force transcription task
                "fp16": False  # Force FP32 since FP16 isn't supported on CPU
            }

            # Update with provided options
            if options:
                # Convert option values to proper types
                if "language" in options:
                    transcribe_kwargs["language"] = str(options["language"])
                if "word_timestamps" in options:
                    transcribe_kwargs["word_timestamps"] = bool(options["word_timestamps"])
                if "task" in options:
                    transcribe_kwargs["task"] = str(options["task"])

            # Convert to a temporary WAV file
            with NamedTemporaryFile(suffix=".wav") as temp_file:
                print("Preprocessing audio...")
                # Preprocess audio to match whisper's requirements (16000 Hz, mono)
                # Ensure we have an AudioSegment
                audio: AudioSegment = audio_file if isinstance(audio_file, AudioSegment) else AudioSegment.from_file(str(audio_file))
                print(f"Input audio: {len(audio)/1000}s, {audio.frame_rate}Hz, {audio.channels} channel(s)")
                audio = audio.set_frame_rate(16000).set_channels(1)
                print(f"Processed audio: {len(audio)/1000}s, {audio.frame_rate}Hz, {audio.channels} channel(s)")
                audio.export(temp_file.name, format="wav")

                print(f"Transcribing audio with {transcribe_kwargs}...")
                result = model.transcribe(temp_file.name, **transcribe_kwargs)

            # Handle different return types from whisper
            text = result.get("text", "")
            if isinstance(text, list):
                text = " ".join(str(t) for t in text)
            elif not isinstance(text, str):
                raise AudioProcessingError("Failed to extract text: Transcription returned invalid format")

            # Calculate overall confidence from segment log probabilities
            # Get and type check segments
            segments = result.get("segments", [])
            if not isinstance(segments, list):
                segments = []

            # Calculate confidence from segments
            confidence = 0.0
            try:
                valid_segments = []
                for segment in segments:
                    if isinstance(segment, dict) and 'avg_logprob' in segment:
                        try:
                            logprob = float(segment['avg_logprob'])
                            valid_segments.append(logprob)
                        except (TypeError, ValueError):
                            continue

                if valid_segments:
                    avg_logprob = sum(valid_segments) / len(valid_segments)
                    confidence = min(1.0, max(0.0, 1 + avg_logprob))
            except Exception as e:
                print(f"Warning: Failed to calculate confidence: {e}")

            # Prepare metadata
            metadata = {
                "language": result.get("language", "en"),
                "model": "base.en",
                "task": transcribe_kwargs.get("task", "transcribe"),
                "duration": len(audio) / 1000.0  # Convert from ms to seconds
            }

            # Create TranscriptionResult object
            transcription = TranscriptionResult(
                text=text,
                language=metadata["language"],
                segments=segments,
                confidence=confidence,
                metadata=metadata
            )
            print(f"Response: {transcription}")
            return transcription

        except ValueError as e:
            print(f"ValueError: {e}")
            raise ValueError(str(e)) from e
        except Exception as e:
            print(f"Error during transcription: {e}")
            raise AudioProcessingError(f"Failed to extract text: {str(e)}") from e

    def get_audio_info(self, audio_data: AudioSegment) -> Dict:
        """
        Get audio file metadata.

        Args:
            audio_data: AudioSegment containing the audio

        Returns:
            Dictionary containing audio metadata
        """
        return {
            "sample_rate": audio_data.frame_rate,
            "channels": audio_data.channels,
            "duration": len(audio_data) / 1000.0  # Convert to seconds
        }
