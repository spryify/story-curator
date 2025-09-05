"""Unit tests for CLI commands."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from audio_icon_matcher.cli.main import (
    audio_icon_matcher_commands,
    find_matching_icons,
    validate_audio_source,
    list_supported_formats,
    show_info,
    _output_results,
    _format_json_output,
    _format_table_output,
    _format_summary_output
)
from audio_icon_matcher.models.results import AudioIconResult, IconMatch
from audio_icon_matcher.core.exceptions import AudioIconValidationError, AudioIconProcessingError


class TestCLICommands:
    """Test CLI command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Mock pipeline with successful result
        self.mock_pipeline = Mock()
        self.mock_result = AudioIconResult(
            success=True,
            transcription="Test transcription",
            transcription_confidence=0.95,
            subjects={'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]},
            icon_matches=[],
            processing_time=1.5,
            metadata={'source_type': 'local_file', 'audio_file': 'test.mp3'}
        )
        self.mock_pipeline.process.return_value = self.mock_result
        self.mock_pipeline.validate_audio_file.return_value = True
        self.mock_pipeline.validate_podcast_url.return_value = True
        self.mock_pipeline.get_supported_formats.return_value = ['mp3', 'wav', 'm4a']
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_local_file_success(self, mock_pipeline_class):
        """Test find-icons command with local file."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        with self.runner.isolated_filesystem():
            # Create a test file
            Path('test.mp3').touch()
            
            result = self.runner.invoke(
                audio_icon_matcher_commands, 
                ['find-icons', 'test.mp3']
            )
            
            assert result.exit_code == 0
            assert "Finding icons for audio file: test.mp3" in result.output
            self.mock_pipeline.process.assert_called_once()
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_podcast_url_success(self, mock_pipeline_class):
        """Test find-icons command with podcast URL."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['find-icons', 'https://podcast.example.com/episode.rss']
        )
        
        assert result.exit_code == 0
        assert "Finding icons for podcast episode" in result.output
        self.mock_pipeline.process.assert_called_once()
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_file_not_found(self, mock_pipeline_class):
        """Test find-icons command with non-existent file."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['find-icons', 'nonexistent.mp3']
        )
        
        assert result.exit_code == 1
        assert "Audio file not found" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_invalid_podcast_url(self, mock_pipeline_class):
        """Test find-icons command with invalid podcast URL."""
        self.mock_pipeline.validate_podcast_url.return_value = False
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['find-icons', 'https://invalid-podcast.com']
        )
        
        assert result.exit_code == 1
        assert "Invalid or unsupported podcast URL" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_with_options(self, mock_pipeline_class):
        """Test find-icons command with custom options."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        with self.runner.isolated_filesystem():
            Path('test.wav').touch()
            
            result = self.runner.invoke(
                audio_icon_matcher_commands,
                [
                    'find-icons', 'test.wav',
                    '--max-icons', '5',
                    '--confidence-threshold', '0.5',
                    '--output-format', 'json'
                ]
            )
            
            assert result.exit_code == 0
            self.mock_pipeline.process.assert_called_once_with(
                'test.wav',
                max_icons=5,
                confidence_threshold=0.5,
                episode_index=0,
                episode_title=None,
                max_duration_minutes=30
            )
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_output_to_file(self, mock_pipeline_class):
        """Test find-icons command with file output."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        with self.runner.isolated_filesystem():
            Path('test.mp3').touch()
            
            result = self.runner.invoke(
                audio_icon_matcher_commands,
                [
                    'find-icons', 'test.mp3',
                    '--output-file', 'results.json',
                    '--output-format', 'json'
                ]
            )
            
            assert result.exit_code == 0
            assert "Results written to results.json" in result.output
            assert Path('results.json').exists()
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_find_icons_processing_error(self, mock_pipeline_class):
        """Test find-icons command with processing error."""
        self.mock_pipeline.process.side_effect = AudioIconProcessingError("Processing failed")
        mock_pipeline_class.return_value = self.mock_pipeline
        
        with self.runner.isolated_filesystem():
            Path('test.mp3').touch()
            
            result = self.runner.invoke(
                audio_icon_matcher_commands,
                ['find-icons', 'test.mp3']
            )
            
            assert result.exit_code == 1
            assert "Processing Error" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_validate_command_local_file_valid(self, mock_pipeline_class):
        """Test validate command with valid local file."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['validate', 'test.mp3']
        )
        
        assert result.exit_code == 0
        assert "✅ Valid audio file" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_validate_command_podcast_url_valid(self, mock_pipeline_class):
        """Test validate command with valid podcast URL."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['validate', 'https://podcast.example.com/feed.rss']
        )
        
        assert result.exit_code == 0
        assert "✅ Valid podcast URL" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_validate_command_invalid_file(self, mock_pipeline_class):
        """Test validate command with invalid file."""
        self.mock_pipeline.validate_audio_file.return_value = False
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['validate', 'invalid.mp3']
        )
        
        assert result.exit_code == 1
        assert "❌ Invalid audio file" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_formats_command(self, mock_pipeline_class):
        """Test formats command."""
        mock_pipeline_class.return_value = self.mock_pipeline
        
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['formats']
        )
        
        assert result.exit_code == 0
        assert "SUPPORTED AUDIO FORMATS" in result.output
        assert "• .mp3" in result.output
        assert "SUPPORTED PODCAST SOURCES" in result.output
    
    def test_info_command(self):
        """Test info command."""
        result = self.runner.invoke(
            audio_icon_matcher_commands,
            ['info']
        )
        
        assert result.exit_code == 0
        assert "AUDIO-ICON MATCHER" in result.output
        assert "find-icons" in result.output
        assert "EXAMPLES:" in result.output


class TestOutputFormatting:
    """Test output formatting functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock icon and match
        self.mock_icon = Mock()
        self.mock_icon.name = "test-icon"
        self.mock_icon.url = "https://example.com/icon.svg"
        self.mock_icon.category = "test"
        self.mock_icon.tags = ["tag1", "tag2"]
        
        self.mock_match = IconMatch(
            icon=self.mock_icon,
            confidence=0.85,
            match_reason="keyword match",
            subjects_matched=["test subject"]
        )
        
        # Create test result
        self.test_result = AudioIconResult(
            success=True,
            transcription="Test transcription content",
            transcription_confidence=0.95,
            subjects={
                'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}],
                'topics': [{'name': 'testing', 'confidence': 0.7, 'type': 'TOPIC'}]
            },
            icon_matches=[self.mock_match],
            processing_time=2.5,
            metadata={
                'source_type': 'local_file',
                'audio_file': 'test.mp3',
                'max_icons_requested': 10
            }
        )
    
    def test_format_json_output_success(self):
        """Test JSON output formatting for successful result."""
        output = _format_json_output(self.test_result)
        
        assert output is not None
        data = json.loads(output)
        
        assert data['success'] is True
        assert data['transcription'] == "Test transcription content"
        assert data['transcription_confidence'] == 0.95
        assert len(data['icon_matches']) == 1
        assert data['icon_matches'][0]['icon_name'] == "test-icon"
        assert data['icon_matches'][0]['confidence'] == 0.85
    
    def test_format_json_output_error(self):
        """Test JSON output formatting for error result."""
        error_result = AudioIconResult(
            success=False,
            error="Test error message",
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=0.5,
            metadata={'source_type': 'local_file'}
        )
        
        output = _format_json_output(error_result)
        data = json.loads(output)
        
        assert data['success'] is False
        assert data['error'] == "Test error message"
        assert len(data['icon_matches']) == 0
    
    def test_format_table_output_success(self):
        """Test table output formatting for successful result."""
        output = _format_table_output(self.test_result)
        
        assert "AUDIO TO ICON PROCESSING RESULTS" in output
        assert "Success: ✓" in output
        assert "Source: Local Audio File" in output
        assert "test.mp3" in output
        assert "Test transcription" in output
        assert "SUBJECTS IDENTIFIED:" in output
        assert "ICON MATCHES FOUND (1):" in output
        assert "test-icon" in output
    
    def test_format_table_output_podcast(self):
        """Test table output formatting for podcast result."""
        podcast_result = AudioIconResult(
            success=True,
            transcription="Podcast content",
            transcription_confidence=0.9,
            subjects={'keywords': [{'name': 'podcast', 'confidence': 0.8, 'type': 'KEYWORD'}]},
            icon_matches=[],
            processing_time=3.0,
            metadata={
                'source_type': 'podcast',
                'episode_title': 'Test Episode',
                'show_name': 'Test Show'
            }
        )
        
        output = _format_table_output(podcast_result)
        
        assert "Source: Podcast URL" in output
        assert "Episode: Test Episode" in output
        assert "Show: Test Show" in output
    
    def test_format_summary_output_success(self):
        """Test summary output formatting."""
        output = _format_summary_output(self.test_result)
        
        assert "AUDIO-TO-ICON PROCESSING SUCCESS (LOCAL FILE)" in output
        assert "Processing time: 2.50s" in output
        assert "Transcription confidence: 0.95" in output
        assert "Subjects found: 2" in output
        assert "Icon matches: 1" in output
        assert "test-icon" in output
    
    def test_format_summary_output_error(self):
        """Test summary output formatting for error."""
        error_result = AudioIconResult(
            success=False,
            error="Test error",
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=0.5,
            metadata={'source_type': 'local_file'}
        )
        
        output = _format_summary_output(error_result)
        
        assert "AUDIO-TO-ICON PROCESSING FAILED" in output
        assert "Error: Test error" in output
    
    def test_output_results_to_stdout(self, capsys):
        """Test output results to stdout."""
        _output_results(self.test_result, "summary")
        
        captured = capsys.readouterr()
        assert "AUDIO-TO-ICON PROCESSING SUCCESS" in captured.out
    
    def test_output_results_to_file(self):
        """Test output results to file."""
        with CliRunner().isolated_filesystem():
            output_file = Path('test_output.json')
            _output_results(self.test_result, "json", output_file)
            
            assert output_file.exists()
            with open(output_file) as f:
                data = json.load(f)
                assert data['success'] is True


