"""Unit tests for icon data models."""

import pytest
from datetime import datetime

from src.icon_extractor.models.icon import IconData, ScrapingResult


class TestIconData:
    """Test cases for IconData model."""
    
    def test_create_icon_data_with_required_fields(self):
        """Test creating IconData with minimum required fields."""
        icon = IconData(
            name="Test Icon",
            url="https://example.com/icon.svg",
            tags=["test"]
        )
        
        assert icon.name == "Test Icon"
        assert icon.url == "https://example.com/icon.svg"
        assert icon.tags == ["test"]
        assert icon.description is None
        assert icon.category is None
        assert isinstance(icon.created_at, datetime)
        assert isinstance(icon.updated_at, datetime)
        assert icon.metadata == {}
    
    def test_create_icon_data_with_all_fields(self):
        """Test creating IconData with all fields populated."""
        created_at = datetime(2025, 1, 1, 12, 0, 0)
        updated_at = datetime(2025, 1, 2, 12, 0, 0)
        metadata = {"source": "test", "version": "1.0"}
        
        icon = IconData(
            name="Complete Icon",
            url="https://example.com/complete.svg",
            tags=["complete", "test"],
            description="A complete test icon",
            category="Testing",
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata
        )
        
        assert icon.name == "Complete Icon"
        assert icon.url == "https://example.com/complete.svg"
        assert icon.tags == ["complete", "test"]
        assert icon.description == "A complete test icon"
        assert icon.category == "Testing"
        assert icon.created_at == created_at
        assert icon.updated_at == updated_at
        assert icon.metadata == metadata
    
    def test_icon_data_post_init(self):
        """Test IconData post-initialization behavior."""
        icon = IconData(
            name="Test",
            url="https://example.com/test",
            tags=["test"]
        )
        
        # Check that defaults are set
        assert icon.metadata is not None
        assert isinstance(icon.metadata, dict)
        assert icon.created_at is not None
        assert icon.updated_at is not None
        
        # Times should be close to now
        now = datetime.now()
        assert abs((icon.created_at - now).total_seconds()) < 1
        assert abs((icon.updated_at - now).total_seconds()) < 1


class TestScrapingResult:
    """Test cases for ScrapingResult model."""
    
    def test_create_scraping_result(self):
        """Test creating a ScrapingResult."""
        timestamp = datetime.now()
        errors = ["Error 1", "Error 2"]
        
        result = ScrapingResult(
            total_icons=100,
            successful_scraped=85,
            failed_scraped=15,
            errors=errors,
            processing_time=120.5,
            timestamp=timestamp,
            icons=[]
        )
        
        assert result.total_icons == 100
        assert result.successful_scraped == 85
        assert result.failed_scraped == 15
        assert result.errors == errors
        assert result.processing_time == 120.5
        assert result.timestamp == timestamp
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = ScrapingResult(
            total_icons=100,
            successful_scraped=85,
            failed_scraped=15,
            errors=[],
            processing_time=60.0,
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert result.success_rate == 85.0
    
    def test_success_rate_zero_total(self):
        """Test success rate when total icons is zero."""
        result = ScrapingResult(
            total_icons=0,
            successful_scraped=0,
            failed_scraped=0,
            errors=[],
            processing_time=0.0,
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert result.success_rate == 0.0
    
    def test_success_rate_perfect_success(self):
        """Test success rate with 100% success."""
        result = ScrapingResult(
            total_icons=50,
            successful_scraped=50,
            failed_scraped=0,
            errors=[],
            processing_time=30.0,
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert result.success_rate == 100.0
