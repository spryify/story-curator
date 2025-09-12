"""Pytest plugin to mock spaCy at import time for CI compatibility."""

import sys
import os
from unittest.mock import Mock


def pytest_configure(config):
    """Configure spaCy mocking before any imports happen.
    
    Args:
        config: pytest configuration object (required by pytest hook)
    """
    # Mock for unit tests, not integration tests - matching original conftest.py logic
    should_mock = (
        os.environ.get("PYTEST_CURRENT_TEST", "").find("unit") != -1 or 
        not os.environ.get("TESTING_INTEGRATION", False)
    )
    
    if should_mock:
        _setup_spacy_mocks()


def _setup_spacy_mocks():
    """Set up comprehensive spaCy mocks before any imports."""
    # Create a mock factory decorator that just returns the function
    def mock_factory(name, **kwargs):  # pylint: disable=unused-argument
        """Mock factory decorator.
        
        Args:
            name: factory name (unused but required for compatibility)
            **kwargs: factory kwargs (unused but required for compatibility)
        """
        def decorator(func):
            return func
        return decorator
    
    mock_language = Mock()
    mock_language.factory = mock_factory
    
    # Create mock English class with factory method
    mock_english = Mock()
    mock_english.factory = mock_factory
    
    mock_token = Mock()
    mock_token.text = "test"
    mock_token.pos_ = "NOUN"
    mock_token.is_stop = False
    mock_token.is_space = False
    mock_token.is_alpha = True
    mock_token.label_ = "ORG"
    
    mock_doc = Mock()
    mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
    mock_doc.__len__ = Mock(return_value=1)
    mock_doc.noun_chunks = []
    mock_doc.ents = [mock_token]
    
    mock_nlp = Mock()
    mock_nlp.return_value = mock_doc
    mock_nlp.select_pipes = Mock()
    
    # Create the main spaCy module mock
    mock_spacy = Mock()
    mock_spacy.load = Mock(return_value=mock_nlp)
    mock_spacy.Language = mock_language
    
    # Create spacy.language module mock
    mock_spacy_language = Mock()
    mock_spacy_language.Language = mock_language
    
    # Create spacy.lang.en module mock with English class
    mock_spacy_lang_en = Mock()
    mock_spacy_lang_en.English = mock_english
    
    # Pre-populate sys.modules to prevent real imports
    sys.modules['spacy'] = mock_spacy
    sys.modules['spacy.language'] = mock_spacy_language
    sys.modules['spacy.lang'] = Mock()
    sys.modules['spacy.lang.en'] = mock_spacy_lang_en
    sys.modules['spacy.util'] = Mock()
    sys.modules['spacy.cli'] = Mock()
    sys.modules['spacy.tokens'] = Mock()
    sys.modules['en_core_web_sm'] = Mock()
