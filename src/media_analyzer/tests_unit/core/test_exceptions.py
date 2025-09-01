"""Unit tests for exceptions module."""

import pytest

from media_analyzer.core.exceptions import (
    MediaAnalyzerError,
    AudioProcessingError,
    ValidationError,
    TranscriptionError
)


class TestMediaAnalyzerError:
    """Test MediaAnalyzerError base exception."""
    
    def test_media_analyzer_error_creation(self):
        """Test creating MediaAnalyzerError with message."""
        error = MediaAnalyzerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_media_analyzer_error_inheritance(self):
        """Test MediaAnalyzerError inheritance."""
        error = MediaAnalyzerError()
        assert isinstance(error, Exception)
        assert issubclass(MediaAnalyzerError, Exception)


class TestAudioProcessingError:
    """Test AudioProcessingError exception."""
    
    def test_audio_processing_error_creation(self):
        """Test creating AudioProcessingError with message."""
        error = AudioProcessingError("Audio processing failed")
        assert str(error) == "Audio processing failed"
        assert isinstance(error, MediaAnalyzerError)
        assert isinstance(error, Exception)
    
    def test_audio_processing_error_inheritance(self):
        """Test AudioProcessingError inheritance."""
        error = AudioProcessingError()
        assert isinstance(error, MediaAnalyzerError)
        assert issubclass(AudioProcessingError, MediaAnalyzerError)
        assert issubclass(AudioProcessingError, Exception)


class TestValidationError:
    """Test ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError with message."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, MediaAnalyzerError)
        assert isinstance(error, Exception)
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inheritance."""
        error = ValidationError()
        assert isinstance(error, MediaAnalyzerError)
        assert issubclass(ValidationError, MediaAnalyzerError)
        assert issubclass(ValidationError, Exception)


class TestTranscriptionError:
    """Test TranscriptionError exception."""
    
    def test_transcription_error_creation(self):
        """Test creating TranscriptionError with message."""
        error = TranscriptionError("Transcription failed")
        assert str(error) == "Transcription failed"
        assert isinstance(error, MediaAnalyzerError)
        assert isinstance(error, Exception)
    
    def test_transcription_error_inheritance(self):
        """Test TranscriptionError inheritance."""
        error = TranscriptionError()
        assert isinstance(error, MediaAnalyzerError)
        assert issubclass(TranscriptionError, MediaAnalyzerError)
        assert issubclass(TranscriptionError, Exception)


class TestExceptionHierarchy:
    """Test exception hierarchy relationships."""
    
    def test_exception_hierarchy(self):
        """Test that all exceptions follow proper hierarchy."""
        # Test that all custom exceptions inherit from MediaAnalyzerError
        assert issubclass(AudioProcessingError, MediaAnalyzerError)
        assert issubclass(ValidationError, MediaAnalyzerError)
        assert issubclass(TranscriptionError, MediaAnalyzerError)
        
        # Test that MediaAnalyzerError inherits from Exception
        assert issubclass(MediaAnalyzerError, Exception)
        
        # Test that all custom exceptions ultimately inherit from Exception
        assert issubclass(AudioProcessingError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(TranscriptionError, Exception)
    
    def test_exception_catching(self):
        """Test that exceptions can be caught properly."""
        # Test catching specific exception
        with pytest.raises(AudioProcessingError):
            raise AudioProcessingError("Test error")
        
        # Test catching base MediaAnalyzerError
        with pytest.raises(MediaAnalyzerError):
            raise AudioProcessingError("Test error")
        
        # Test catching generic Exception
        with pytest.raises(Exception):
            raise ValidationError("Test error")
