"""Integration tests for the audio analysis pipeline."""

import os
import numpy as np
from pathlib import Path
from scipy import signal
import pytest
import io
import wave

from media_analyzer.core.analyzer import Analyzer
from media_analyzer.core.exceptions import ValidationError
from media_analyzer.models.audio import TranscriptionResult


def create_test_file(tmp_path: Path, duration: int = 1000, filename: str = "test.wav") -> Path:
    """Create a test audio file using macOS text-to-speech.
    
    Args:
        tmp_path: Directory to create the file in
        duration: Duration in milliseconds (approximate)
        filename: Name of the file to create
        
    Returns:
        Path to the created audio file
    """
    import subprocess
    from pydub import AudioSegment
    
    # Create temp AIFF file (macOS say command output)
    temp_aiff = str(tmp_path / "temp.aiff")
    
    # Generate test text based on duration, with proper speech timing
    # Use shorter phrases for more precise timing control
    base_phrase = "testing one two three"  # Takes roughly 1 second at 200 wpm
    # Calculate number of phrases needed, accounting for the speaking rate
    words_per_phrase = 4
    words_per_minute = 200  # From the say command rate
    words_per_second = words_per_minute / 60
    seconds_per_phrase = words_per_phrase / words_per_second
    num_phrases = max(1, round((duration / 1000.0) / seconds_per_phrase))
    phrases = [base_phrase] * num_phrases
    text = ". ".join(phrases) + "."  # Add periods for natural pauses
    
    # Use macOS say command to generate speech with fast but natural rate
    # Note: 200 words per minute is a natural fast speaking rate
    subprocess.run(["say", "-r", "200", "-v", "Samantha", "-o", temp_aiff, text], check=True)
    
    # Convert to AudioSegment and adjust format
    audio = AudioSegment.from_file(temp_aiff, format="aiff")
    
    # Convert to proper format for Whisper
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    # Export to desired format
    file_path = tmp_path / filename
    audio.export(str(file_path), format=filename.split('.')[-1])
    
    # Clean up temp file
    import os
    os.unlink(temp_aiff)
    
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
    durations = [10000, 20000]  # 10 seconds, 20 seconds
    
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
        # Verify duration is within expected range, allowing 50% variance
        expected_duration = duration / 1000.0  # Convert ms to seconds
        actual_duration = result.metadata["duration"]
        # Allow for wider variance since TTS timing can vary significantly
        assert 0.5 * expected_duration <= actual_duration <= 1.5 * expected_duration


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
