"""Integration test configuration and fixtures."""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os

from audio_icon_matcher.tests_unit.conftest import (
    sample_transcription_result,
    sample_subject_analysis_result,
    sample_icon_data,
    sample_icon_matches,
    subjects_dict,
    assert_valid_audio_icon_result,
    assert_valid_icon_match,
    create_test_audio_file,
    cleanup_test_file
)


@pytest.fixture(scope="session")
def integration_test_setup():
    """Set up integration test environment."""
    # This could include database setup, model loading, etc.
    # For now, we'll just ensure the environment is ready
    yield
    # Cleanup after all integration tests


@pytest.fixture
def mocked_dependencies():
    """Mock all external dependencies for integration tests."""
    with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
         patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
         patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
        
        # Set up audio processor mock
        mock_audio = Mock()
        mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
        mock_audio.validate_file.return_value = "/test/audio.wav"
        mock_audio.extract_text.return_value = Mock(
            text="Test audio content",
            language="en",
            confidence=0.9
        )
        mock_audio_class.return_value = mock_audio
        
        # Set up subject identifier mock
        mock_subject = Mock()
        mock_subject_result = Mock()
        mock_subject_result.subjects = set()
        mock_subject_result.categories = set()
        mock_subject_result.metadata = {}
        mock_subject.identify_subjects.return_value = mock_subject_result
        mock_subject_class.return_value = mock_subject
        
        # Set up icon service mock
        mock_icon_service = Mock()
        mock_icon_service.search_icons.return_value = []
        mock_icon_service_class.return_value = mock_icon_service
        
        yield {
            'audio_processor': mock_audio,
            'subject_identifier': mock_subject,
            'icon_service': mock_icon_service
        }


@pytest.fixture
def realistic_audio_scenarios():
    """Provide realistic audio processing scenarios."""
    scenarios = {
        'music': {
            'transcription': "Beautiful jazz piano with smooth saxophone melodies",
            'subjects': ['jazz', 'piano', 'saxophone', 'music'],
            'expected_icons': ['piano', 'music', 'jazz']
        },
        'nature': {
            'transcription': "Birds singing in the forest with water flowing",
            'subjects': ['birds', 'forest', 'water', 'nature'],
            'expected_icons': ['bird', 'tree', 'nature']
        },
        'sports': {
            'transcription': "Football game with crowd cheering and commentary",
            'subjects': ['football', 'sports', 'game', 'crowd'],
            'expected_icons': ['football', 'sports', 'stadium']
        },
        'cooking': {
            'transcription': "Cooking pasta with garlic and herbs sizzling in the pan",
            'subjects': ['cooking', 'pasta', 'garlic', 'herbs', 'food'],
            'expected_icons': ['cooking', 'food', 'chef', 'kitchen']
        }
    }
    return scenarios


# Integration test markers
integration = pytest.mark.integration
performance = pytest.mark.performance
slow = pytest.mark.slow
