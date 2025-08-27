"""Unit tests for CLI interface."""

import os
import pytest
from unittest.mock import Mock, patch
import sys
from io import StringIO

from src.icon_extractor.cli.main import (
    create_parser, 
    main,
    scrape_command,
    search_command,
    stats_command
)
from src.icon_extractor.models.icon import IconData, ScrapingResult
from src.icon_extractor.core.exceptions import IconCuratorError


class TestCLIParser:
    """Test cases for CLI argument parser."""
    
    def test_parser_creation(self):
        """Test creating the argument parser."""
        parser = create_parser()
        
        assert parser.prog == 'icon-curator'
        assert 'Yoto Icons Database Management Tool' in parser.description
    
    def test_scrape_command_parser(self):
        """Test scrape command parser."""
        parser = create_parser()
        
        # Test basic scrape command
        args = parser.parse_args(['scrape'])
        assert args.command == 'scrape'
        assert args.force_update is False
        
        # Test scrape with force update
        args = parser.parse_args(['scrape', '--force-update'])
        assert args.command == 'scrape'
        assert args.force_update is True
    
    def test_search_command_parser(self):
        """Test search command parser."""
        parser = create_parser()
        
        # Test basic search
        args = parser.parse_args(['search', 'test query'])
        assert args.command == 'search'
        assert args.query == 'test query'
        assert args.category is None
        assert args.tags is None
        assert args.limit == 50
        
        # Test search with all options
        args = parser.parse_args([
            'search', 'test query',
            '--category', 'Animals',
            '--tags', 'cute,fluffy',
            '--limit', '25'
        ])
        assert args.command == 'search'
        assert args.query == 'test query'
        assert args.category == 'Animals'
        assert args.tags == 'cute,fluffy'
        assert args.limit == 25
    
    def test_stats_command_parser(self):
        """Test stats command parser."""
        parser = create_parser()
        
        args = parser.parse_args(['stats'])
        assert args.command == 'stats'
    
    def test_verbose_flag(self):
        """Test verbose flag parsing."""
        parser = create_parser()
        
        # Test without verbose
        args = parser.parse_args(['stats'])
        assert args.verbose is False
        
        # Test with verbose short form
        args = parser.parse_args(['-v', 'stats'])
        assert args.verbose is True
        
        # Test with verbose long form
        args = parser.parse_args(['--verbose', 'stats'])
        assert args.verbose is True


