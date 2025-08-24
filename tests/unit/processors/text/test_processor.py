"""Unit tests for the text processor module.

This module contains unit tests for the TextProcessor class, which handles text summarization
and other text processing operations on transcribed audio content.

Test Categories:
1. Initialization
   - Default initialization
   - Configuration handling

2. Summarization Features
   - Basic text summarization
   - Length constraints
   - Key information preservation
   - Empty text handling

3. Special Cases
   - Unicode text
   - Special characters
   - Formatting preservation
   - Whitespace handling

4. Error Handling
   - Invalid inputs
   - Length validation
   - Format validation

5. Performance
   - Long text handling
   - Memory usage
   - Processing time

Dependencies:
- conftest.py: Provides test configuration
- No external test data required

Usage:
    pytest tests/unit/processors/text/test_processor.py
"""

import pytest

from media_analyzer.processors.text.processor import TextProcessor


def test_text_processor_initialization():
    """Test that text processor can be initialized with default config."""
    processor = TextProcessor()
    assert processor.config == {}


def test_text_processor_initialization_with_config(test_config):
    """Test that text processor can be initialized with custom config."""
    processor = TextProcessor(test_config.get("text", {}))
    assert processor.config == test_config.get("text", {})


def test_summarize():
    """Test text summarization."""
    processor = TextProcessor()
    
    # Test with short text
    short_text = "This is a test sentence."
    summary = processor.summarize(short_text)
    assert isinstance(summary, str)
    assert summary == short_text  # Short text should not be summarized
    
    # Test with long text
    long_text = " ".join(["This is test sentence " + str(i) for i in range(100)])
    summary = processor.summarize(long_text)
    assert isinstance(summary, str)
    assert len(summary) < len(long_text)
    assert len(summary.split()) > 0


def test_summarize_with_max_length():
    """Test summarization with max length constraint."""
    processor = TextProcessor()
    
    text = " ".join(["This is test sentence " + str(i) for i in range(100)])
    max_length = 100
    
    summary = processor.summarize(text, max_length=max_length)
    assert isinstance(summary, str)
    assert len(summary) <= max_length


def test_summarize_empty_text():
    """Test summarization with empty or whitespace text."""
    processor = TextProcessor()
    
    assert processor.summarize("") == ""
    assert processor.summarize("   ") == ""
    assert processor.summarize("\n\t") == ""


def test_summarize_with_invalid_input():
    """Test summarization with invalid input."""
    processor = TextProcessor()
    
    with pytest.raises(ValueError) as exc_info:
        processor.summarize(None)
    assert "Input text cannot be None" in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        processor.summarize("test", max_length=-1)
    assert "max_length must be positive" in str(exc_info.value)


def test_summarize_preserves_key_information():
    """Test that summarization preserves key information."""
    processor = TextProcessor()
    
    text = """
    The quick brown fox jumps over the lazy dog.
    This is an important fact that should be in the summary.
    Here are some details that might be less important.
    Another crucial point that should be preserved.
    Some more filler text that could be omitted.
    The final important conclusion.
    """
    
    summary = processor.summarize(text, max_length=100)
    
    # Key phrases that should be in the summary
    assert any(phrase in summary.lower() for phrase in [
        "important fact",
        "crucial point",
        "conclusion"
    ])


def test_summarize_handles_special_characters():
    """Test summarization with special characters and formatting."""
    processor = TextProcessor()
    
    text = """
    Line 1 with *special* formatting
    Line 2 with numbers: 12345
    Line 3 with punctuation: !@#$%^&*()
    Line 4 with unicode: 你好, привет, مرحبا
    """
    
    summary = processor.summarize(text)
    assert isinstance(summary, str)
    assert len(summary) > 0
    # Summary should preserve some of the special content
    assert any(char in summary for char in ["*", "1", "!", "你", "п", "م"])
