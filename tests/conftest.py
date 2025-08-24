"""Test configuration and fixtures."""

import pytest
from pathlib import Path

# Define test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def test_audio_file():
    """Return path to a test audio file."""
    return TEST_DATA_DIR / "sample.wav"

@pytest.fixture
def test_config():
    """Return test configuration."""
    return {
        "max_audio_duration": 3600,  # 1 hour
        "supported_formats": ["wav", "mp3"],
        "summary_max_length": 500,
    }
