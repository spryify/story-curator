"""Unit tests for main CLI functionality using mocks."""

import os
import tempfile
import sys
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

# Mock spacy and related modules before importing the CLI
sys.modules['spacy'] = MagicMock()
sys.modules['spacy.language'] = MagicMock()
sys.modules['spacy.tokens'] = MagicMock()

from media_analyzer.cli.__main__ import cli, print_error, print_success
from media_analyzer.models.audio.transcription import TranscriptionResult


class TestMainCLI:
    """Test main CLI functionality and structure."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help_command(self):
        """Test that the CLI help command works."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Media Analyzer CLI" in result.output
        assert "Process and analyze audio files" in result.output
        assert "audio" in result.output  # Should show audio subcommand
        assert "podcast" in result.output  # Should show podcast subcommand
        assert "analyze" in result.output
    
    def test_analyze_help(self):
        """Test analyze subcommand help."""
        result = self.runner.invoke(cli, ['analyze', '--help'])
        assert result.exit_code == 0
        assert "Analyze an audio file" in result.output
        assert "--language" in result.output
        assert "--summary-length" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output
    
    def test_analyze_missing_file(self):
        """Test analyze command with missing file."""
        result = self.runner.invoke(cli, ['analyze', '/nonexistent/file.wav'])
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "no such file" in result.output.lower()
    
    def test_cli_with_no_arguments(self):
        """Test CLI behavior with no arguments."""
        result = self.runner.invoke(cli)
        # CLI with no arguments shows help by default (exit code 0)
        # or exits with error code 2 for missing command
        assert result.exit_code in [0, 2]
        # Should show help or available commands
        assert "analyze" in result.output or "Usage:" in result.output
    
    def test_cli_invalid_command(self):
        """Test CLI with invalid command."""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output
    
    def test_cli_group_configuration(self):
        """Test that CLI group is properly configured."""
        # Test that the CLI group exists and has the right configuration
        assert cli.name == 'cli'
        assert 'Media Analyzer CLI' in cli.get_short_help_str() or 'Process and analyze audio files' in str(cli.help)



