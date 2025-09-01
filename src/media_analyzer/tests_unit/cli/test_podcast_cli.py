"""Unit tests for podcast CLI functionality using mocks."""

import os
import sys
import json
import tempfile
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Mock spacy and related modules before importing the CLI
sys.modules['spacy'] = MagicMock()
sys.modules['spacy.language'] = MagicMock()
sys.modules['spacy.tokens'] = MagicMock()

from media_analyzer.cli.podcast import cli, print_error, print_success, print_warning
from media_analyzer.models.podcast import AnalysisOptions


class TestPodcastCLI:
    """Test main podcast CLI functionality and structure."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help_command(self):
        """Test that the podcast CLI help command works."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Podcast analysis tools" in result.output
        assert "Analyze podcast episodes from streaming platforms" in result.output
        assert "analyze" in result.output
        assert "metadata" in result.output
    
    def test_analyze_help(self):
        """Test analyze subcommand help."""
        result = self.runner.invoke(cli, ['analyze', '--help'])
        assert result.exit_code == 0
        assert "Analyze a podcast episode from a streaming platform URL" in result.output
        assert "--language" in result.output
        assert "--max-duration" in result.output
        assert "--segment-length" in result.output
        assert "--confidence-threshold" in result.output
        assert "--skip-subjects" in result.output
        assert "--output" in result.output
        assert "--format" in result.output
        assert "--verbose" in result.output
    
    def test_metadata_help(self):
        """Test metadata subcommand help."""
        result = self.runner.invoke(cli, ['metadata', '--help'])
        assert result.exit_code == 0
        assert "Extract metadata from a podcast episode" in result.output
        assert "without full analysis" in result.output
    
    def test_cli_structure(self):
        """Test that CLI has the expected command structure."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "metadata" in result.output


class TestPodcastCLIUtilities:
    """Test CLI utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_print_error_function(self):
        """Test the print_error helper function."""
        with patch('media_analyzer.cli.podcast.console.print') as mock_print:
            print_error("Test error message")
            mock_print.assert_called_once_with("[red]Error:[/red] Test error message")
    
    def test_print_success_function(self):
        """Test the print_success helper function."""
        with patch('media_analyzer.cli.podcast.console.print') as mock_print:
            print_success("Test success message")
            mock_print.assert_called_once_with("[green]Test success message[/green]")
    
    def test_print_warning_function(self):
        """Test the print_warning helper function."""
        with patch('media_analyzer.cli.podcast.console.print') as mock_print:
            print_warning("Test warning message")
            mock_print.assert_called_once_with("[yellow]Warning:[/yellow] Test warning message")


