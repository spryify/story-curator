"""Unit tests for icon curator exceptions."""

import pytest

from src.icon_curator.core.exceptions import (
    IconCuratorError,
    ScrapingError,
    ValidationError,
    DatabaseError,
    ProcessingError,
    NetworkError
)


class TestExceptions:
    """Test cases for custom exceptions."""
    
    def test_base_exception_hierarchy(self):
        """Test that all custom exceptions inherit from IconCuratorError."""
        exceptions = [
            ScrapingError,
            ValidationError,
            DatabaseError,
            ProcessingError,
            NetworkError
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, IconCuratorError)
            assert issubclass(exc_class, Exception)
    
    def test_exception_creation_with_message(self):
        """Test creating exceptions with error messages."""
        message = "Test error message"
        
        exceptions = [
            IconCuratorError(message),
            ScrapingError(message),
            ValidationError(message),
            DatabaseError(message),
            ProcessingError(message),
            NetworkError(message)
        ]
        
        for exc in exceptions:
            assert str(exc) == message
    
    def test_exception_creation_without_message(self):
        """Test creating exceptions without error messages."""
        exceptions = [
            IconCuratorError(),
            ScrapingError(),
            ValidationError(),
            DatabaseError(),
            ProcessingError(),
            NetworkError()
        ]
        
        # Should not raise any errors
        for exc in exceptions:
            assert isinstance(exc, Exception)
    
    def test_exception_chaining(self):
        """Test exception chaining (raise from)."""
        original_error = ValueError("Original error")
        
        try:
            raise ValidationError("Validation failed") from original_error
        except ValidationError as e:
            assert str(e) == "Validation failed"
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ValueError)
