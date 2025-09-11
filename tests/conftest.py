"""Global test configuration and fixtures."""

import pytest
import pytest_asyncio
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Define test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"


def pytest_configure():
    """Configure pytest before test collection."""
    # Ensure test data directories exist
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """Modify test items to ensure proper asyncio handling."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope="session", autouse=True)
def mock_spacy_for_unit_tests():
    """Mock spaCy for all unit tests to avoid dependency on model downloads."""
    # Only mock for unit tests, not integration tests
    import os
    import sys
    
    if os.environ.get("PYTEST_CURRENT_TEST", "").find("unit") != -1 or not os.environ.get("TESTING_INTEGRATION", False):
        # Create comprehensive spaCy mocks
        
        # Create a mock factory decorator that just returns the function
        def mock_factory(name, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        mock_language = Mock()
        mock_language.factory = mock_factory
        
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
        
        # Patch the entire spaCy module ecosystem
        with patch.dict('sys.modules', {
            'spacy': mock_spacy,
            'spacy.language': mock_spacy_language,
            'spacy.util': Mock(),
            'spacy.cli': Mock(),
            'spacy.tokens': Mock()
        }):
            yield
    else:
        # For integration tests, don't mock spaCy
        yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_resources():
    """Automatically cleanup resources after each test session"""
    yield
    
    # Give time for async cleanup to complete
    time.sleep(1.0)


def _ensure_test_dirs():
    """Ensure test data directories exist."""
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)


# Create test directories on import
_ensure_test_dirs()
