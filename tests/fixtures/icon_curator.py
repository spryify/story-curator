"""Test fixtures for icon curator tests."""

import pytest
from datetime import datetime
from typing import List

from src.icon_curator.models.icon import IconData, ScrapingResult
from src.icon_curator.database.models import IconModel


@pytest.fixture
def sample_icon_data() -> IconData:
    """Create sample icon data for testing."""
    return IconData(
        name="Test Icon",
        url="https://yotoicons.com/test-icon",
        image_url="https://yotoicons.com/images/test-icon.svg",
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
            url="https://yotoicons.com/icon-one",
            image_url="https://yotoicons.com/images/icon-one.svg",
            tags=["animals", "cute"],
            description="First test icon",
            category="Animals"
        ),
        IconData(
            name="Icon Two", 
            url="https://yotoicons.com/icon-two",
            image_url="https://yotoicons.com/images/icon-two.svg",
            tags=["nature", "plants"],
            description="Second test icon",
            category="Nature"
        ),
        IconData(
            name="Icon Three",
            url="https://yotoicons.com/icon-three",
            image_url="https://yotoicons.com/images/icon-three.svg",
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
        timestamp=datetime(2025, 8, 26, 10, 30, 0)
    )


@pytest.fixture
def sample_icon_model() -> IconModel:
    """Create sample icon model for testing."""
    return IconModel(
        id=1,
        name="Model Test Icon",
        url="https://yotoicons.com/model-test",
        image_url="https://yotoicons.com/images/model-test.svg",
        tags=["model", "test"],
        description="Test icon model",
        category="Testing",
        metadata={"test": "data"}
    )
