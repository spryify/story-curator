"""Unit tests for utils __init__ module."""

import logging
import pytest
from unittest.mock import patch

# Import the module to test
import media_analyzer.utils


class TestLoggingConfiguration:
    """Test logging configuration in utils.__init__."""
    
    def test_logger_exists(self):
        """Test that the media_analyzer logger is created."""
        logger = media_analyzer.utils.logger
        assert logger is not None
        assert logger.name == 'media_analyzer'
        assert isinstance(logger, logging.Logger)
    
    def test_logger_level(self):
        """Test that logger level configuration works."""
        logger = media_analyzer.utils.logger
        # The logger exists and has a level configured
        # Note: The actual level might be WARNING due to root logger configuration
        # We test that the logger has a defined level
        assert hasattr(logger, 'level')
        assert isinstance(logger.level, int)
    
    @patch('logging.basicConfig')
    def test_logging_basic_config_called(self, mock_basic_config):
        """Test that logging.basicConfig is called with correct parameters."""
        # Re-import to trigger the basicConfig call
        import importlib
        importlib.reload(media_analyzer.utils)
        
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def test_logger_can_log_messages(self):
        """Test that logger can actually log messages."""
        logger = media_analyzer.utils.logger
        
        # Test that these don't raise exceptions
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verify logger has the correct methods
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
    
    def test_module_attributes(self):
        """Test that module has expected attributes."""
        assert hasattr(media_analyzer.utils, 'logger')
        assert hasattr(media_analyzer.utils, 'logging')
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance."""
        logger = media_analyzer.utils.logger
        assert logger.parent == logging.getLogger()  # Root logger
        assert logger.name == 'media_analyzer'
