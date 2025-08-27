"""Shared test fixtures and configuration for icon curator integration tests."""

import os
import pytest
from datetime import datetime
from typing import List
from unittest.mock import Mock

from src.icon_curator.models.icon import IconData, ScrapingResult
from src.icon_curator.processors.scraper import YotoIconScraper


# Live test configuration
SKIP_LIVE_TESTS = os.getenv('SKIP_LIVE_TESTS', 'false').lower() == 'true'
skip_live = pytest.mark.skipif(SKIP_LIVE_TESTS, reason="Live tests disabled")

# Database integration tests require PostgreSQL setup
SKIP_DATABASE_TESTS = os.getenv('SKIP_DATABASE_TESTS', 'true').lower() == 'true'
skip_database = pytest.mark.skipif(SKIP_DATABASE_TESTS, reason="Database integration tests require PostgreSQL setup")


# Mock database fixtures (no actual database connection needed)
@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing database interactions without a real DB."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.query = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_icon_repository(mock_db_session):
    """Create a mock repository instance for testing without database dependencies."""
    repository = Mock()
    repository.session = mock_db_session
    
    # Setup common mock return values
    repository.save_icon = Mock()
    repository.get_icon_by_id = Mock()
    repository.get_icon_by_url = Mock()
    repository.search_icons = Mock(return_value=[])
    repository.get_all_categories = Mock(return_value=[])
    repository.get_icon_count = Mock(return_value=0)
    repository.delete_icon = Mock(return_value=True)
    
    return repository


# Data fixtures
@pytest.fixture
def sample_icon_data() -> IconData:
    """Create sample icon data for testing."""
    return IconData(
        name="Test Icon",
        url="https://yotoicons.com/images/test-icon.svg",
        tags=["test", "sample"],
        description="A test icon for integration tests",
        category="Testing",
        metadata={"source": "integration_test"}
    )


@pytest.fixture
def sample_icon_data_list() -> List[IconData]:
    """Create a list of sample icon data for testing."""
    return [
        IconData(
            name="Animal Icon",
            url="https://yotoicons.com/images/animal.svg",
            tags=["animals", "cute"],
            description="Cute animal icon",
            category="Animals"
        ),
        IconData(
            name="Plant Icon", 
            url="https://yotoicons.com/images/plant.svg",
            tags=["nature", "plants"],
            description="Nature plant icon",
            category="Nature"
        ),
        IconData(
            name="Vehicle Icon",
            url="https://yotoicons.com/images/vehicle.svg",
            tags=["vehicles", "transport"],
            description="Transport vehicle icon",
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
        errors=["Failed to scrape icon1", "Failed to scrape icon2"],
        processing_time=15.5,
        timestamp=datetime.now(),
        icons=[]  # Add empty icons list
    )


# Scraper fixtures
@pytest.fixture
def yoto_scraper() -> YotoIconScraper:
    """Create a YotoIconScraper instance for testing."""
    return YotoIconScraper()


@pytest.fixture
def custom_scraper() -> YotoIconScraper:
    """Create a custom configured YotoIconScraper for testing."""
    return YotoIconScraper(
        base_url="https://test-icons.com",
        delay_between_requests=0.5,
        max_retries=2,
        timeout=15
    )
