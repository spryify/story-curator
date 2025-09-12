"""Unit tests for audio format support.

This module contains tests specifically for validating support of different audio formats:
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- AAC (.aac)

Test Categories:
1. Format Detection
2. Loading Different Formats
3. Format Validation
4. Format Conversion
5. Error Handling
"""

import os
import pytest
from pathlib import Path
import tempfile
import wave

from pydub import AudioSegment

from media_analyzer.core.validator import AudioFileValidator, AudioFormat
from media_analyzer.processors.audio.audio_processor import AudioProcessor
from media_analyzer.core.exceptions import AudioProcessingError

# Skip tests that require 'say' command only in CI environments
skip_audio_tests = pytest.mark.skipif(
    os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true',
    reason="Requires macOS 'say' command for audio generation - skipped in CI environments"
)

# Audio fixtures are automatically imported from tests.fixtures.audio.samples





@skip_audio_tests
def test_format_detection(sample_wav, sample_mp3, sample_m4a, sample_aac):
    """Test detection of different audio formats.
    
    Args:
        sample_wav: Path to sample WAV file
        sample_mp3: Path to sample MP3 file
        sample_m4a: Path to sample M4A file
        sample_aac: Path to sample AAC file
    """
    validator = AudioFileValidator()
    
    # Test WAV detection
    assert AudioFormat.from_extension(sample_wav.suffix) == AudioFormat.WAV
    
    # Test MP3 detection
    assert AudioFormat.from_extension(sample_mp3.suffix) == AudioFormat.MP3
    
    # Test M4A detection
    assert AudioFormat.from_extension(sample_m4a.suffix) == AudioFormat.M4A
    
    # Test AAC detection
    assert AudioFormat.from_extension(sample_aac.suffix) == AudioFormat.AAC
    
    # Test invalid format
    assert AudioFormat.from_extension(".xyz") is None


@skip_audio_tests
def test_format_validation(sample_wav, sample_mp3, sample_m4a, sample_aac):
    """Test validation of different audio formats.
    
    Args:
        sample_wav: Path to sample WAV file
        sample_mp3: Path to sample MP3 file
        sample_m4a: Path to sample M4A file
        sample_aac: Path to sample AAC file
    """
    validator = AudioFileValidator()
    
    # Test all supported formats
    is_valid, _ = validator.validate_file(str(sample_wav))
    assert is_valid
    
    is_valid, _ = validator.validate_file(str(sample_mp3))
    assert is_valid
    
    is_valid, _ = validator.validate_file(str(sample_m4a))
    assert is_valid
    
    is_valid, _ = validator.validate_file(str(sample_aac))
    assert is_valid
    
    # Test invalid format
    with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
        is_valid, error = validator.validate_file(tmp.name)
        assert not is_valid
        assert error is not None and "Unsupported audio format" in error


@skip_audio_tests
def test_audio_loading(sample_wav, sample_mp3, sample_m4a, sample_aac):
    """Test loading of different audio formats.
    
    Args:
        sample_wav: Path to sample WAV file
        sample_mp3: Path to sample MP3 file
        sample_m4a: Path to sample M4A file
        sample_aac: Path to sample AAC file
    """
    processor = AudioProcessor()
    
    # Test loading each format
    for file_path in [sample_wav, sample_mp3, sample_m4a, sample_aac]:
        audio = processor.load_audio(file_path)
        assert isinstance(audio, AudioSegment)
        assert len(audio) > 0
        # Check that duration is reasonable (between 1 and 5 seconds)
        duration_ms = len(audio)
        assert 1000 <= duration_ms <= 5000
    with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
        with pytest.raises(AudioProcessingError):
            processor.load_audio(Path(tmp.name))


@skip_audio_tests
def test_audio_info(sample_wav):
    """Test getting audio file information.
    
    Args:
        sample_wav: Path to sample WAV file
    """
    processor = AudioProcessor()
    audio = processor.load_audio(sample_wav)
    
    info = processor.get_audio_info(audio)
    assert isinstance(info, dict)
    assert "sample_rate" in info
    assert isinstance(info["sample_rate"], int)
    assert info["sample_rate"] > 0
    assert "channels" in info
    assert isinstance(info["channels"], int)
    assert info["channels"] > 0
    assert "duration" in info
    assert isinstance(info["duration"], float)
    assert info["duration"] > 0