class TestAnalyzeCommand:
    """Test the analyze command with comprehensive mocking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Create mock analysis result
        self.mock_episode = Mock()
        self.mock_episode.title = "Test Episode Title"
        self.mock_episode.show_name = "Test Podcast Show"
        self.mock_episode.platform = "rss"
        self.mock_episode.duration_seconds = 3600  # 1 hour
        self.mock_episode.publication_date = datetime(2024, 1, 15, 10, 30)
        self.mock_episode.description = "This is a test podcast episode description."
        self.mock_episode.url = "https://example.com/test-episode.mp3"
        self.mock_episode.author = "Test Author"
        
        self.mock_transcription = Mock()
        self.mock_transcription.text = "This is the transcribed text of the podcast episode."
        self.mock_transcription.language = "en"
        self.mock_transcription.confidence = 0.92
        self.mock_transcription.metadata = {"duration": 3600.0, "processing_time": 45.2}
        
        self.mock_subject = Mock()
        self.mock_subject.name = "Test Subject"
        self.mock_subject.subject_type = Mock()
        self.mock_subject.subject_type.value = "person"
        self.mock_subject.confidence = 0.85
        
        self.mock_result = Mock()
        self.mock_result.success = True
        self.mock_result.episode = self.mock_episode
        self.mock_result.transcription = self.mock_transcription
        self.mock_result.subjects = [self.mock_subject]
        self.mock_result.processing_metadata = {
            "connector_used": "rss",
            "transcription_service": "whisper",
            "subject_extraction_enabled": True
        }
        self.mock_result.error_message = None
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    @patch('media_analyzer.cli.podcast._analyze_episode')
    def test_analyze_command_success(self, mock_analyze, mock_asyncio_run):
        """Test successful analyze command execution."""
        # Setup mocks
        mock_asyncio_run.return_value = self.mock_result
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/podcast.rss',
            '--language', 'en',
            '--max-duration', '180'
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete!" in result.output
        assert "Test Episode Title" in result.output
        assert "Test Podcast Show" in result.output
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    @patch('media_analyzer.cli.podcast._analyze_episode')
    def test_analyze_command_with_all_options(self, mock_analyze, mock_asyncio_run):
        """Test analyze command with all options specified."""
        mock_asyncio_run.return_value = self.mock_result
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/podcast.rss',
            '--language', 'es',
            '--max-duration', '120',
            '--segment-length', '240',
            '--confidence-threshold', '0.8',
            '--skip-subjects',
            '--format', 'json',
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete!" in result.output
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_json_output(self, mock_asyncio_run):
        """Test analyze command with JSON output format."""
        mock_asyncio_run.return_value = self.mock_result
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete!" in result.output
        # JSON output should be displayed
        assert '"episode"' in result.output or "Test Episode Title" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_with_output_file_text(self, mock_asyncio_run):
        """Test analyze command with text output file."""
        mock_asyncio_run.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze',
                    'https://example.com/podcast.rss',
                    '--output', tmp_file.name,
                    '--format', 'text'
                ])
                
                assert result.exit_code == 0
                assert "Results saved to:" in result.output
                assert "Analysis complete!" in result.output
                
                # Verify output file was created and has content
                assert os.path.exists(tmp_file.name)
                with open(tmp_file.name, 'r') as f:
                    content = f.read()
                    assert "Podcast Analysis Result" in content
                    assert "Test Episode Title" in content
                    assert "Test Podcast Show" in content
                    
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_with_output_file_json(self, mock_asyncio_run):
        """Test analyze command with JSON output file."""
        mock_asyncio_run.return_value = self.mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze',
                    'https://example.com/podcast.rss',
                    '--output', tmp_file.name,
                    '--format', 'json'
                ])
                
                assert result.exit_code == 0
                assert "Results saved to:" in result.output
                assert "Analysis complete!" in result.output
                
                # Verify output file was created and has valid JSON
                assert os.path.exists(tmp_file.name)
                with open(tmp_file.name, 'r') as f:
                    data = json.load(f)
                    assert "episode" in data
                    assert "transcription" in data
                    assert "subjects" in data
                    assert data["episode"]["title"] == "Test Episode Title"
                    
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_analyze_command_invalid_confidence_threshold(self):
        """Test analyze command with invalid confidence threshold."""
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--confidence-threshold', '1.5'
        ])
        
        assert result.exit_code == 1
        assert "Confidence threshold must be between 0 and 1" in result.output
    
    def test_analyze_command_invalid_max_duration(self):
        """Test analyze command with invalid max duration."""
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--max-duration', '-10'
        ])
        
        assert result.exit_code == 1
        assert "Maximum duration must be positive" in result.output
    
    def test_analyze_command_invalid_segment_length(self):
        """Test analyze command with invalid segment length."""
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--segment-length', '0'
        ])
        
        assert result.exit_code == 1
        assert "Segment length must be positive" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_processing_failure(self, mock_asyncio_run):
        """Test analyze command when processing fails."""
        # Mock failed result
        failed_result = Mock()
        failed_result.success = False
        failed_result.error_message = "Failed to download audio"
        
        mock_asyncio_run.return_value = failed_result
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/nonexistent.rss'
        ])
        
        assert result.exit_code == 1
        assert "Analysis failed: Failed to download audio" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_validation_error(self, mock_asyncio_run):
        """Test analyze command with validation error."""
        from media_analyzer.core.exceptions import ValidationError
        
        mock_asyncio_run.side_effect = ValidationError("Invalid podcast URL")
        
        result = self.runner.invoke(cli, [
            'analyze',
            'invalid-url'
        ])
        
        assert result.exit_code == 1
        assert "Validation error: Invalid podcast URL" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_keyboard_interrupt(self, mock_asyncio_run):
        """Test analyze command with keyboard interrupt."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss'
        ])
        
        assert result.exit_code == 1
        assert "Analysis interrupted by user" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_unexpected_error(self, mock_asyncio_run):
        """Test analyze command with unexpected error."""
        mock_asyncio_run.side_effect = Exception("Unexpected error occurred")
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss'
        ])
        
        assert result.exit_code == 1
        assert "Processing failed: Unexpected error occurred" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    @patch('media_analyzer.cli.podcast.console.print_exception')
    def test_analyze_command_unexpected_error_verbose(self, mock_print_exception, mock_asyncio_run):
        """Test analyze command with unexpected error in verbose mode."""
        mock_asyncio_run.side_effect = Exception("Unexpected error occurred")
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--verbose'
        ])
        
        assert result.exit_code == 1
        assert "Processing failed: Unexpected error occurred" in result.output
        mock_print_exception.assert_called_once()
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_analyze_command_skip_subjects(self, mock_asyncio_run):
        """Test analyze command with skip-subjects flag."""
        # Mock result without subjects
        result_no_subjects = Mock()
        result_no_subjects.success = True
        result_no_subjects.episode = self.mock_episode
        result_no_subjects.transcription = self.mock_transcription
        result_no_subjects.subjects = []
        result_no_subjects.processing_metadata = {
            "connector_used": "rss",
            "transcription_service": "whisper",
            "subject_extraction_enabled": False
        }
        
        mock_asyncio_run.return_value = result_no_subjects
        
        result = self.runner.invoke(cli, [
            'analyze',
            'https://example.com/test.rss',
            '--skip-subjects',
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete!" in result.output
        assert "disabled" in result.output  # Should show subject extraction disabled


class TestMetadataCommand:
    """Test the metadata command with comprehensive mocking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Create mock metadata result
        self.mock_metadata = Mock()
        self.mock_metadata.title = "Test Podcast Episode"
        self.mock_metadata.show_name = "Amazing Test Show"
        self.mock_metadata.platform = "rss"
        self.mock_metadata.duration_seconds = 2700  # 45 minutes
        self.mock_metadata.publication_date = datetime(2024, 2, 20, 14, 30)
        self.mock_metadata.author = "Test Podcast Host"
        self.mock_metadata.url = "https://example.com/episode.mp3"
        self.mock_metadata.description = "This is a comprehensive description of the test podcast episode that provides detailed information about the content and topics covered."
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    @patch('media_analyzer.cli.podcast._get_metadata')
    def test_metadata_command_success(self, mock_get_metadata, mock_asyncio_run):
        """Test successful metadata command execution."""
        mock_asyncio_run.return_value = self.mock_metadata
        
        result = self.runner.invoke(cli, [
            'metadata',
            'https://example.com/podcast.rss'
        ])
        
        assert result.exit_code == 0
        assert "Podcast Episode Metadata" in result.output
        assert "Test Podcast Episode" in result.output
        assert "Amazing Test Show" in result.output
        assert "45:00" in result.output  # Duration formatted
        assert "2024-02-20" in result.output  # Publication date
        assert "Test Podcast Host" in result.output
        assert "Metadata extraction complete!" in result.output
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_metadata_command_with_long_description(self, mock_asyncio_run):
        """Test metadata command with long description (truncation)."""
        # Create metadata with very long description
        long_description_metadata = Mock()
        long_description_metadata.title = "Test Episode"
        long_description_metadata.show_name = "Test Show"
        long_description_metadata.platform = "rss"
        long_description_metadata.duration_seconds = 1800
        long_description_metadata.publication_date = datetime(2024, 1, 1)
        long_description_metadata.author = "Host"
        long_description_metadata.url = "https://example.com/test.mp3"
        long_description_metadata.description = "A" * 500  # Very long description
        
        mock_asyncio_run.return_value = long_description_metadata
        
        result = self.runner.invoke(cli, [
            'metadata',
            'https://example.com/podcast.rss'
        ])
        
        assert result.exit_code == 0
        assert "..." in result.output  # Should be truncated
        assert "Metadata extraction complete!" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_metadata_command_minimal_data(self, mock_asyncio_run):
        """Test metadata command with minimal data (no optional fields)."""
        minimal_metadata = Mock()
        minimal_metadata.title = "Basic Episode"
        minimal_metadata.show_name = "Basic Show"
        minimal_metadata.platform = "rss"
        minimal_metadata.duration_seconds = 600  # 10 minutes
        minimal_metadata.publication_date = None  # No publication date
        minimal_metadata.author = None  # No author
        minimal_metadata.url = "https://example.com/basic.mp3"
        minimal_metadata.description = None  # No description
        
        mock_asyncio_run.return_value = minimal_metadata
        
        result = self.runner.invoke(cli, [
            'metadata',
            'https://example.com/basic.rss'
        ])
        
        assert result.exit_code == 0
        assert "Basic Episode" in result.output
        assert "Basic Show" in result.output
        assert "10:00" in result.output  # Duration
        assert "Metadata extraction complete!" in result.output
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_metadata_command_error(self, mock_asyncio_run):
        """Test metadata command with processing error."""
        mock_asyncio_run.side_effect = Exception("Failed to fetch metadata")
        
        result = self.runner.invoke(cli, [
            'metadata',
            'https://example.com/nonexistent.rss'
        ])
        
        assert result.exit_code == 1
        assert "Failed to extract metadata: Failed to fetch metadata" in result.output


class TestAsyncFunctions:
    """Test async helper functions with mocking."""
    
    @patch('media_analyzer.cli.podcast.PodcastAnalyzer')
    def test_analyze_episode_function(self, mock_analyzer_class):
        """Test _analyze_episode async function."""
        from media_analyzer.cli.podcast import _analyze_episode
        
        # Setup mocks
        mock_analyzer = AsyncMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_result = Mock()
        mock_result.success = True
        mock_analyzer.analyze_episode.return_value = mock_result
        
        # Create analysis options
        options = AnalysisOptions(
            language="en",
            transcription_service="whisper",
            subject_extraction=True,
            icon_matching=False,
            max_duration_minutes=180,
            segment_length_seconds=300,
            confidence_threshold=0.5
        )
        
        # Run the async function
        result = asyncio.run(_analyze_episode("https://test.com/rss", options, False))
        
        assert result.success is True
        mock_analyzer.analyze_episode.assert_called_once_with("https://test.com/rss", options)
        mock_analyzer.cleanup.assert_called_once()
    
    @patch('media_analyzer.cli.podcast.PodcastAnalyzer')
    def test_get_metadata_function(self, mock_analyzer_class):
        """Test _get_metadata async function."""
        from media_analyzer.cli.podcast import _get_metadata
        
        # Setup mocks
        mock_analyzer = AsyncMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_metadata = Mock()
        mock_metadata.title = "Test Episode"
        mock_analyzer.get_episode_metadata.return_value = mock_metadata
        
        # Run the async function
        result = asyncio.run(_get_metadata("https://test.com/rss"))
        
        assert result.title == "Test Episode"
        mock_analyzer.get_episode_metadata.assert_called_once_with("https://test.com/rss")
        mock_analyzer.cleanup.assert_called_once()


class TestCLIIntegration:
    """Integration tests for the podcast CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('media_analyzer.cli.podcast.asyncio.run')
    def test_full_workflow_analyze_with_output(self, mock_asyncio_run):
        """Test complete analyze workflow with file output."""
        # Create comprehensive mock result
        mock_episode = Mock()
        mock_episode.title = "Integration Test Episode"
        mock_episode.show_name = "Integration Test Show"
        mock_episode.platform = "rss"
        mock_episode.duration_seconds = 1800
        mock_episode.publication_date = datetime(2024, 3, 1, 9, 0)
        mock_episode.description = "Integration test episode description"
        mock_episode.url = "https://example.com/integration-test.mp3"
        
        mock_transcription = Mock()
        mock_transcription.text = "This is the integration test transcription."
        mock_transcription.language = "en"
        mock_transcription.confidence = 0.88
        mock_transcription.metadata = {"duration": 1800.0, "processing_time": 30.5}
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.episode = mock_episode
        mock_result.transcription = mock_transcription
        mock_result.subjects = []
        mock_result.processing_metadata = {
            "connector_used": "rss",
            "transcription_service": "whisper", 
            "subject_extraction_enabled": False
        }
        
        mock_asyncio_run.return_value = mock_result
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            try:
                result = self.runner.invoke(cli, [
                    'analyze',
                    'https://example.com/integration-test.rss',
                    '--language', 'en',
                    '--max-duration', '60',
                    '--skip-subjects',
                    '--output', tmp_file.name,
                    '--format', 'json',
                    '--verbose'
                ])
                
                # Verify successful execution
                assert result.exit_code == 0
                assert "Results saved to:" in result.output
                assert "Analysis complete!" in result.output
                
                # Verify output file contains expected data
                assert os.path.exists(tmp_file.name)
                with open(tmp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data["episode"]["title"] == "Integration Test Episode"
                    assert data["transcription"]["text"] == "This is the integration test transcription."
                    assert data["subjects"] == []
                    
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
