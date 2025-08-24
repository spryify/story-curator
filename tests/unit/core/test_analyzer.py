"""Unit tests for the core analyzer module."""

import pytest
from pathlib import Path

from media_analyzer.core.analyzer import Analyzer
from media_analyzer.core.exceptions import ValidationError
from media_analyzer.models.data_models import TranscriptionResult


def test_analyzer_initialization():
    """Test that analyzer can be initialized with default config."""
    analyzer = Analyzer()
    assert analyzer.config == {}


def test_analyzer_initialization_with_config(test_config):
    """Test that analyzer can be initialized with custom config."""
    analyzer = Analyzer(test_config)
    assert analyzer.config == test_config


def test_process_file_not_found():
    """Test that processing a non-existent file raises FileNotFoundError."""
    analyzer = Analyzer()
    with pytest.raises(FileNotFoundError):
        analyzer.process_file("nonexistent.wav")


def test_process_file_invalid_format(tmp_path):
    """Test that processing an invalid file format raises ValueError."""
    # Create a dummy file with invalid extension
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("Not an audio file")
    
    analyzer = Analyzer()
    with pytest.raises(ValueError):
        analyzer.process_file(str(invalid_file))
