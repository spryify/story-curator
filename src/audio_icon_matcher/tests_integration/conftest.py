"""Integration test configuration and fixtures."""

import pytest
import tempfile
import os


@pytest.fixture(scope="session")
def integration_test_setup():
    """Set up integration test environment."""
    # This could include database setup, model loading, etc.
    # For now, we'll just ensure the environment is ready
    yield
    # Cleanup after all integration tests


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
