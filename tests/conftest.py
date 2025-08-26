"""Test configuration and fixtures."""

import pytest
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
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

@pytest.fixture
def test_db_engine():
    """Create PostgreSQL test database engine."""
    # Use environment variable or default test database URL
    test_db_url = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/icon_curator_test"
    )
    engine = create_engine(test_db_url, echo=False)
    yield engine
    engine.dispose()

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_db_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def _ensure_test_dirs():
    """Ensure test data directories exist."""
    AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create test directories on import
_ensure_test_dirs()
