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
from tests.utils.audio import create_timed_speech_file


@pytest.fixture
def audio_analyzer():
    """Create an AudioAnalyzer instance."""
    return Analyzer()

class TestAudioPipeline:
    """Integration test suite for audio processing pipeline."""

    def test_end_to_end_audio_analysis(self, audio_analyzer, tmp_path, test_config):
        """Test the complete audio analysis pipeline."""
        # Create a test audio file
        test_file = create_timed_speech_file(tmp_path)
        
        # Process the file with default options
        result = audio_analyzer.process_file(test_file)
        
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

    def test_pipeline_with_different_formats(self, audio_analyzer, tmp_path):
        """Test the pipeline with different audio formats."""
        for fmt in ["wav", "mp3"]:
            # Create test file in the current format
            test_file = create_timed_speech_file(tmp_path, filename=f"test.{fmt}")
            
            # Process the file
            result = audio_analyzer.process_file(test_file)
            
            # Verify basic results
            assert isinstance(result, TranscriptionResult)
            assert result.text
            assert result.metadata["duration"] > 0

    def test_pipeline_with_various_languages(self, audio_analyzer, tmp_path):
        """Test the pipeline with different language settings."""
        test_file = create_timed_speech_file(tmp_path)
        
        # Test valid language
        result = audio_analyzer.process_file(test_file, {"language": "en"})
        assert isinstance(result, TranscriptionResult)
        assert result.metadata["language"] == "en"
        
        # Test unsupported language
        with pytest.raises(ValueError) as exc_info:
            audio_analyzer.process_file(test_file, {"language": "es"})
        assert "Unsupported language: es" in str(exc_info.value)

    def test_pipeline_error_propagation(self, audio_analyzer, tmp_path):
        """Test how errors propagate through the pipeline."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            audio_analyzer.process_file("nonexistent.wav")
        
        # Test with invalid format
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("Not an audio file")
        with pytest.raises(ValueError):
            audio_analyzer.process_file(invalid_file)
        
        # Test with invalid options
        test_file = create_timed_speech_file(tmp_path)
        with pytest.raises(ValidationError):
            audio_analyzer.process_file(test_file, {"language": "invalid"})

    def test_pipeline_performance(self, audio_analyzer, tmp_path):
        """Test pipeline performance with different file sizes."""
        # Test with different durations
        durations = [10000, 20000]  # 10 seconds, 20 seconds
        
        for duration in durations:
            # Create audio file of specified duration
            file_path = create_timed_speech_file(
                tmp_path,
                duration=duration,
                filename=f"test_{duration}ms.wav"
            )
            
            # Process and verify timing
            result = audio_analyzer.process_file(file_path)
            
            # Basic performance checks
            assert result.metadata["processing_time"] > 0
            # Verify duration is within expected range, allowing 50% variance
            expected_duration = duration / 1000.0  # Convert ms to seconds
            actual_duration = result.metadata["duration"]
            # Allow for wider variance since TTS timing can vary significantly
            assert 0.5 * expected_duration <= actual_duration <= 1.5 * expected_duration

    def test_pipeline_concurrent_processing(self, audio_analyzer, tmp_path):
        """Test pipeline handling multiple files concurrently."""
        import concurrent.futures
        
        # Create multiple test files
        test_files = [
            create_timed_speech_file(tmp_path, filename=f"test{i}.wav")
            for i in range(3)
        ]
        
        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {
                executor.submit(audio_analyzer.process_file, file_path): file_path
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
