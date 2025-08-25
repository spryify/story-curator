"""Custom exceptions for the media analyzer."""

class MediaAnalyzerError(Exception):
    """Base exception for all media analyzer errors."""
    pass


class AudioProcessingError(MediaAnalyzerError):
    """Raised when there's an error processing audio content."""
    pass


class ValidationError(MediaAnalyzerError):
    """Raised when input validation fails."""
    pass


class TranscriptionError(MediaAnalyzerError):
    """Raised when speech-to-text transcription fails."""
    pass


class SummarizationError(MediaAnalyzerError):
    """Raised when text summarization fails."""
    pass


class ProcessingError(MediaAnalyzerError):
    """Raised when general processing fails."""
    pass
