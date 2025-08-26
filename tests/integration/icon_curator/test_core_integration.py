"""Comprehensive integration tests for icon curator core functionality."""

import pytest
from datetime import datetime

from src.icon_curator.models.icon import IconData, ScrapingResult
from src.icon_curator.core.exceptions import ValidationError
from src.icon_curator.processors.scraper import YotoIconScraper


class TestIconDataIntegration:
    """Integration tests for IconData functionality."""
    
    def test_icon_data_creation_with_all_fields(self, sample_icon_data):
        """Test creating IconData objects with all fields."""
        icon = IconData(
            name="Complete Test Icon",
            url="https://yotoicons.com/complete",
            image_url="https://yotoicons.com/complete.svg",
            tags=["test", "integration", "complete"],
            description="A complete test icon for integration tests",
            category="Testing",
            metadata={"source": "integration_test", "version": "2.0", "author": "test"}
        )
        
        # Verify all fields are set correctly
        assert icon.name == "Complete Test Icon"
        assert icon.url == "https://yotoicons.com/complete"
        assert icon.image_url == "https://yotoicons.com/complete.svg"
        assert icon.tags == ["test", "integration", "complete"]
        assert icon.description == "A complete test icon for integration tests"
        assert icon.category == "Testing"
        assert isinstance(icon.created_at, datetime)
        assert isinstance(icon.updated_at, datetime)
        assert icon.metadata == {"source": "integration_test", "version": "2.0", "author": "test"}
    
    def test_icon_data_validation_errors(self):
        """Test IconData validation with invalid data."""
        # Test with missing required fields
        with pytest.raises(TypeError):
            IconData()  # Missing required name, url, image_url, tags
        
        with pytest.raises(TypeError):
            IconData(name="Test")  # Missing url, image_url, tags
    
    def test_icon_data_defaults(self):
        """Test IconData default values."""
        icon = IconData(
            name="Minimal Icon",
            url="https://yotoicons.com/minimal",
            image_url="https://yotoicons.com/minimal.svg",
            tags=["minimal"]
        )
        
        # Check defaults
        assert icon.description is None
        assert icon.category is None
        assert isinstance(icon.created_at, datetime)
        assert isinstance(icon.updated_at, datetime)
        assert icon.metadata == {}
    
    def test_icon_data_collections_and_deduplication(self):
        """Test IconData in collections for deduplication scenarios."""
        icon1 = IconData(
            name="Duplicate Test",
            url="https://yotoicons.com/dup",
            image_url="https://yotoicons.com/dup.svg",
            tags=["duplicate"]
        )
        
        icon2 = IconData(
            name="Duplicate Test Same URL",
            url="https://yotoicons.com/dup",
            image_url="https://yotoicons.com/dup.svg",
            tags=["duplicate", "same"]
        )
        
        icon3 = IconData(
            name="Different Icon",
            url="https://yotoicons.com/different",
            image_url="https://yotoicons.com/different.svg",
            tags=["different"]
        )
        
        # Test URL-based deduplication logic
        icon_list = [icon1, icon2, icon3]
        unique_urls = {icon.url for icon in icon_list}
        assert len(unique_urls) == 2  # Should have 2 unique URLs
        
        # Test that icons with same URL can be identified
        same_url_icons = [icon for icon in icon_list if icon.url == "https://yotoicons.com/dup"]
        assert len(same_url_icons) == 2
    
    def test_icon_data_string_representations(self):
        """Test IconData string representation for debugging and logging."""
        icon = IconData(
            name="Debug Icon",
            url="https://yotoicons.com/debug",
            image_url="https://yotoicons.com/debug.svg",
            tags=["debug", "testing"],
            category="Debug"
        )
        
        icon_str = str(icon)
        assert "Debug Icon" in icon_str
        
        # Verify debugging info is accessible
        assert hasattr(icon, 'name')
        assert hasattr(icon, 'url')
        assert hasattr(icon, 'category')


class TestScrapingResultIntegration:
    """Integration tests for ScrapingResult functionality."""
    
    def test_scraping_result_creation_and_calculations(self):
        """Test creating ScrapingResult objects and success rate calculations."""
        result = ScrapingResult(
            total_icons=20,
            successful_scraped=18,
            failed_scraped=2,
            processing_time=45.5,
            errors=["Network timeout for icon19", "Parse error for icon20"],
            timestamp=datetime.now()
        )
        
        # Verify all fields
        assert result.total_icons == 20
        assert result.successful_scraped == 18
        assert result.failed_scraped == 2
        assert result.processing_time == 45.5
        assert len(result.errors) == 2
        assert result.success_rate == 90.0  # 18/20 * 100
    
    def test_scraping_result_edge_cases(self):
        """Test ScrapingResult with edge cases and boundary conditions."""
        # Test with zero total icons
        empty_result = ScrapingResult(
            total_icons=0,
            successful_scraped=0,
            failed_scraped=0,
            processing_time=0.1,
            errors=[],
            timestamp=datetime.now()
        )
        assert empty_result.success_rate == 0.0
        
        # Test with perfect success rate
        perfect_result = ScrapingResult(
            total_icons=100,
            successful_scraped=100,
            failed_scraped=0,
            processing_time=300.0,
            errors=[],
            timestamp=datetime.now()
        )
        assert perfect_result.success_rate == 100.0
        
        # Test with complete failure
        failed_result = ScrapingResult(
            total_icons=10,
            successful_scraped=0,
            failed_scraped=10,
            processing_time=5.0,
            errors=["Error1", "Error2", "Error3"],
            timestamp=datetime.now()
        )
        assert failed_result.success_rate == 0.0


