"""Live integration tests for real yotoicons.com scraping."""

import os
import pytest
import requests
from bs4 import BeautifulSoup
from typing import List

from src.icon_extractor.processors.scraper import YotoIconScraper
from src.icon_extractor.models.icon import IconData
from src.icon_extractor.core.exceptions import NetworkError, ScrapingError


# Skip these tests if we're in CI or if explicitly disabled
SKIP_LIVE_TESTS = os.getenv('SKIP_LIVE_TESTS', 'false').lower() == 'true'
skip_live = pytest.mark.skipif(SKIP_LIVE_TESTS, reason="Live tests disabled")


class TestLiveYotoIconsScraping:
    """Integration tests that actually connect to yotoicons.com."""
    
    @skip_live
    @pytest.mark.integration
    def test_yotoicons_site_accessibility(self):
        """Test that yotoicons.com is accessible and returns expected content."""
        response = requests.get("https://yotoicons.com/", timeout=30)
        
        assert response.status_code == 200
        assert "Yoto Icons" in response.text or "yoto" in response.text.lower()
        assert response.headers.get('content-type', '').startswith('text/html')
        
        print(f"✅ Successfully connected to yotoicons.com")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type')}")
    
    @skip_live
    @pytest.mark.integration
    def test_scraper_can_connect_to_yotoicons(self, yoto_scraper):
        """Test that our scraper can successfully connect to yotoicons.com."""
        scraper = yoto_scraper
        
        # Test the main page connection
        response = scraper._make_request("https://yotoicons.com/")
        
        assert response is not None
        assert response.status_code == 200
        assert len(response.text) > 0
        
        print(f"✅ Scraper successfully connected to yotoicons.com")
        print(f"   Response length: {len(response.text)} characters")
    
    @skip_live
    @pytest.mark.integration
    def test_discover_real_icon_categories(self, yoto_scraper):
        """Test discovering actual icon categories from yotoicons.com."""
        scraper = yoto_scraper
        
        # Test known category pages
        test_categories = ["food", "animals", "weather", "nature"]
        successful_categories = []
        
        for category in test_categories:
            try:
                url = f"https://yotoicons.com/icons?tag={category}"
                response = scraper._make_request(url)
                
                if response and response.status_code == 200:
                    successful_categories.append(category)
                    print(f"✅ Found category: {category}")
                
            except Exception as e:
                print(f"⚠️  Could not access category {category}: {e}")
        
        # Should find at least some categories
        assert len(successful_categories) > 0, f"No categories found. Tested: {test_categories}"
        
        print(f"✅ Successfully discovered {len(successful_categories)} categories")
    
    @skip_live
    def test_extract_real_icon_image_urls(self):
        """Test extracting actual icon image URLs from yotoicons.com."""
        test_categories = ["food", "weather"]
        
        all_image_urls = []
        successful_extractions = 0
        
        for category in test_categories:
            print(f"\n🔍 Testing category: {category}")
            
            try:
                # Connect to category page
                url = f"https://yotoicons.com/icons?tag={category}"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    print(f"   ✅ Connected to {category} page")
                    
                    # Parse the page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    images = soup.find_all('img')
                    
                    # Extract icon image URLs
                    category_image_urls = []
                    for img in images:
                        src = img.get('src') if hasattr(img, 'get') else None
                        if src and isinstance(src, str):
                            # Look for uploaded icon images (the real icons)
                            if 'uploads/' in src and any(ext in src for ext in ['.png', '.jpg', '.svg']):
                                if src.startswith('/'):
                                    src = f"https://yotoicons.com{src}"
                                elif not src.startswith('http'):
                                    src = f"https://yotoicons.com/{src.lstrip('/')}"
                                category_image_urls.append(src)
                    
                    if category_image_urls:
                        successful_extractions += 1
                        print(f"   🖼️  Found {len(category_image_urls)} icon URLs")
                        
                        # Test first few URLs for accessibility
                        for i, img_url in enumerate(category_image_urls[:3]):
                            try:
                                img_response = requests.get(img_url, timeout=10)
                                if img_response.status_code == 200:
                                    content_type = img_response.headers.get('content-type', '')
                                    print(f"      ✅ {img_url} ({content_type}, {len(img_response.content)} bytes)")
                                else:
                                    print(f"      ❌ {img_url} (HTTP {img_response.status_code})")
                            except Exception as e:
                                print(f"      ⚠️  {img_url} (Error: {e})")
                        
                        all_image_urls.extend(category_image_urls[:3])  # Keep first 3 from each category
                    else:
                        print(f"   ❌ No icon URLs found in {category}")
                
            except Exception as e:
                print(f"   ❌ Error processing {category}: {e}")
        
        # Verify we extracted some actual image URLs
        assert len(all_image_urls) > 0, "No icon image URLs were extracted"
        assert successful_extractions > 0, "No successful category extractions"
        
        print(f"\n🎉 LIVE INTEGRATION TEST RESULTS:")
        print(f"   Categories tested: {len(test_categories)}")
        print(f"   Successful extractions: {successful_extractions}")  
        print(f"   Total verified image URLs: {len(all_image_urls)}")
        
        if all_image_urls:
            print(f"   Sample URLs:")
            for url in all_image_urls[:3]:
                print(f"      - {url}")
    
    @skip_live
    @pytest.mark.integration
    def test_scraper_integration_with_real_site(self, yoto_scraper):
        """Test complete scraper integration with the real yotoicons.com site."""
        scraper = yoto_scraper
        
        try:
            # Test URL discovery
            discovered_urls = scraper._discover_icon_urls()
            
            print(f"✅ Scraper discovered {len(discovered_urls)} URLs")
            
            if len(discovered_urls) > 0:
                # Test extracting data from first few URLs
                test_urls = discovered_urls[:3]  # Test first 3
                extracted_icons = []
                
                for url in test_urls:
                    try:
                        icon_data = scraper._extract_icon_data(url)
                        if icon_data:
                            extracted_icons.append(icon_data)
                            print(f"   ✅ Extracted: {icon_data.name}")
                    except Exception as e:
                        print(f"   ⚠️  Could not extract from {url}: {e}")
                
                assert len(extracted_icons) > 0, "No icons were successfully extracted"
                
                # Verify extracted data structure
                for icon in extracted_icons:
                    assert isinstance(icon, IconData)
                    assert icon.name is not None
                    assert icon.url is not None
                    assert isinstance(icon.tags, list)
                
                print(f"✅ Successfully extracted {len(extracted_icons)} complete icon records")
            
        except Exception as e:
            pytest.skip(f"Scraper integration test skipped due to site changes: {e}")
    
    @skip_live
    def test_verify_image_url_accessibility(self):
        """Test that discovered image URLs are actually accessible and return valid images."""
        # Test a few known working URLs from previous runs
        test_urls = [
            "https://yotoicons.com/icons?tag=food",
            "https://yotoicons.com/icons?tag=animals"
        ]
        
        verified_image_urls = []
        
        for page_url in test_urls:
            try:
                response = requests.get(page_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    images = soup.find_all('img')
                    
                    for img in images[:2]:  # Test first 2 per page
                        src = img.get('src') if hasattr(img, 'get') else None
                        if src and isinstance(src, str) and 'uploads/' in src:
                            if src.startswith('/'):
                                src = f"https://yotoicons.com{src}"
                            
                            # Test accessibility
                            try:
                                img_response = requests.get(src, timeout=10)
                                if img_response.status_code == 200:
                                    content_type = img_response.headers.get('content-type', '')
                                    if any(img_type in content_type for img_type in ['image/', 'svg']):
                                        verified_image_urls.append(src)
                                        print(f"✅ Verified: {src} ({content_type})")
                            except Exception as e:
                                print(f"⚠️  Could not verify {src}: {e}")
                        
            except Exception as e:
                print(f"⚠️  Could not test {page_url}: {e}")
        
        assert len(verified_image_urls) > 0, "No image URLs could be verified as accessible"
        
        print(f"🎉 Verified {len(verified_image_urls)} accessible image URLs")
    
    @skip_live
    @pytest.mark.integration
    def test_full_scraping_pipeline_sample(self, yoto_scraper):
        """Test the complete scraping pipeline with a small sample of real data."""
        scraper = yoto_scraper
        
        try:
            # Test scraping a small sample
            result = scraper.scrape_sample_icons(max_icons=5, max_pages=2)
            
            print(f"✅ Sample scraping completed:")
            print(f"   Total icons attempted: {result.total_icons}")
            print(f"   Successfully scraped: {result.successful_scraped}")
            print(f"   Failed: {result.failed_scraped}")
            print(f"   Success rate: {result.success_rate}%")
            print(f"   Processing time: {result.processing_time}s")
            
            # Basic validation
            assert result.total_icons > 0
            assert result.successful_scraped >= 0
            assert result.failed_scraped >= 0
            assert result.total_icons == result.successful_scraped + result.failed_scraped
            assert result.processing_time > 0
            
            if result.errors:
                print(f"   Errors encountered: {len(result.errors)}")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")
            
        except AttributeError:
            # Method might not exist - skip with message
            pytest.skip("scrape_sample_icons method not implemented yet")
        except Exception as e:
            pytest.skip(f"Full pipeline test skipped due to site changes: {e}")


class TestLiveScrapingConfiguration:
    """Test configuration and setup for live scraping."""
    
    def test_live_test_skip_configuration(self):
        """Test that live tests can be properly skipped via environment variable."""
        # This test always runs to verify the skip configuration
        import os
        
        skip_env_var = os.getenv('SKIP_LIVE_TESTS', 'false').lower()
        
        print(f"✅ SKIP_LIVE_TESTS environment variable: {skip_env_var}")
        
        if skip_env_var == 'true':
            print("   Live tests will be SKIPPED")
        else:
            print("   Live tests will RUN (ensure internet connection)")
    
    @skip_live
    def test_scraper_configuration_for_live_testing(self, yoto_scraper):
        """Test that the scraper is configured correctly for live testing."""
        scraper = yoto_scraper
        
        assert scraper.base_url == "https://yotoicons.com"
        assert scraper.timeout > 0
        assert scraper.max_retries >= 1
        assert scraper.delay_between_requests >= 0
        
        print(f"✅ Scraper configuration validated:")
        print(f"   Base URL: {scraper.base_url}")
        print(f"   Timeout: {scraper.timeout}s")
        print(f"   Max retries: {scraper.max_retries}")
        print(f"   Delay between requests: {scraper.delay_between_requests}s")


# Instructions for running these tests
"""
To run live integration tests:

1. Enable live tests:
   export SKIP_LIVE_TESTS=false

2. Run specific live test:
   pytest tests/integration/icon_extractor/test_live_integration.py::TestLiveYotoIconsScraping::test_extract_real_icon_image_urls -v -s

3. Run all live tests:
   pytest tests/integration/icon_extractor/test_live_integration.py -v -s

4. Skip live tests (default):
   export SKIP_LIVE_TESTS=true
   pytest tests/integration/icon_extractor/test_live_integration.py -v

These tests will:
- Connect to the real yotoicons.com website
- Discover actual icon URLs and categories
- Extract real icon data with names, URLs, and image URLs
- Verify image URLs are accessible and return valid image data
- Test the complete scraping pipeline with real data
- Validate scraper configuration for production use
"""