@skip_audio_tests
def test_format_conversion(sample_wav, sample_mp3, sample_m4a, sample_aac, tmp_path):
    """Test conversion between different audio formats.
    
    Args:
        sample_wav: Path to sample WAV file
        sample_mp3: Path to sample MP3 file
        sample_m4a: Path to sample M4A file
        sample_aac: Path to sample AAC file
        tmp_path: Temporary directory from pytest
    """
    validator = AudioFileValidator()
    
    # Test conversion to WAV from each format
    for input_file in [sample_mp3, sample_m4a, sample_aac]:
        output_file = tmp_path / f"converted_{input_file.name}.wav"
        
        try:
            assert validator.convert_to_wav(str(input_file), str(output_file))
            assert output_file.exists()
            
            # Verify converted file
            with wave.open(str(output_file), 'rb') as wav:
                assert wav.getnchannels() == 1  # Mono
                assert wav.getframerate() == 16000  # 16kHz
                
        finally:
            # Cleanup
            if output_file.exists():
                output_file.unlink()


def test_processor_configuration():
    """Test AudioProcessor initialization with different configurations."""
    from unittest.mock import patch, Mock
    
    # Test default config with Whisper model mocking
    with patch('whisper.load_model') as mock_load_model:
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        processor = AudioProcessor()
        assert processor.config == {}
        assert processor.model is not None
        
    # Test custom config with mock_model flag
    config = {
        "model": "base",
        "device": "cpu", 
        "sample_rate": 16000,
        "max_duration": 3600,
        "mock_model": True  # Use the built-in mock mechanism
    }
    processor = AudioProcessor(config)
    assert processor.config == config





def test_error_handling(tmp_path):
    """Test error handling for invalid files and formats.
    
    Args:
        tmp_path: Temporary directory from pytest
    """
    from unittest.mock import patch, Mock
    
    validator = AudioFileValidator()
    
    with patch('whisper.load_model') as mock_load_model:
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        processor = AudioProcessor()
    
    # Test non-existent file
    non_existent = tmp_path / "non_existent.wav"
    is_valid, error = validator.validate_file(str(non_existent))
    assert not is_valid
    assert error is not None and "File does not exist" in error
    
    # Test empty file
    empty_file = tmp_path / "empty.wav"
    empty_file.touch()
    try:
        is_valid, error = validator.validate_file(str(empty_file))
        assert not is_valid
        assert error is not None and ("Invalid audio file format" in error or "Invalid data found" in error)
    finally:
        empty_file.unlink()
    
    # Test corrupted file
    corrupt_file = tmp_path / "corrupt.wav"
    try:
        # Create corrupted WAV file
        with open(corrupt_file, 'wb') as f:
            f.write(b'RIFF1234WAVEfmt not valid audio data')
            
        is_valid, error = validator.validate_file(str(corrupt_file))
        assert not is_valid
        assert error is not None and ("Invalid audio file" in error or "Invalid data found" in error)
    finally:
        if corrupt_file.exists():
            corrupt_file.unlink()


@skip_audio_tests
def test_extract_text_unit(sample_wav):
    """Unit test for text extraction logic without Whisper dependency.
    
    This test focuses on the AudioProcessor's text extraction workflow
    and result formatting, using patch to mock the actual Whisper model.
    
    Args:
        sample_wav: Path to sample WAV file
    """
    from unittest.mock import patch, Mock
    from media_analyzer.processors.audio.audio_processor import AudioProcessor
    from media_analyzer.models.audio import TranscriptionResult
    
    # Mock the Whisper model at the module level
    mock_transcribe_result = {
        "text": "This is mocked transcribed text.",
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "This is mocked transcribed text."}
        ]
    }
    
    with patch('whisper.load_model') as mock_load_model:
        mock_model = Mock()
        mock_model.transcribe.return_value = mock_transcribe_result
        mock_load_model.return_value = mock_model
        
        processor = AudioProcessor()
        
        # Test with default options
        audio = processor.load_audio(sample_wav)
        result = processor.extract_text(audio)
        
        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.text, str)
        assert result.text == "This is mocked transcribed text."
        assert result.language == "en"
        assert isinstance(result.segments, list)
        assert len(result.segments) == 1
        
        # Verify the mock was called
        mock_load_model.assert_called_once()
        mock_model.transcribe.assert_called()
        
        # Test with custom options
        options = {
            "language": "en",
            "task": "transcribe"
        }
        result = processor.extract_text(audio, options)
        assert result.metadata.get("task") == "transcribe"
        assert result.metadata.get("language") == "en"