class TestCLIUtilities:
    """Test CLI utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_print_error_function(self):
        """Test the print_error helper function."""
        with patch('media_analyzer.cli.__main__.console.print') as mock_print:
            print_error("Test error message")
            mock_print.assert_called_once_with("[red]Error:[/red] Test error message")
    
    def test_print_success_function(self):
        """Test the print_success helper function."""
        with patch('media_analyzer.cli.__main__.console.print') as mock_print:
            print_success("Test success message")
            mock_print.assert_called_once_with("[green]Test success message[/green]")


class TestAnalyzeCommand:
    """Test the analyze command with comprehensive mocking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Create a comprehensive mock analysis result
        self.mock_result = Mock(spec=TranscriptionResult)
        self.mock_result.text = "This is a test transcription of the audio file."
        self.mock_result.summary = "Test audio file transcription summary."
        self.mock_result.confidence = 0.95
        self.mock_result.metadata = {
            'duration': 10.5,
            'processing_time': 2.3,
            'language': 'en',
            'sample_rate': 44100,
            'channels': 2
        }
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_command_success(self, mock_analyzer_class):
        """Test successful analyze command execution."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        # Create a temp file to satisfy click.Path(exists=True)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                # Run the command
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name,
                    '--language', 'en',
                    '--summary-length', '100'
                ])
                
                assert result.exit_code == 0
                assert "Analysis complete" in result.output
                assert "Transcription Result" in result.output
                
                # Verify analyzer was called correctly
                mock_analyzer_class.assert_called_once()
                mock_analyzer.process_file.assert_called_once_with(
                    tmp_file.name,
                    {
                        'language': 'en',
                        'max_summary_length': 100
                    }
                )
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_successful_processing_with_tempfile(self, mock_analyzer_class):
        """Test successful file analysis with temporary file."""
        # Set up mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name,
                    '--language', 'en',
                    '--summary-length', '500'
                ])
                
                assert result.exit_code == 0
                assert "Analysis complete!" in result.output
                assert "This is a test transcription" in result.output
                assert "Test audio file transcription summary" in result.output
                assert "95.00%" in result.output  # Confidence
                assert "10.50 seconds" in result.output  # Duration
                
                # Verify analyzer was called correctly
                mock_analyzer.process_file.assert_called_once_with(
                    tmp_file.name, 
                    {
                        "language": "en",
                        "max_summary_length": 500
                    }
                )
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_command_with_output_file(self, mock_analyzer_class):
        """Test analyze command with output file option."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_input:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_output:
                try:
                    result = self.runner.invoke(cli, [
                        'analyze', tmp_input.name,
                        '--output', tmp_output.name
                    ])
                    
                    assert result.exit_code == 0
                    assert "Results saved to:" in result.output
                    
                    # Verify output file was written
                    assert os.path.exists(tmp_output.name)
                    with open(tmp_output.name, 'r') as f:
                        content = f.read()
                        assert "Transcription Result" in content
                        
                finally:
                    os.unlink(tmp_input.name)
                    if os.path.exists(tmp_output.name):
                        os.unlink(tmp_output.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_with_output_file_tempfile(self, mock_analyzer_class):
        """Test analysis with output file option using temp files."""
        # Set up mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as output_file:
                try:
                    result = self.runner.invoke(cli, [
                        'analyze', input_file.name,
                        '--output', output_file.name,
                        '--language', 'en'
                    ])
                    
                    assert result.exit_code == 0
                    assert "Results saved to:" in result.output
                    assert output_file.name in result.output
                    assert "Analysis complete!" in result.output
                    
                    # Verify output file was created and has content
                    assert os.path.exists(output_file.name)
                    with open(output_file.name, 'r') as f:
                        content = f.read()
                        assert "Transcription Result" in content
                        assert "This is a test transcription" in content
                        assert "Test audio file transcription summary" in content
                        assert "Confidence: 95.00%" in content
                        assert "Duration: 10.50 seconds" in content
                        
                finally:
                    os.unlink(input_file.name)
                    if os.path.exists(output_file.name):
                        os.unlink(output_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_with_verbose_flag(self, mock_analyzer_class):
        """Test analysis with verbose flag."""
        # Set up mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name,
                    '--verbose',
                    '--language', 'es',
                    '--summary-length', '800'
                ])
                
                assert result.exit_code == 0
                assert "Analysis complete!" in result.output
                
                # Verify analyzer was called with correct options
                mock_analyzer.process_file.assert_called_once_with(
                    tmp_file.name,
                    {
                        "language": "es",
                        "max_summary_length": 800
                    }
                )
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_command_with_all_options(self, mock_analyzer_class):
        """Test analyze command with all options specified."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name,
                    '--language', 'es',
                    '--summary-length', '200',
                    '--verbose'
                ])
                
                assert result.exit_code == 0
                
                # Verify correct options were passed
                mock_analyzer.process_file.assert_called_once_with(
                    tmp_file.name,
                    {
                        'language': 'es',
                        'max_summary_length': 200
                    }
                )
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_default_options(self, mock_analyzer_class):
        """Test analyze command with default options."""
        # Set up mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, ['analyze', tmp_file.name])
                
                assert result.exit_code == 0
                
                # Verify default options were used
                mock_analyzer.process_file.assert_called_once_with(
                    tmp_file.name,
                    {
                        "language": "en",  # Default
                        "max_summary_length": 1000  # Default
                    }
                )
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_command_with_processing_error(self, mock_analyzer_class):
        """Test analyze command when processing fails."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.side_effect = Exception("Processing failed")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, ['analyze', tmp_file.name])
                
                assert result.exit_code == 1
                assert "Processing failed: Processing failed" in result.output
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_processing_error(self, mock_analyzer_class):
        """Test handling of processing errors."""
        # Set up mocks to raise an exception
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.side_effect = Exception("Processing failed")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name
                ])
                
                assert result.exit_code == 1
                assert "Processing failed" in result.output
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_command_with_verbose_error(self, mock_analyzer_class):
        """Test analyze command with verbose error reporting."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.side_effect = Exception("Detailed error")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                with patch('media_analyzer.cli.__main__.console.print_exception') as mock_print_exception:
                    result = self.runner.invoke(cli, [
                        'analyze', tmp_file.name, '--verbose'
                    ])
                    
                    assert result.exit_code == 1
                    assert "Processing failed: Detailed error" in result.output
                    mock_print_exception.assert_called_once()
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_analyze_processing_error_with_verbose(self, mock_analyzer_class):
        """Test handling of processing errors with verbose flag."""
        # Set up mocks to raise an exception
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.process_file.side_effect = ValueError("Invalid audio format")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                # Mock console.print_exception to verify it's called
                with patch('media_analyzer.cli.__main__.console.print_exception') as mock_print_exception:
                    result = self.runner.invoke(cli, [
                        'analyze', tmp_file.name,
                        '--verbose'
                    ])
                    
                    assert result.exit_code == 1
                    assert "Invalid audio format" in result.output
                    # In verbose mode, exception details should be printed
                    mock_print_exception.assert_called_once()
            finally:
                os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.__main__.console')
    def test_analyze_command_with_status_updates(self, mock_console):
        """Test that analyze command shows status updates."""
        mock_status = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_status
        
        with patch('media_analyzer.cli.__main__.Analyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.process_file.return_value = self.mock_result
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                try:
                    result = self.runner.invoke(cli, [
                        'analyze', tmp_file.name, '--verbose'
                    ])
                    
                    assert result.exit_code == 0
                    
                    # Verify status updates were called
                    mock_console.status.assert_called_once_with("[bold blue]Processing audio file...")
                    mock_status.update.assert_any_call("[bold blue]Analyzing audio content...")
                    mock_status.update.assert_any_call("[bold blue]Generating output...")
                finally:
                    os.unlink(tmp_file.name)


class TestCLIIntegration:
    """End-to-end integration tests for CLI with comprehensive mocking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('media_analyzer.cli.__main__.Analyzer')
    def test_full_workflow_with_mocked_analyzer(self, mock_analyzer_class):
        """Test complete workflow from CLI to analyzer."""
        # Set up comprehensive mock
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_result = Mock(spec=TranscriptionResult)
        mock_result.text = "Complete integration test transcription."
        mock_result.summary = "Integration test summary."
        mock_result.confidence = 0.87
        mock_result.metadata = {
            'duration': 15.7,
            'processing_time': 3.2,
            'language': 'en',
            'sample_rate': 22050,
            'channels': 1
        }
        mock_analyzer.process_file.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze', tmp_file.name,
                    '--language', 'en',
                    '--summary-length', '750',
                    '--verbose'
                ])
                
                # Verify successful execution
                assert result.exit_code == 0
                assert "Complete integration test transcription" in result.output
                assert "Integration test summary" in result.output
                assert "87.00%" in result.output
                assert "Analysis complete!" in result.output
                
                # Verify all components worked together
                mock_analyzer_class.assert_called_once()
                mock_analyzer.process_file.assert_called_once()
                
            finally:
                os.unlink(tmp_file.name)
