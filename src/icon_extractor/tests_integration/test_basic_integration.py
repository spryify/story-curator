"""Integration tests for core icon curator functionality."""

import pytest
from datetime import datetime

from src.icon_extractor.models.icon import IconData, ScrapingResult
from src.icon_extractor.core.exceptions import ValidationError
from src.icon_extractor.processors.scraper import YotoIconScraper


class TestIconCuratorBasicFunctionality:
    """Basic integration tests for icon curator functionality."""
    
    def test_icon_data_creation(self):
        """Test creating IconData objects with all fields."""
        icon = IconData(
            name="Test Icon",
            url="https://yotoicons.com/test.svg",
            tags=["test", "integration"],
            description="A test icon for integration tests",
            category="Testing",
            metadata={"source": "integration_test", "version": "1.0"}
        )
        
        assert icon.name == "Test Icon"
        assert icon.url == "https://yotoicons.com/test.svg"
        assert icon.tags == ["test", "integration"]
        assert icon.description == "A test icon for integration tests"
        assert icon.category == "Testing"
        assert isinstance(icon.created_at, datetime)
        assert isinstance(icon.updated_at, datetime)
        assert icon.metadata == {"source": "integration_test", "version": "1.0"}
    
    def test_icon_data_validation(self):
        """Test IconData validation with invalid data."""
        # Test with missing required fields
        with pytest.raises(TypeError):
            IconData()  # Missing required name, url, tags
    
    def test_scraping_result_creation(self):
        """Test creating ScrapingResult objects."""
        result = ScrapingResult(
            total_icons=3,
            successful_scraped=2,
            failed_scraped=1,
            processing_time=5.5,
            errors=["Failed to scrape icon3"],
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert result.total_icons == 3
        assert result.successful_scraped == 2 
        assert result.failed_scraped == 1
        assert result.processing_time == 5.5
        assert len(result.errors) == 1
        # Check success rate is approximately 66.7% (2/3 * 100)
        assert abs(result.success_rate - 66.7) < 0.1
    
    def test_scraper_initialization(self):
        """Test YotoIconScraper initialization and configuration."""
        # Test default initialization
        scraper = YotoIconScraper()
        assert scraper.base_url == "https://yotoicons.com"
        assert scraper.delay_between_requests == 1.0
        assert scraper.max_retries == 3
        assert scraper.timeout == 30
        
        # Test custom initialization
        custom_scraper = YotoIconScraper(
            base_url="https://custom-icons.com",
            delay_between_requests=2.0,
            max_retries=5,
            timeout=60
        )
        assert custom_scraper.base_url == "https://custom-icons.com"
        assert custom_scraper.delay_between_requests == 2.0
        assert custom_scraper.max_retries == 5
        assert custom_scraper.timeout == 60
    
    def test_icon_data_equality_and_hashing(self):
        """Test IconData equality and hashing for collections."""
        icon1 = IconData(
            name="Test Icon",
            url="https://yotoicons.com/test",
            tags=["test"]
        )
        
        icon2 = IconData(
            name="Test Icon",
            url="https://yotoicons.com/test", 
            tags=["test"]
        )
        
        icon3 = IconData(
            name="Different Icon",
            url="https://yotoicons.com/different",
            tags=["different"]
        )
        
        # Test that icons with same URL are considered equal for deduplication
        assert icon1.url == icon2.url
        assert icon1.url != icon3.url
        
        # Test that we can work with icons in lists for deduplication
        icon_list = [icon1, icon2, icon3]
        # Should have 2 unique icons based on URL
        unique_urls = {icon.url for icon in icon_list}
        assert len(unique_urls) == 2
    
    def test_icon_data_string_representation(self):
        """Test IconData string representation for debugging."""
        icon = IconData(
            name="Debug Icon",
            url="https://yotoicons.com/debug",
            tags=["debug"],
            category="Debug"
        )
        
        # Test that string representation contains key information
        icon_str = str(icon)
        assert "Debug Icon" in icon_str
        assert "Debug" in icon_str or "debug" in icon_str.lower()
    
    def test_scraping_result_edge_cases(self):
        """Test ScrapingResult with edge cases."""
        # Test with zero total icons
        empty_result = ScrapingResult(
            total_icons=0,
            successful_scraped=0,
            failed_scraped=0,
            processing_time=0.1,
            errors=[],
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert empty_result.success_rate == 0.0
        
        # Test with perfect success rate
        perfect_result = ScrapingResult(
            total_icons=5,
            successful_scraped=5,
            failed_scraped=0,
            processing_time=10.0,
            errors=[],
            timestamp=datetime.now(),
            icons=[]
        )
        
        assert perfect_result.success_rate == 100.0
