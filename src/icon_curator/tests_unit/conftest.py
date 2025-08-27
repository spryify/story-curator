"""Icon curator specific test fixtures."""

import pytest
from unittest.mock import Mock
from datetime import datetime
from typing import List
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.icon_curator.models.icon import IconData, ScrapingResult
from src.icon_curator.database.models import IconModel


@pytest.fixture
def sample_icon_data() -> IconData:
    """Create sample icon data for testing."""
    return IconData(
        name="Test Icon",
        url="https://yotoicons.com/images/test-icon.svg",
        tags=["test", "sample"],
        description="A test icon for unit tests",
        category="Testing",
        metadata={"source": "test"}
    )


@pytest.fixture
def sample_icon_data_list() -> List[IconData]:
    """Create a list of sample icon data for testing."""
    return [
        IconData(
            name="Icon One",
            url="https://yotoicons.com/images/icon-one.svg",
            tags=["animals", "cute"],
            description="First test icon",
            category="Animals"
        ),
        IconData(
            name="Icon Two", 
            url="https://yotoicons.com/images/icon-two.svg",
            tags=["nature", "plants"],
            description="Second test icon",
            category="Nature"
        ),
        IconData(
            name="Icon Three",
            url="https://yotoicons.com/images/icon-three.svg",
            tags=["vehicles", "transport"],
            description="Third test icon",
            category="Transport"
        )
    ]


@pytest.fixture
def sample_scraping_result() -> ScrapingResult:
    """Create sample scraping result for testing."""
    return ScrapingResult(
        total_icons=10,
        successful_scraped=8,
        failed_scraped=2,
        errors=["Failed to parse icon X", "Network timeout for icon Y"],
        processing_time=45.5,
        timestamp=datetime(2025, 8, 26, 10, 30, 0),
        icons=[]  # Add empty icons list for now
    )


@pytest.fixture
def sample_icon_model() -> IconModel:
    """Create sample icon model for testing."""
    return IconModel(
        id=1,
        name="Model Test Icon",
        url="https://yotoicons.com/images/model-test.svg",
        tags=["model", "test"],
        description="Test icon model",
        category="Testing",
        metadata={"test": "data"}
    )


@pytest.fixture
def mock_icon_repository():
    """Create a mock IconRepository for unit testing."""
    return Mock()


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
