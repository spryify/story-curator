"""Integrati    test_db_url = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/story_curator_test"
    )est fixtures - uses real dependencies, not mocks."""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db_engine():
    """Create PostgreSQL test database engine for integration tests."""
    # Use environment variable or default test database URL
    test_db_url = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/icon_extractor_test"
    )
    engine = create_engine(test_db_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session for integration tests."""
    TestSession = sessionmaker(bind=test_db_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def icon_repository(test_db_session):
    """Create a real IconRepository with test database session."""
    from src.icon_extractor.database.repository import IconRepository
    return IconRepository(test_db_session)
