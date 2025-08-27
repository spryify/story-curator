"""Unit tests for web scraper (mocked tests)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.icon_curator.processors.scraper import YotoIconScraper
from src.icon_curator.models.icon import ScrapingResult
from src.icon_curator.core.exceptions import ScrapingError, NetworkError


class TestYotoIconScraper:
    """Test cases for YotoIconScraper."""
    
    def test_scraper_initialization(self):
        """Test scraper initialization with defaults."""
        scraper = YotoIconScraper()
        
        assert scraper.base_url == "https://yotoicons.com"
        assert scraper.delay_between_requests == 1.0
        assert scraper.max_retries == 3
        assert scraper.timeout == 30
        assert scraper.session is not None
    
    def test_scraper_initialization_with_custom_params(self):
        """Test scraper initialization with custom parameters."""
        scraper = YotoIconScraper(
            base_url="https://custom.com",
            delay_between_requests=2.0,
            max_retries=5,
            timeout=60
        )
        
        assert scraper.base_url == "https://custom.com"
        assert scraper.delay_between_requests == 2.0
        assert scraper.max_retries == 5
        assert scraper.timeout == 60
    
    def test_extract_icon_name_from_img(self):
        """Test extracting icon name from image tag."""
        scraper = YotoIconScraper()
        
        # Mock image tag with alt text
        mock_img = Mock()
        mock_img.get.return_value = "Test Icon Alt Text"
        
        result = scraper._extract_icon_name_from_img(mock_img, "https://example.com/test.svg")
        
        assert result == "Test Icon Alt Text"
    
    @patch('src.icon_curator.processors.scraper.requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful HTTP request."""
        scraper = YotoIconScraper()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._make_request("https://example.com/test")
        
        assert result == mock_response
        mock_get.assert_called_once_with("https://example.com/test", timeout=30)
        mock_response.raise_for_status.assert_called_once()
    
    @patch('src.icon_curator.processors.scraper.requests.Session.get')
    def test_make_request_failure(self, mock_get):
        """Test HTTP request failure."""
        scraper = YotoIconScraper()
        
        # Mock request exception
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Network error")
        
        with pytest.raises(NetworkError) as exc_info:
            scraper._make_request("https://example.com/test")
        
        assert "HTTP request failed" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)
    
    @patch('src.icon_curator.processors.scraper.BeautifulSoup')
    def test_build_icon_name(self, mock_beautifulsoup):
        """Test building icon name from tags and ID."""
        scraper = YotoIconScraper()
        
        result = scraper._build_icon_name("animals", "cat", "icon123")
        
        assert result == "Animals Cat (#icon123)"
    
    def test_has_next_page(self):
        """Test detecting if a page has a next page link."""
        scraper = YotoIconScraper()
        
        # Mock BeautifulSoup with pagination section and next page link
        mock_soup = Mock()
        mock_pagination = Mock()
        mock_next_link = Mock()
        
        # Set up the mock chain: soup.find() returns pagination, soup.select_one() returns next_link
        mock_soup.find.return_value = mock_pagination
        mock_soup.select_one.return_value = mock_next_link
        
        result = scraper._has_next_page(mock_soup)
        
        assert result is True
        mock_soup.find.assert_called_with('section', {'id': 'pagination'})
        mock_soup.select_one.assert_called_with('#pagination a#next_page')
    
    def test_extract_onclick_metadata(self):
        """Test extracting metadata from onclick attribute."""
        scraper = YotoIconScraper()
        
        # Mock div with onclick attribute - 6 parameters format
        mock_div = Mock()
        mock_div.get.return_value = "populate_icon_modal('278', 'animals', 'dinosaur', 't-rex', 'pangolinpaw', '1914');"
        
        result = scraper._extract_onclick_metadata(mock_div)
        
        assert result == {
            'icon_id': '278',
            'category': 'animals',
            'primary_tag': 'dinosaur',
            'secondary_tag': 't-rex',
            'artist': 'pangolinpaw',
            'artist_id': '1914'
        }
    
    def test_scraper_cleanup(self):
        """Test scraper resource cleanup."""
        scraper = YotoIconScraper()
        
        # Mock the session close method
        scraper.session.close = Mock()
        
        scraper.close()
        
        scraper.session.close.assert_called_once()
    
    @patch('src.icon_curator.processors.scraper.time.sleep')
    @patch.object(YotoIconScraper, '_discover_categories')
    @patch.object(YotoIconScraper, '_scrape_category')
    def test_scrape_all_icons_basic_flow(self, mock_scrape_category, mock_discover_categories, mock_sleep):
        """Test the basic flow of scraping all icons."""
        scraper = YotoIconScraper(delay_between_requests=0.1)
        
        # Mock discovery returning some categories
        mock_discover_categories.return_value = ["animals", "nature"]
        
        # Mock successful scraping for each category
        from src.icon_curator.models.icon import IconData
        mock_icon1 = IconData(
            name="Test Icon 1",
            url="https://example.com/icon1",
            tags=["animals"]
        )
        mock_icon2 = IconData(
            name="Test Icon 2", 
            url="https://example.com/icon2",
            tags=["nature"]
        )
        mock_scrape_category.side_effect = [[mock_icon1], [mock_icon2]]
        
        result = scraper.scrape_all_icons()
        
        assert isinstance(result, ScrapingResult)
        assert result.total_icons == 2
        assert result.successful_scraped == 2
        assert result.failed_scraped == 0
        assert len(result.errors) == 0
        assert result.processing_time > 0
        assert len(result.icons) == 2
        
        # Should have called scrape_category for each discovered category
        assert mock_scrape_category.call_count == 2
