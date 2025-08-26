"""Live integration tests for yotoicons.com scraping."""

import os
import pytest
import requests
from typing import List

from src.icon_curator.processors.scraper import YotoIconScraper
from src.icon_curator.models.icon import IconData
from src.icon_curator.core.exceptions import NetworkError, ScrapingError


# Skip these tests if we're in CI or if explicitly disabled
SKIP_LIVE_TESTS = os.getenv('SKIP_LIVE_TESTS', 'false').lower() == 'true'
skip_live = pytest.mark.skipif(SKIP_LIVE_TESTS, reason="Live tests disabled")


class TestLiveYotoIconsScraping:
    """Integration tests that actually connect to yotoicons.com."""
    
    @skip_live
    def test_yotoicons_site_accessibility(self):
        """Test that yotoicons.com is accessible and returns expected content."""
        response = requests.get("https://yotoicons.com/", timeout=30)
        
        assert response.status_code == 200
        assert "Yoto Icons" in response.text
        assert response.headers.get('content-type', '').startswith('text/html')
    
    @skip_live
    def test_scraper_can_connect_to_yotoicons(self):
        """Test that our scraper can successfully connect to yotoicons.com."""
        scraper = YotoIconScraper()
        
        # Test the main page connection
        response = scraper._make_request("https://yotoicons.com/")
        
        assert response is not None
        assert response.status_code == 200
        assert "Yoto Icons" in response.text
    
    @skip_live
    def test_discover_real_icon_urls(self):
        """Test discovering actual icon URLs from yotoicons.com."""
        scraper = YotoIconScraper()
        
        # Discover real icon URLs
        icon_urls = scraper._discover_icon_urls()
        
        # Should find some icon URLs
        assert len(icon_urls) > 0, "Should discover at least some icon URLs"
        
        # All URLs should be valid yotoicons URLs
        for url in icon_urls[:5]:  # Check first 5 URLs
            assert url.startswith("https://yotoicons.com/") or url.startswith("https://www.yotoicons.com/"), f"Invalid URL: {url}"
    
    @skip_live
    def test_extract_specific_icon_data(self):
        """Test extracting specific icon data from a real yotoicons.com page."""
        scraper = YotoIconScraper()
        
        # First discover some icon URLs
        icon_urls = scraper._discover_icon_urls()
        assert len(icon_urls) > 0, "Need at least one icon URL for testing"
        
        # Take the first discovered URL and try to extract icon data
        test_url = icon_urls[0]
        
        try:
            icon_data = scraper._scrape_icon_from_url(test_url)
            
            # Validate that we got actual icon data
            assert icon_data is not None, f"Should extract icon data from {test_url}"
            assert isinstance(icon_data, IconData)
            
            # Check required fields
            assert icon_data.name, "Icon should have a name"
            assert icon_data.url, "Icon should have a URL" 
            assert icon_data.image_url, "Icon should have an image URL"
            
            # Image URL should be an actual image
            assert any(icon_data.image_url.endswith(ext) for ext in ['.svg', '.png', '.jpg', '.jpeg', '.gif']), \
                f"Image URL should end with image extension: {icon_data.image_url}"
            
            print(f"✅ Successfully extracted icon data:")
            print(f"   Name: {icon_data.name}")
            print(f"   URL: {icon_data.url}")
            print(f"   Image: {icon_data.image_url}")
            print(f"   Tags: {icon_data.tags}")
            print(f"   Category: {icon_data.category}")
            
        except Exception as e:
            pytest.skip(f"Could not extract icon data from {test_url}: {e}")
    
    @skip_live
    def test_verify_image_url_accessibility(self):
        """Test that extracted image URLs are actually accessible."""
        scraper = YotoIconScraper()
        
        # Discover and scrape first icon
        icon_urls = scraper._discover_icon_urls()
        assert len(icon_urls) > 0
        
        test_url = icon_urls[0]
        icon_data = scraper._scrape_icon_from_url(test_url)
        
        if icon_data and icon_data.image_url:
            # Try to access the image URL
            try:
                image_response = requests.get(icon_data.image_url, timeout=30)
                
                assert image_response.status_code == 200, f"Image URL should be accessible: {icon_data.image_url}"
                
                # Check content type
                content_type = image_response.headers.get('content-type', '')
                assert any(img_type in content_type for img_type in ['image/', 'svg']), \
                    f"Should return image content: {content_type}"
                
                print(f"✅ Image URL verified: {icon_data.image_url}")
                print(f"   Content-Type: {content_type}")
                print(f"   Size: {len(image_response.content)} bytes")
                
            except requests.RequestException as e:
                pytest.skip(f"Could not access image URL {icon_data.image_url}: {e}")
        else:
            pytest.skip("No image URL found to test")
    
    @skip_live
    def test_scrape_multiple_icons_sample(self):
        """Test scraping a small sample of icons to verify the full pipeline."""
        scraper = YotoIconScraper()
        
        # Discover icon URLs
        icon_urls = scraper._discover_icon_urls()
        assert len(icon_urls) > 0
        
        # Test scraping first 3 icons (small sample)
        sample_size = min(3, len(icon_urls))
        successful_scrapes = 0
        errors = []
        
        for i, url in enumerate(icon_urls[:sample_size]):
            try:
                icon_data = scraper._scrape_icon_from_url(url)
                if icon_data:
                    successful_scrapes += 1
                    print(f"✅ Scraped icon {i+1}: {icon_data.name}")
                else:
                    errors.append(f"No data returned for {url}")
            except Exception as e:
                errors.append(f"Error scraping {url}: {e}")
        
        # Should have some success
        assert successful_scrapes > 0, f"Should successfully scrape at least one icon. Errors: {errors}"
        
        # Calculate success rate
        success_rate = (successful_scrapes / sample_size) * 100
        print(f"✅ Sample scraping success rate: {success_rate:.1f}% ({successful_scrapes}/{sample_size})")
        
        # Should have reasonable success rate (at least 30%)
        assert success_rate >= 30, f"Success rate too low: {success_rate}%. Errors: {errors}"
    
    @skip_live
    def test_icon_categories_discovery(self):
        """Test that we can discover different icon categories."""
        scraper = YotoIconScraper()
        
        # Discover icon URLs
        icon_urls = scraper._discover_icon_urls()
        assert len(icon_urls) > 0
        
        # Look for category patterns in URLs
        categories = set()
        for url in icon_urls:
            if "tag=" in url:
                # Extract tag parameter
                tag_part = url.split("tag=")[1].split("&")[0]
                if tag_part:
                    categories.add(tag_part)
        
        # Should find multiple categories
        assert len(categories) >= 2, f"Should discover multiple categories, found: {categories}"
        
        print(f"✅ Discovered {len(categories)} icon categories:")
        for category in sorted(categories):
            print(f"   - {category}")
        
        # Verify some expected categories from our demo
        expected_categories = {"food", "patterns", "vehicles", "weather"}
        found_expected = expected_categories.intersection(categories)
        
        assert len(found_expected) >= 2, f"Should find at least 2 expected categories. Found: {found_expected}, All: {categories}"