class TestCLIHelp:
    """Test CLI help and command interface scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main help command."""
        result = self.runner.invoke(audio_icon_matcher_commands, ['--help'])
        
        assert result.exit_code == 0
        assert "Audio-icon matcher commands" in result.output
        assert "find-icons" in result.output
        assert "validate" in result.output
        assert "formats" in result.output
        assert "info" in result.output
    
    def test_find_icons_help(self):
        """Test find-icons help command."""
        result = self.runner.invoke(audio_icon_matcher_commands, ['find-icons', '--help'])
        
        assert result.exit_code == 0
        assert "Find matching icons for audio source" in result.output
        assert "AUDIO_SOURCE can be:" in result.output
        assert "--max-icons" in result.output
        assert "--confidence-threshold" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_formats_command_error_handling(self, mock_pipeline_class):
        """Test formats command error handling."""
        mock_pipeline = Mock()
        mock_pipeline.get_supported_formats.side_effect = RuntimeError("Test error")
        mock_pipeline_class.return_value = mock_pipeline
        
        result = self.runner.invoke(audio_icon_matcher_commands, ['formats'])
        
        assert result.exit_code == 1
        assert "❌ Error getting formats" in result.output
    
    @patch('audio_icon_matcher.cli.main.AudioIconPipeline')
    def test_validate_command_exception_handling(self, mock_pipeline_class):
        """Test validate command exception handling."""
        mock_pipeline = Mock()
        mock_pipeline.validate_audio_file.side_effect = ValueError("Validation error")
        mock_pipeline_class.return_value = mock_pipeline
        
        result = self.runner.invoke(audio_icon_matcher_commands, ['validate', 'test.mp3'])
        
        assert result.exit_code == 1
        assert "❌ Validation error" in result.output


