"""Global test configuration and fixtures."""

import pytest
import pytest_asyncio
import asyncio
import time
from pathlib import Path

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
