"""Unit tests for the core analyzer module.

This module contains unit tests for the Analyzer class, which serves as the main interface
for the audio analysis functionality. The tests cover:

Test Categories:
1. Initialization and Configuration
   - Default initialization
   - Configuration handling

2. File Processing
   - File path validation
   - Format validation
   - Error handling for invalid files

3. Transcription Features
   - Basic transcription
   - Options handling
   - Format support

4. Error Handling
   - Invalid language options
   - Invalid summary length
   - File not found
   - Invalid format

5. Performance and Security
   - Performance metrics collection
   - Path traversal prevention
   - Input validation

Test Dependencies:
- conftest.py: Provides test_audio_file and test_config fixtures
- test data files: sample.wav and sample.mp3 in tests/data/

Usage:
    pytest tests/unit/core/test_analyzer.py
"""

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


def test_successful_transcription(test_audio_file):
    """Test successful transcription of an audio file."""
    analyzer = Analyzer()
    result = analyzer.process_file(test_audio_file)
    
    assert isinstance(result, TranscriptionResult)
    assert "test audio file" in result.full_text.lower()
    assert "speech recognition" in result.full_text.lower()
    assert result.summary != ""
    assert result.confidence > 0.0
    assert "duration" in result.metadata


def test_transcription_with_options(test_audio_file):
    """Test transcription with custom options."""
    options = {
        "max_summary_length": 100,
        "min_confidence": 0.8,
        "language": "en"
    }
    
    analyzer = Analyzer()
    result = analyzer.process_file(test_audio_file, options)
    
    assert isinstance(result, TranscriptionResult)
    assert len(result.summary.split()) <= 100
    assert result.metadata.get("language") == "en"
    assert "test audio file" in result.full_text.lower()


@pytest.mark.parametrize("audio_format", ["wav", "mp3"])
def test_supported_formats(test_audio_file, audio_format):
    """Test that analyzer supports different audio formats."""
    # Use the actual audio files we created
    test_file = test_audio_file.parent / f"sample.{audio_format}"
    
    analyzer = Analyzer()
    result = analyzer.process_file(str(test_file))
    assert isinstance(result, TranscriptionResult)
    assert "duration" in result.metadata


def test_analyzer_error_handling(test_audio_file):
    """Test that analyzer properly handles and logs errors."""
    analyzer = Analyzer()
    
    # Test with invalid language option
    with pytest.raises(ValidationError) as exc_info:
        analyzer.process_file(test_audio_file, {"language": "invalid"})
    assert "Invalid language" in str(exc_info.value)
    
    # Test with invalid max_summary_length
    with pytest.raises(ValidationError) as exc_info:
        analyzer.process_file(test_audio_file, {"max_summary_length": -1})
    assert "Invalid summary length" in str(exc_info.value)


def test_analyzer_performance_metrics(test_audio_file):
    """Test that analyzer captures performance metrics."""
    analyzer = Analyzer()
    result = analyzer.process_file(test_audio_file)
    
    # Verify performance metrics in metadata
    assert "processing_time" in result.metadata
    assert isinstance(result.metadata["processing_time"], float)
    assert result.metadata["processing_time"] > 0
    
    # Verify audio metadata
    assert "sample_rate" in result.metadata
    assert isinstance(result.metadata["sample_rate"], int)
    assert result.metadata["sample_rate"] > 0
    
    assert "channels" in result.metadata
    assert isinstance(result.metadata["channels"], int)
    assert result.metadata["channels"] > 0
    
    assert "duration" in result.metadata
    assert isinstance(result.metadata["duration"], float)
    assert result.metadata["duration"] > 0


def test_analyzer_security_validation(test_audio_file):
    """Test that analyzer validates inputs for security."""
    analyzer = Analyzer()
    
    # Test with potentially malicious file path
    with pytest.raises(ValidationError) as exc_info:
        analyzer.process_file("../../../etc/passwd")
    assert "Invalid file path" in str(exc_info.value)
    
    # Test with oversized input
    with pytest.raises(ValidationError) as exc_info:
        analyzer.process_file(test_audio_file, {"max_summary_length": 1000000})
    assert "Invalid summary length" in str(exc_info.value)