class TestOutputFormattingEdgeCases:
    """Test edge cases in output formatting."""
    
    def test_format_table_output_no_subjects(self):
        """Test table formatting with no subjects."""
        result = AudioIconResult(
            success=True,
            transcription="Test",
            transcription_confidence=0.9,
            subjects={},
            icon_matches=[],
            processing_time=1.0,
            metadata={'source_type': 'local_file'}
        )
        
        output = _format_table_output(result)
        assert "No icon matches found" in output
    
    def test_format_table_output_error_result(self):
        """Test table formatting with error result."""
        result = AudioIconResult(
            success=False,
            error="Test error message",
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=0.5,
            metadata={'source_type': 'local_file'}
        )
        
        output = _format_table_output(result)
        assert "Success: ✗" in output
        assert "Error: Test error message" in output
    
    def test_format_json_output_with_rich_subjects(self):
        """Test JSON formatting with rich subject metadata."""
        result = AudioIconResult(
            success=True,
            transcription="Test",
            transcription_confidence=0.9,
            subjects={
                'keywords': [
                    {
                        'name': 'test',
                        'confidence': 0.8,
                        'type': 'KEYWORD',
                        'context': {'domain': 'tech', 'language': 'en'}
                    }
                ]
            },
            icon_matches=[],
            processing_time=1.0,
            metadata={'source_type': 'local_file'}
        )
        
        output = _format_json_output(result)
        data = json.loads(output)
        
        assert data['subjects']['keywords'][0]['context']['domain'] == 'tech'
        assert data['subjects']['keywords'][0]['type'] == 'KEYWORD'