class TestCLICommands:
    """Test cases for CLI command functions."""
    
    @patch.dict(os.environ, {'ICON_EXTRACTOR_DEMO': 'false'})
    @patch('src.icon_extractor.cli.main.IconService')
    def test_scrape_command_success(self, mock_service_class):
        """Test successful scrape command execution."""
        # Mock service and its methods
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock scraping result
        mock_result = Mock()
        mock_result.total_icons = 100
        mock_result.successful_scraped = 85
        mock_result.failed_scraped = 15
        mock_result.success_rate = 85.0
        mock_result.processing_time = 60.5
        mock_result.errors = []

        mock_service.scrape_and_store_icons.return_value = mock_result

        # Create mock args (no demo mode)
        args = Mock()
        args.force_update = False
        args.demo = False
        args.category = None
        args.max_pages = None

        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = scrape_command(args)

        assert result == 0
        mock_service.scrape_and_store_icons.assert_called_once_with(force_update=False, category=None, max_pages=None)
        
        output = fake_stdout.getvalue()
        assert "Starting icon scraping" in output
        assert "Total icons found: 100" in output
        assert "Successfully scraped: 85" in output
    
    @patch.dict(os.environ, {'ICON_EXTRACTOR_DEMO': 'false'})
    @patch('src.icon_extractor.cli.main.IconService')
    def test_scrape_command_with_errors(self, mock_service_class):
        """Test scrape command with errors."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        mock_result = Mock()
        mock_result.total_icons = 10
        mock_result.successful_scraped = 8
        mock_result.failed_scraped = 2
        mock_result.success_rate = 80.0
        mock_result.processing_time = 15.0
        mock_result.errors = ["Error 1", "Error 2"]

        mock_service.scrape_and_store_icons.return_value = mock_result

        args = Mock()
        args.force_update = True
        args.demo = False
        args.category = None
        args.max_pages = None

        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = scrape_command(args)

        assert result == 0
        mock_service.scrape_and_store_icons.assert_called_once_with(force_update=True, category=None, max_pages=None)
        
        output = fake_stdout.getvalue()
        assert "Errors encountered (2)" in output
        assert "Error 1" in output
        assert "Error 2" in output
    
    @patch.dict(os.environ, {'ICON_EXTRACTOR_DEMO': 'false'})
    @patch('src.icon_extractor.cli.main.IconService')
    def test_scrape_command_failure(self, mock_service_class):
        """Test scrape command failure."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        from src.icon_extractor.core.exceptions import IconCuratorError
        mock_service.scrape_and_store_icons.side_effect = IconCuratorError("Scraping failed")
        
        args = Mock()
        args.force_update = False
        args.demo = False
        
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            result = scrape_command(args)
        
        assert result == 1
        
        output = fake_stderr.getvalue()
        assert "Error: Scraping failed" in output
    
    @patch('src.icon_extractor.cli.main.IconService')
    def test_search_command_success(self, mock_service_class):
        """Test successful search command."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock search results
        mock_icons = [
            IconData(
                name="Test Icon 1",
                url="https://example.com/1",
                tags=["test", "icon"],
                description="First test icon",
                category="Testing"
            ),
            IconData(
                name="Test Icon 2",
                url="https://example.com/2",
                tags=["test"],
                description="Second test icon",
                category="Testing"
            )
        ]
        
        mock_service.search_icons.return_value = mock_icons
        
        args = Mock()
        args.query = "test"
        args.category = "Testing"
        args.tags = "test,icon"
        args.limit = 50
        
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = search_command(args)
        
        assert result == 0
        mock_service.search_icons.assert_called_once_with(
            query="test",
            category="Testing",
            tags=["test", "icon"],
            limit=50
        )
        
        output = fake_stdout.getvalue()
        assert "Found 2 icons" in output
        assert "Test Icon 1" in output
        assert "Test Icon 2" in output
    
    @patch('src.icon_extractor.cli.main.IconService')
    def test_search_command_no_results(self, mock_service_class):
        """Test search command with no results."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_service.search_icons.return_value = []
        
        args = Mock()
        args.query = "nonexistent"
        args.category = None
        args.tags = None
        args.limit = 50
        
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = search_command(args)
        
        assert result == 0
        
        output = fake_stdout.getvalue()
        assert "No icons found matching the criteria" in output
    
    @patch('src.icon_extractor.cli.main.IconService')
    def test_stats_command_success(self, mock_service_class):
        """Test successful stats command."""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_stats = {
            'total_icons': 150,
            'total_categories': 10,
            'total_tags': 45,
            'categories': ['Animals', 'Nature', 'Transport'],
            'tags': ['cute', 'fluffy', 'green', 'fast', 'red']
        }
        
        mock_service.get_statistics.return_value = mock_stats
        
        args = Mock()
        
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = stats_command(args)
        
        assert result == 0
        
        output = fake_stdout.getvalue()
        assert "Total Icons: 150" in output
        assert "Total Categories: 10" in output
        assert "Total Tags: 45" in output
        assert "Animals" in output
        assert "cute" in output


class TestMainFunction:
    """Test cases for main entry point."""
    
    def test_main_no_command(self):
        """Test main function with no command."""
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            result = main([])
        
        assert result == 1
        # Should print help when no command provided
        output = fake_stdout.getvalue()
        assert "usage:" in output.lower() or "help" in output.lower()
    
    @patch('src.icon_extractor.cli.main.scrape_command')
    def test_main_with_scrape_command(self, mock_scrape_command):
        """Test main function with scrape command."""
        mock_scrape_command.return_value = 0
        
        result = main(['scrape'])
        
        assert result == 0
        mock_scrape_command.assert_called_once()
    
    @patch('src.icon_extractor.cli.main.search_command')
    def test_main_with_search_command(self, mock_search_command):
        """Test main function with search command."""
        mock_search_command.return_value = 0
        
        result = main(['search', 'test'])
        
        assert result == 0
        mock_search_command.assert_called_once()
    
    @patch('src.icon_extractor.cli.main.stats_command')
    def test_main_with_stats_command(self, mock_stats_command):
        """Test main function with stats command."""
        mock_stats_command.return_value = 0
        
        result = main(['stats'])
        
        assert result == 0
        mock_stats_command.assert_called_once()
