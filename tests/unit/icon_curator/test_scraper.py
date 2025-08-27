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
    
    def test_is_icon_url_filtering(self):
        """Test URL filtering logic."""
        scraper = YotoIconScraper()
        
        # Should accept icon-like URLs
        assert scraper._is_icon_url("https://example.com/icon/test")
        assert scraper._is_icon_url("https://example.com/item/123")
        assert scraper._is_icon_url("https://example.com/detail/abc")
        
        # Should reject resource URLs
        assert not scraper._is_icon_url("https://example.com/test.png")
        assert not scraper._is_icon_url("https://example.com/test.jpg")
        assert not scraper._is_icon_url("https://example.com/style.css")
        assert not scraper._is_icon_url("https://example.com/script.js")
    
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
    def test_extract_icon_name_from_title(self, mock_beautifulsoup):
        """Test extracting icon name from page title."""
        scraper = YotoIconScraper()
        
        # Mock BeautifulSoup and title tag
        mock_soup = Mock()
        mock_beautifulsoup.return_value = mock_soup
        
        mock_title = Mock()
        mock_title.text = "Test Icon - Yoto Icons"
        mock_soup.find.return_value = mock_title
        
        result = scraper._extract_icon_name(mock_soup, "https://example.com/test")
        
        assert result == "Test Icon"
        mock_soup.find.assert_called_with('title')
    
    @patch('src.icon_curator.processors.scraper.BeautifulSoup')
    def test_extract_icon_name_from_h1(self, mock_beautifulsoup):
        """Test extracting icon name from H1 tag."""
        scraper = YotoIconScraper()
        
        mock_soup = Mock()
        mock_beautifulsoup.return_value = mock_soup
        
        # No title tag, but has H1
        mock_title = None
        mock_h1 = Mock()
        mock_h1.text = "Icon from H1"
        mock_soup.find.side_effect = [mock_title, mock_h1]  # title, then h1
        
        result = scraper._extract_icon_name(mock_soup, "https://example.com/test")
        
        assert result == "Icon from H1"
    
    @patch('src.icon_curator.processors.scraper.BeautifulSoup')
    def test_extract_icon_name_fallback_to_url(self, mock_beautifulsoup):
        """Test extracting icon name falls back to URL parsing."""
        scraper = YotoIconScraper()
        
        mock_soup = Mock()
        mock_beautifulsoup.return_value = mock_soup
        
        # No title, no H1, no meta
        mock_soup.find.return_value = None
        
        result = scraper._extract_icon_name(
            mock_soup, 
            "https://example.com/path/test-icon-name"
        )
        
        assert result == "Test Icon Name"
    
    def test_scraper_cleanup(self):
        """Test scraper resource cleanup."""
        scraper = YotoIconScraper()
        
        # Mock the session close method
        scraper.session.close = Mock()
        
        scraper.close()
        
        scraper.session.close.assert_called_once()
    
    @patch('src.icon_curator.processors.scraper.time.sleep')
    @patch.object(YotoIconScraper, '_discover_icon_urls')
    @patch.object(YotoIconScraper, '_scrape_icon_from_url')
    def test_scrape_all_icons_basic_flow(self, mock_scrape_icon, mock_discover_urls, mock_sleep):
        """Test the basic flow of scraping all icons."""
        scraper = YotoIconScraper(delay_between_requests=0.1)
        
        # Mock discovery returning some URLs
        mock_discover_urls.return_value = [
            "https://example.com/icon1",
            "https://example.com/icon2"
        ]
        
        # Mock successful scraping
        from src.icon_curator.models.icon import IconData
        mock_icon = IconData(
            name="Test Icon",
            url="https://example.com/icon1",
            tags=["test"]
        )
        mock_scrape_icon.return_value = mock_icon
        
        result = scraper.scrape_all_icons()
        
        assert isinstance(result, ScrapingResult)
        assert result.total_icons == 2
        assert result.successful_scraped == 2
        assert result.failed_scraped == 0
        assert len(result.errors) == 0
        assert result.processing_time > 0
        
        # Should have called scrape_icon_from_url for each discovered URL
        assert mock_scrape_icon.call_count == 2
