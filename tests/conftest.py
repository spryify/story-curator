"""Test configuration and fixtures."""

import pytest
from pathlib import Path

# Define test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"

def pytest_configure():
    """Configure pytest."""
    # Ensure test data directories exist
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Move audio files under a dedicated audio subdirectory
AUDIO_DATA_DIR = TEST_DATA_DIR / "audio"

def pytest_configure():
    """Configure pytest before test collection."""
    # Ensure test data directories exist
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)

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

def _ensure_test_dirs():
    """Ensure test data directories exist."""
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create test directories on import
_ensure_test_dirs()
