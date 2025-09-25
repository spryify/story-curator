"""Global test configuration and fixtures."""

import pytest
import pytest_asyncio
import asyncio
import time
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Define test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"


def pytest_configure(config):
    """Configure pytest before test collection.

    Args:
        config (pytest.Config): The pytest configuration object representing the test session's configuration and state.
            This object can be used to access and modify pytest's configuration, plugins, and command-line options.
    """
    # Ensure test data directories exist
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set up mocking for CI environments
    _setup_ci_mocks()


def _setup_ci_mocks():
    """Set up CI environment mocks for external dependencies."""
    # In CI environments, always mock dependencies unless explicitly running integration tests
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    explicit_integration = os.environ.get("TESTING_INTEGRATION") == "true"
    
    # Mock in CI unless it's explicitly an integration test
    should_mock = is_ci and not explicit_integration
    
    if not should_mock:
        return
    
    _setup_spacy_mocks()
    _setup_whisper_mocks()


def _setup_spacy_mocks():
    """Set up comprehensive spaCy mocks."""
    # First, remove any existing spaCy modules from sys.modules to force our mocks
    spacy_modules_to_remove = [key for key in sys.modules.keys() if key.startswith('spacy') or key == 'en_core_web_sm']
    for module_name in spacy_modules_to_remove:
        sys.modules.pop(module_name, None)
    
    # Create a mock factory decorator that just returns the function
    def mock_factory(name, **kwargs):  # pylint: disable=unused-argument
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
    mock_spacy.__version__ = "3.8.7"  # Add version for compatibility
    
    # Create spacy.language module mock
    mock_spacy_language = Mock()
    mock_spacy_language.Language = mock_language
    
    # Create spacy.lang.en module mock with English class
    mock_spacy_lang_en = Mock()
    mock_spacy_lang_en.English = mock_english
    
    # Pre-populate sys.modules to prevent real spaCy imports
    sys.modules['spacy'] = mock_spacy
    sys.modules['spacy.language'] = mock_spacy_language
    sys.modules['spacy.lang'] = Mock()
    sys.modules['spacy.lang.en'] = mock_spacy_lang_en
    sys.modules['spacy.util'] = Mock()
    sys.modules['spacy.cli'] = Mock()
    sys.modules['spacy.tokens'] = Mock()
    sys.modules['spacy.pipeline'] = Mock()
    sys.modules['spacy.training'] = Mock()
    sys.modules['spacy.scorer'] = Mock()
    sys.modules['en_core_web_sm'] = Mock()
    
    # Also add the English class to the language module directly
    mock_spacy_lang_en.English.factory = mock_factory


def _setup_whisper_mocks():
    """Set up comprehensive Whisper mocks."""
    # First, remove any existing Whisper modules from sys.modules to force our mocks
    whisper_modules_to_remove = [key for key in sys.modules.keys() if key.startswith('whisper')]
    for module_name in whisper_modules_to_remove:
        sys.modules.pop(module_name, None)
    
    mock_whisper_model = Mock()
    mock_whisper_model.transcribe = Mock(return_value={'text': 'test transcription'})
    
    mock_whisper = Mock()
    mock_whisper.load_model = Mock(return_value=mock_whisper_model)
    mock_whisper.__version__ = "20231117"  # Add version for compatibility
    
    # Pre-populate sys.modules to prevent real Whisper imports
    sys.modules['whisper'] = mock_whisper


def pytest_collection_modifyitems(config, items):
    """Modify test items to ensure proper asyncio handling."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


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


def _setup_ci_mocks_at_import():
    """Set up CI environment mocks at import time - earliest possible."""
    # In CI environments, always mock dependencies unless explicitly running integration tests
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    explicit_integration = os.environ.get("TESTING_INTEGRATION") == "true"
    
    # Mock in CI unless it's explicitly an integration test
    should_mock = is_ci and not explicit_integration
    
    if not should_mock:
        return
    
    _setup_spacy_mocks()
    _setup_whisper_mocks()


# Set up CI mocks immediately at import time, before any other imports
_setup_ci_mocks_at_import()
