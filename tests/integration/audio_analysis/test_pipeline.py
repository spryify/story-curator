"""Integration tests for the audio analysis pipeline."""

import os
import pytest
from pathlib import Path

from media_analyzer.core.analyzer import Analyzer
from media_analyzer.core.exceptions import ValidationError
from media_analyzer.models.audio import TranscriptionResult


def create_test_file(tmp_path: Path, duration: int = 1000, filename: str = "test.wav") -> Path:
    """Helper function to create a test audio file.
    
    Args:
        tmp_path: Directory to create the file in
        duration: Duration of the audio in milliseconds
        filename: Name of the file to create
    
    Returns:
        Path to the created audio file
    """
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    # Create a simple audio file with a sine wave
    sine = Sine(440)  # 440 Hz sine wave
    audio = sine.to_audio_segment(duration=duration)  # 1 second
    
    file_path = tmp_path / filename
    audio.export(str(file_path), format=filename.split(".")[-1])
    return file_path


def test_end_to_end_audio_analysis(tmp_path, test_config):
    """Test the complete audio analysis pipeline."""
    # Initialize components
    analyzer = Analyzer(test_config)
    
    # Create a test audio file
    test_file = create_test_file(tmp_path)
    
    # Process the file with default options
    result = analyzer.process_file(test_file)
    
    # Verify the result structure
    assert isinstance(result, TranscriptionResult)
    assert result.text
    assert result.summary
    assert result.confidence > 0
    assert result.metadata
    
    # Verify metadata
    assert "processing_time" in result.metadata
    assert "sample_rate" in result.metadata
    assert "channels" in result.metadata
    assert "duration" in result.metadata
    assert "language" in result.metadata


def test_pipeline_with_different_formats(tmp_path):
    """Test the pipeline with different audio formats."""
    analyzer = Analyzer()
    
    for fmt in ["wav", "mp3"]:
        # Create test file in the current format
        test_file = create_test_file(tmp_path, filename=f"test.{fmt}")
        
        # Process the file
        result = analyzer.process_file(test_file)
        
        # Verify basic results
        assert isinstance(result, TranscriptionResult)
        assert result.text
        assert result.metadata["duration"] > 0


def test_pipeline_with_various_languages(tmp_path):
    """Test the pipeline with different language settings."""
    analyzer = Analyzer()
    test_file = create_test_file(tmp_path)
    
    languages = ["en", "es", "fr"]  # Test with a few common languages
    for lang in languages:
        result = analyzer.process_file(test_file, {"language": lang})
        assert isinstance(result, TranscriptionResult)
        assert result.metadata["language"] == lang


def test_pipeline_error_propagation(tmp_path):
    """Test how errors propagate through the pipeline."""
    analyzer = Analyzer()
    
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        analyzer.process_file("nonexistent.wav")
    
    # Test with invalid format
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("Not an audio file")
    with pytest.raises(ValueError):
        analyzer.process_file(invalid_file)
    
    # Test with invalid options
    test_file = create_test_file(tmp_path)
    with pytest.raises(ValidationError):
        analyzer.process_file(test_file, {"language": "invalid"})


def test_pipeline_performance(tmp_path):
    """Test pipeline performance with different file sizes."""
    analyzer = Analyzer()
    
    # Test with different durations
    durations = [1000, 5000]  # 1 second, 5 seconds
    
    for duration in durations:
        # Create audio file of specified duration
        file_path = create_test_file(
            tmp_path,
            duration=duration,
            filename=f"test_{duration}ms.wav"
        )
        
        # Process and verify timing
        result = analyzer.process_file(file_path)
        
        # Basic performance checks
        assert result.metadata["processing_time"] > 0
        assert result.metadata["duration"] == duration / 1000.0  # Convert ms to seconds


def test_pipeline_concurrent_processing(tmp_path):
    """Test pipeline handling multiple files concurrently."""
    import concurrent.futures
    
    analyzer = Analyzer()
    
    # Create multiple test files
    test_files = [
        create_test_file(tmp_path, filename=f"test{i}.wav")
        for i in range(3)
    ]
    
    # Process files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_file = {
            executor.submit(analyzer.process_file, file_path): file_path
            for file_path in test_files
        }
        
        # Verify all results
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                assert isinstance(result, TranscriptionResult)
                assert result.text
                assert result.metadata["duration"] > 0
            except Exception as e:
                pytest.fail(f"Processing failed for {file_path}: {e}")