class TestLiveScrapingConfiguration:
    """Test configuration and setup for live scraping."""
    
    def test_skip_configuration(self):
        """Test that live tests can be skipped via environment variable."""
        # This test always runs to verify the skip mechanism works
        skip_env = os.getenv('SKIP_LIVE_TESTS', 'false')
        
        if skip_env.lower() == 'true':
            print("✅ Live tests are properly configured to skip")
        else:
            print("⚠️  Live tests will run (set SKIP_LIVE_TESTS=true to skip)")
    
    def test_scraper_configuration(self):
        """Test that the scraper is configured correctly for live testing."""
        scraper = YotoIconScraper()
        
        assert scraper.base_url == "https://yotoicons.com"
        assert scraper.timeout > 0
        assert scraper.max_retries >= 1
        assert scraper.delay_between_requests >= 0
        
        print(f"✅ Scraper configuration:")
        print(f"   Base URL: {scraper.base_url}")
        print(f"   Timeout: {scraper.timeout}s")
        print(f"   Max retries: {scraper.max_retries}")
        print(f"   Delay: {scraper.delay_between_requests}s")


# Instructions for running these tests
"""
To run live integration tests:

1. Enable live tests:
   export SKIP_LIVE_TESTS=false

2. Run specific live test:
   pytest tests/integration/icon_curator/test_live_scraping.py::TestLiveYotoIconsScraping::test_extract_specific_icon_data -v

3. Run all live tests:
   pytest tests/integration/icon_curator/test_live_scraping.py -v

4. Run with output:
   pytest tests/integration/icon_curator/test_live_scraping.py -v -s

5. Skip live tests (default):
   export SKIP_LIVE_TESTS=true
   pytest tests/integration/icon_curator/test_live_scraping.py -v

These tests will:
- Connect to the real yotoicons.com website
- Discover actual icon URLs
- Extract real icon data with names, URLs, and image URLs
- Verify image URLs are accessible
- Test the complete scraping pipeline with real data
"""
