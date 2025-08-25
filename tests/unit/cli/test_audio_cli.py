"""Unit tests for the audio CLI interface.

This module tests the CLI functionality for audio processing, following ADR-004
requirements for CLI testing and ADR-006 for test coverage.

Test Categories:
1. Basic CLI Operations
2. Format Validation
3. Output Formatting
4. Error Handling
5. File I/O
"""

from pathlib import Path
import json
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch

import sys
from unittest.mock import MagicMock, patch

# Mock core dependencies
mock_dependencies = [
    'whisper',
    'spacy',
    'torch',
    'numpy',
    'thinc'
]

for dep in mock_dependencies:
    sys.modules[dep] = MagicMock()

with patch('media_analyzer.core.analyzer.Analyzer'), \
     patch('media_analyzer.processors.text.processor.TextProcessor'), \
     patch('media_analyzer.processors.audio.processor.AudioProcessor'):
    from media_analyzer.cli.audio import cli, transcribe
from media_analyzer.core.exceptions import ValidationError
from media_analyzer.models.data_models import TranscriptionResult


@pytest.fixture
def cli_runner():
    """Fixture providing Click CLI test runner.
    
    Returns:
        CliRunner: Configured Click test runner
    """
    return CliRunner()


@pytest.fixture
def mock_analyzer():
    """Fixture providing mocked Analyzer class.
    
    Returns:
        Mock: Mocked Analyzer instance with predefined responses
    """
    mock = Mock()
    
    # Set up mock result
    result = Mock(spec=TranscriptionResult)
    result.full_text = "This is a test transcription"
    result.summary = "Test summary"
    result.confidence = 0.95
    result.metadata = {
        "duration": 10.5,
        "processing_time": 2.3,
        "language": "en",
        "sample_rate": 16000,
        "channels": 1
    }
    
    # Configure analyzer mock to return our result
    mock.process_file.return_value = result
    return mock


def test_cli_help(cli_runner):
    """Test CLI help output.
    
    Args:
        cli_runner: Click CLI test runner
    """
    result = cli_runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Audio analysis tools' in result.output
    assert 'transcribe' in result.output


def test_transcribe_help(cli_runner):
    """Test transcribe command help output.
    
    Args:
        cli_runner: Click CLI test runner
    """
    result = cli_runner.invoke(cli, ['transcribe', '--help'])
    assert result.exit_code == 0
    assert 'Transcribe an audio file' in result.output
    assert 'Supported audio formats: MP3, M4A, AAC, WAV' in result.output


@patch('media_analyzer.cli.audio.Analyzer')
def test_transcribe_basic(mock_analyzer_cls, cli_runner, mock_analyzer, tmp_path):
    """Test basic transcription functionality.
    
    Args:
        mock_analyzer_cls: Mocked Analyzer class
        cli_runner: Click CLI test runner
        mock_analyzer: Mocked analyzer instance
        tmp_path: Temporary directory path
    """
    mock_analyzer_cls.return_value = mock_analyzer
    
    # Create a dummy audio file
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"dummy audio content")
    
    result = cli_runner.invoke(cli, ['transcribe', str(audio_file)])
    assert result.exit_code == 0
    assert "Transcription Result" in result.output
    assert "Test summary" in result.output
    assert "95.00%" in result.output  # Confidence
    assert "10.50 seconds" in result.output  # Duration


