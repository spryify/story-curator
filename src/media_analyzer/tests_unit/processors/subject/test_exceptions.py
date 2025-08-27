"""Tests for subject identification exceptions."""
import pytest
from media_analyzer.processors.subject.exceptions import (
    SubjectProcessingError,
    InvalidInputError,
    ProcessingTimeoutError,
    ModelLoadError
)


def test_subject_processing_error():
    """Test base exception."""
    with pytest.raises(SubjectProcessingError) as exc_info:
        raise SubjectProcessingError("Test error")
    assert str(exc_info.value) == "Test error"


def test_invalid_input_error():
    """Test invalid input exception."""
    with pytest.raises(InvalidInputError) as exc_info:
        raise InvalidInputError("Invalid text")
    assert str(exc_info.value) == "Invalid text"
    assert isinstance(exc_info.value, SubjectProcessingError)


def test_processing_timeout_error():
    """Test timeout exception."""
    with pytest.raises(ProcessingTimeoutError) as exc_info:
        raise ProcessingTimeoutError("Processing timed out")
    assert str(exc_info.value) == "Processing timed out"
    assert isinstance(exc_info.value, SubjectProcessingError)


def test_model_load_error():
    """Test model loading exception."""
    with pytest.raises(ModelLoadError) as exc_info:
        raise ModelLoadError("Failed to load model")
    assert str(exc_info.value) == "Failed to load model"
    assert isinstance(exc_info.value, SubjectProcessingError)
