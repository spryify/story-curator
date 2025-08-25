"""
Audio file validation and format handling.
"""
from enum import Enum
import os
from typing import Dict, Optional, Tuple

import ffmpeg
from pydub import AudioSegment

class AudioFormat(Enum):
    """Supported audio formats and their properties."""
    MP3 = "mp3"
    M4A = "m4a"
    AAC = "aac"
    WAV = "wav"

    @classmethod
    def from_extension(cls, extension: str) -> Optional["AudioFormat"]:
        """Get format from file extension."""
        try:
            return cls(extension.lower().lstrip('.'))
        except ValueError:
            return None

    @classmethod
    def is_supported(cls, format_str: str) -> bool:
        """Check if the format is supported."""
        try:
            cls(format_str.lower())
            return True
        except ValueError:
            return False

class AudioFileValidator:
    """Validates and processes audio files."""
    
    # Maximum file size (2GB)
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024
    
    # Minimum duration in seconds
    MIN_DURATION = 0.1
    
    # Maximum duration in hours
    MAX_DURATION = 4
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, any]:
        """
        Get audio file information using ffmpeg.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dict containing file information:
            - format: The audio format
            - duration: Duration in seconds
            - sample_rate: Sample rate in Hz
            - channels: Number of audio channels
            - bit_rate: Bit rate in bits/s
            
        Raises:
            ValueError: If file cannot be read or is invalid
        """
        try:
            probe = ffmpeg.probe(file_path)
            audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
            
            return {
                'format': probe['format']['format_name'],
                'duration': float(probe['format'].get('duration', 0)),
                'sample_rate': int(audio_info.get('sample_rate', 0)),
                'channels': int(audio_info.get('channels', 0)),
                'bit_rate': int(audio_info.get('bit_rate', 0))
            }
        except ffmpeg.Error as e:
            raise ValueError(f"Failed to read audio file: {e.stderr.decode()}")
        except (KeyError, StopIteration):
            raise ValueError("Invalid audio file format")

    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Check file existence
        if not os.path.exists(file_path):
            return False, "File does not exist"
            
        # Check file size
        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {self.MAX_FILE_SIZE // (1024*1024)}MB"
            
        # Get file extension
        _, ext = os.path.splitext(file_path)
        if not ext:
            return False, "File has no extension"
            
        # Check format support
        audio_format = AudioFormat.from_extension(ext)
        if not audio_format:
            return False, f"Unsupported audio format: {ext}"
        
        try:
            # Get file information
            info = self.get_file_info(file_path)
            
            # Validate duration
            duration = info['duration']
            if duration < self.MIN_DURATION:
                return False, f"Audio file too short (minimum {self.MIN_DURATION}s)"
            if duration > self.MAX_DURATION * 3600:
                return False, f"Audio file too long (maximum {self.MAX_DURATION} hours)"
                
            # Validate sample rate and channels
            if info['sample_rate'] <= 0:
                return False, "Invalid sample rate"
            if info['channels'] <= 0:
                return False, "Invalid channel count"
                
            return True, None
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """
        Convert audio file to WAV format for processing.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output WAV file
            
        Returns:
            bool: True if conversion successful
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            # Use ffmpeg for conversion
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path,
                                acodec='pcm_s16le',  # 16-bit PCM
                                ar=16000,            # 16kHz sample rate
                                ac=1)                # mono
            
            # Run conversion
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            return True
            
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise ValueError(f"Audio conversion failed: {error_message}")