@patch('media_analyzer.cli.audio.Analyzer')
def test_transcribe_json_output(mock_analyzer_cls, cli_runner, mock_analyzer, tmp_path):
    """Test JSON output format.
    
    Args:
        mock_analyzer_cls: Mocked Analyzer class
        cli_runner: Click CLI test runner
        mock_analyzer: Mocked analyzer instance
        tmp_path: Temporary directory path
    """
    mock_analyzer_cls.return_value = mock_analyzer
    
    # Create a dummy audio file
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"dummy audio content")
    
    # Test JSON output to console
    result = cli_runner.invoke(cli, ['transcribe', str(audio_file), '--format', 'json'])
    assert result.exit_code == 0
    # Find the JSON part in the output (before the success message)
    json_output = result.output.split("\n✨")[0]
    data = json.loads(json_output)
    assert "transcription" in data
    assert data["transcription"]["full_text"] == "This is a test transcription"
    assert data["metadata"]["confidence"] == 0.95    # Test JSON output to file
    output_file = tmp_path / "output.json"
    result = cli_runner.invoke(cli, [
        'transcribe', 
        str(audio_file), 
        '--format', 'json',
        '--output', str(output_file)
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    
    with open(output_file) as f:
        data = json.load(f)
        assert "transcription" in data
        assert "metadata" in data
        assert data["metadata"]["sample_rate"] == 16000


    @patch('media_analyzer.cli.audio.Analyzer')
    def test_transcribe_with_options(mock_analyzer_cls, cli_runner, mock_analyzer, tmp_path):
        """Test transcription with various command options.
    
        Args:
            mock_analyzer_cls: Mocked Analyzer class
            cli_runner: Click CLI test runner
            mock_analyzer: Mocked analyzer instance
            tmp_path: Temporary directory path
        """
        mock_analyzer_cls.return_value = mock_analyzer
    
        # Create a dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy audio content")
    
        result = cli_runner.invoke(cli, [
            'transcribe',
            str(audio_file),
            '--language', 'fr',
            '--summary-length', '500',
            '--verbose'
        ])
    
        assert result.exit_code == 0
        mock_analyzer.process_file.assert_called_once()
        file_path, options = mock_analyzer.process_file.call_args[0]
        assert str(audio_file) == str(file_path)
        assert options['language'] == 'fr'
        assert options['max_summary_length'] == 500
@patch('media_analyzer.cli.audio.Analyzer')
def test_transcribe_error_handling(mock_analyzer_cls, cli_runner, mock_analyzer, tmp_path):
    """Test error handling in transcribe command.
    
    Args:
        mock_analyzer_cls: Mocked Analyzer class
        cli_runner: Click CLI test runner
        mock_analyzer: Mocked analyzer instance
        tmp_path: Temporary directory path
    """
    mock_analyzer_cls.return_value = mock_analyzer
    
    # Test non-existent file
    result = cli_runner.invoke(cli, ['transcribe', 'nonexistent.wav'])
    assert result.exit_code == 2
    assert "does not exist" in result.output
    
    # Test validation error
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"dummy audio content")
    
    mock_analyzer.process_file.side_effect = ValidationError("Invalid audio format")
    result = cli_runner.invoke(cli, ['transcribe', str(audio_file)])
    assert result.exit_code == 1
    assert "Validation error" in result.output
    
    # Test processing error
    mock_analyzer.process_file.side_effect = Exception("Processing failed")
    result = cli_runner.invoke(cli, ['transcribe', str(audio_file), '--verbose'])
    assert result.exit_code == 1
    assert "Processing failed" in result.output
    assert "Traceback" in result.output  # Verbose mode shows traceback


@patch('media_analyzer.cli.audio.Analyzer')
def test_cli_main():
    """Test CLI main entry point."""
    with patch('media_analyzer.cli.audio.cli') as mock_cli:
        from media_analyzer.cli.audio import main
        main()
        mock_cli.assert_called_once()


def test_transcribe_output_file(mock_analyzer_cls, cli_runner, mock_analyzer, tmp_path):
    """Test writing transcription to output file.
    
    Args:
        mock_analyzer_cls: Mocked Analyzer class
        cli_runner: Click CLI test runner
        mock_analyzer: Mocked analyzer instance
        tmp_path: Temporary directory path
    """
    """Test writing transcription to output file.
    
    Args:
        mock_analyzer_cls: Mocked Analyzer class
        cli_runner: Click CLI test runner
        mock_analyzer: Mocked analyzer instance
        tmp_path: Temporary directory path
    """
    mock_analyzer_cls.return_value = mock_analyzer
    
    # Create input and output files
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"dummy audio content")
    output_file = tmp_path / "output.txt"
    
    # Test text output
    result = cli_runner.invoke(cli, [
        'transcribe',
        str(audio_file),
        '--output', str(output_file)
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "Transcription Result" in content
    assert "This is a test transcription" in content
    assert "Test summary" in content
    
    # Test overwriting existing file
    result = cli_runner.invoke(cli, [
        'transcribe',
        str(audio_file),
        '--output', str(output_file)
    ])
    assert result.exit_code == 0
    assert "Results saved to:" in result.output