class TestScraperIntegration:
    """Integration tests for YotoIconScraper functionality."""
    
    def test_scraper_default_initialization(self, yoto_scraper):
        """Test YotoIconScraper initialization with default values."""
        scraper = yoto_scraper
        
        assert scraper.base_url == "https://yotoicons.com"
        assert scraper.delay_between_requests == 1.0
        assert scraper.max_retries == 3
        assert scraper.timeout == 30
    
    def test_scraper_custom_configuration(self, custom_scraper):
        """Test YotoIconScraper with custom configuration."""
        scraper = custom_scraper
        
        assert scraper.base_url == "https://test-icons.com"
        assert scraper.delay_between_requests == 0.5
        assert scraper.max_retries == 2
        assert scraper.timeout == 15
    
    def test_scraper_parameter_validation(self):
        """Test scraper parameter validation and edge cases."""
        # Test with minimum valid parameters
        minimal_scraper = YotoIconScraper(
            delay_between_requests=0.1,
            max_retries=1,
            timeout=5
        )
        assert minimal_scraper.delay_between_requests == 0.1
        assert minimal_scraper.max_retries == 1
        assert minimal_scraper.timeout == 5
        
        # Test with maximum reasonable parameters
        max_scraper = YotoIconScraper(
            delay_between_requests=10.0,
            max_retries=10,
            timeout=300
        )
        assert max_scraper.delay_between_requests == 10.0
        assert max_scraper.max_retries == 10
        assert max_scraper.timeout == 300


class TestIntegratedWorkflow:
    """Integration tests for complete icon curator workflows."""
    
    def test_icon_creation_to_result_workflow(self, sample_icon_data_list):
        """Test complete workflow from icon creation to scraping result."""
        # Simulate creating icons from scraping
        icons = sample_icon_data_list
        
        # Verify we have expected icons
        assert len(icons) == 3
        categories = {icon.category for icon in icons}
        assert "Animals" in categories
        assert "Nature" in categories
        assert "Transport" in categories
        
        # Create a scraping result that represents processing these icons
        result = ScrapingResult(
            total_icons=5,  # Attempted to scrape 5
            successful_scraped=3,  # Got our 3 icons
            failed_scraped=2,  # 2 failed
            processing_time=12.5,
            errors=["Failed icon 1", "Failed icon 2"],
            timestamp=datetime.now()
        )
        
        # Verify the workflow results
        assert result.success_rate == 60.0  # 3/5 * 100
        assert len(result.errors) == result.failed_scraped
        assert result.successful_scraped == len(icons)
    
    def test_multi_scraper_scenario(self):
        """Test scenario with multiple scraper configurations for different sources."""
        # Main scraper for yoto icons
        yoto_scraper = YotoIconScraper()
        
        # Test scraper with different settings
        test_scraper = YotoIconScraper(
            base_url="https://test.example.com",
            delay_between_requests=0.1,  # Faster for testing
            max_retries=1,  # Fewer retries for testing
            timeout=10  # Shorter timeout for testing
        )
        
        # Verify different configurations
        assert yoto_scraper.base_url != test_scraper.base_url
        assert yoto_scraper.delay_between_requests != test_scraper.delay_between_requests
        assert yoto_scraper.max_retries != test_scraper.max_retries
        assert yoto_scraper.timeout != test_scraper.timeout
        
        # Both should be valid scrapers
        scrapers = [yoto_scraper, test_scraper]
        for scraper in scrapers:
            assert hasattr(scraper, 'base_url')
            assert hasattr(scraper, 'timeout')
            assert scraper.timeout > 0
            assert scraper.max_retries >= 1
    
    def test_error_handling_integration(self):
        """Test integrated error handling across components."""
        # Test that we can handle various error scenarios
        
        # Icon creation errors
        with pytest.raises(TypeError):
            IconData()  # Missing required fields
        
        # Scraping result with errors
        error_result = ScrapingResult(
            total_icons=1,
            successful_scraped=0,
            failed_scraped=1,
            processing_time=1.0,
            errors=["Critical scraping error"],
            timestamp=datetime.now()
        )
        
        assert error_result.success_rate == 0.0
        assert len(error_result.errors) == 1
        assert error_result.failed_scraped == 1
    
    def test_data_consistency_across_components(self, sample_icon_data):
        """Test data consistency when passing data between components."""
        # Start with icon data
        original_icon = sample_icon_data
        
        # Verify the icon maintains consistency
        assert original_icon.name == "Test Icon"
        assert original_icon.url == "https://yotoicons.com/test-icon"
        assert "test" in original_icon.tags
        assert "sample" in original_icon.tags
        assert original_icon.category == "Testing"
        
        # Create result that would represent processing this icon
        processing_result = ScrapingResult(
            total_icons=1,
            successful_scraped=1,
            failed_scraped=0,
            processing_time=2.5,
            errors=[],
            timestamp=datetime.now()
        )
        
        # Verify consistency between icon and result
        assert processing_result.successful_scraped == 1
        assert processing_result.total_icons >= processing_result.successful_scraped
        assert processing_result.success_rate == 100.0
        assert len(processing_result.errors) == processing_result.failed_scraped
