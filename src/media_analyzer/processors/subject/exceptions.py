"""Exceptions for subject identification."""


class ProcessingError(Exception):
    """Base exception for all subject processing errors."""

    pass


class SubjectProcessingError(ProcessingError):
    """Error during subject processing."""

    pass


class InvalidInputError(ProcessingError):
    """Error for invalid input data."""

    pass


class ProcessingTimeoutError(SubjectProcessingError):
    """Raised when processing exceeds time limit."""

    pass


class ModelLoadError(SubjectProcessingError):
    """Raised when a model fails to load."""

    pass


class SubjectIdentificationError(SubjectProcessingError):
    """Raised when subject identification fails."""

    pass
