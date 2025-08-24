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
        "audio": {
            "model": "base",
            "device": "cpu",
            "sample_rate": 16000,
            "chunk_size": 30,
            "supported_formats": ["wav", "mp3"],
            "max_duration": 3600  # 1 hour
        },
        "text": {
            "max_summary_length": 1000,
            "min_confidence": 0.8,
            "language": "en"
        }
    }
