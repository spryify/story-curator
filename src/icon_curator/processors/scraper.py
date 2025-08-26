"""Web scraper for Yoto icons."""

import time
from datetime import datetime
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.icon import IconData, ScrapingResult
from ..core.exceptions import ScrapingError, NetworkError, ValidationError


class YotoIconScraper:
    """Scrapes icons from yotoicons.com."""
    
    def __init__(
        self, 
        base_url: str = "https://yotoicons.com",
        delay_between_requests: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize the scraper.
        
        Args:
            base_url: Base URL of the Yoto icons website
            delay_between_requests: Delay in seconds between requests
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Configure requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; IconCurator/1.0; +info@example.com)'
        })
    
    def scrape_all_icons(self) -> ScrapingResult:
        """Scrape all available icons from the website.
        
        Returns:
            ScrapingResult with statistics and any errors encountered
            
        Raises:
            ScrapingError: If scraping fails completely
            NetworkError: If network requests fail
        """
        start_time = time.time()
        scraped_icons: List[IconData] = []
        errors: List[str] = []
        
        try:
            # Get all icon page URLs
            icon_urls = self._discover_icon_urls()
            
            total_icons = len(icon_urls)
            successful_scraped = 0
            
            for url in icon_urls:
                try:
                    icon_data = self._scrape_icon_from_url(url)
                    if icon_data:
                        scraped_icons.append(icon_data)
                        successful_scraped += 1
                    
                    # Be respectful with delays
                    time.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    error_msg = f"Failed to scrape icon from {url}: {e}"
                    errors.append(error_msg)
            
            processing_time = time.time() - start_time
            
            return ScrapingResult(
                total_icons=total_icons,
                successful_scraped=successful_scraped,
                failed_scraped=total_icons - successful_scraped,
                errors=errors,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to scrape icons: {e}") from e
    
    def _discover_icon_urls(self) -> List[str]:
        """Discover all icon page URLs.
        
        Returns:
            List of icon page URLs
            
        Raises:
            NetworkError: If network request fails
            ScrapingError: If page parsing fails
        """
        try:
            response = self._make_request(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find icon links - this will need to be adjusted based on actual site structure
            icon_urls: Set[str] = set()
            
            # Look for common patterns in icon website structures
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                
                # Filter for icon-related URLs
                if self._is_icon_url(full_url):
                    icon_urls.add(full_url)
            
            # Also check for pagination or category pages
            category_urls = self._find_category_urls(soup)
            for category_url in category_urls:
                try:
                    category_response = self._make_request(category_url)
                    category_soup = BeautifulSoup(category_response.content, 'html.parser')
                    
                    for link in category_soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(self.base_url, href)
                        
                        if self._is_icon_url(full_url):
                            icon_urls.add(full_url)
                    
                    time.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    # Log but don't fail completely for category errors
                    print(f"Warning: Failed to scrape category {category_url}: {e}")
            
            return list(icon_urls)
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to discover icon URLs: {e}") from e
        except Exception as e:
            raise ScrapingError(f"Failed to parse icon discovery page: {e}") from e
    
    def _find_category_urls(self, soup: BeautifulSoup) -> List[str]:
        """Find category or pagination URLs.
        
        Args:
            soup: BeautifulSoup object of the main page
            
        Returns:
            List of category/pagination URLs
        """
        category_urls: Set[str] = set()
        
        # Look for common category/navigation patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(self.base_url, href)
            
            # Common patterns for categories or pages
            if any(pattern in href.lower() for pattern in ['category', 'tag', 'page', 'icons']):
                category_urls.add(full_url)
        
        return list(category_urls)
    
    def _is_icon_url(self, url: str) -> bool:
        """Check if a URL likely points to an individual icon page.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be an icon page
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Skip non-HTML resources
        if any(ext in path for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js']):
            return False
        
        # Look for patterns that suggest individual icon pages
        # This will need to be customized based on the actual site structure
        icon_patterns = ['icon', 'item', 'detail']
        
        return any(pattern in path for pattern in icon_patterns)
    
    def _scrape_icon_from_url(self, url: str) -> Optional[IconData]:
        """Scrape icon data from a specific URL.
        
        Args:
            url: URL of the icon page
            
        Returns:
            IconData if successful, None otherwise
            
        Raises:
            NetworkError: If network request fails
            ScrapingError: If parsing fails
        """
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract icon information - this will need to be customized
            # based on the actual HTML structure of yotoicons.com
            
            name = self._extract_icon_name(soup, url)
            image_url = self._extract_image_url(soup, url)
            description = self._extract_description(soup)
            tags = self._extract_tags(soup)
            category = self._extract_category(soup)
            
            if not name or not image_url:
                return None
            
            return IconData(
                name=name,
                url=url,
                image_url=image_url,
                description=description,
                tags=tags,
                category=category,
                metadata={'scraped_at': datetime.now().isoformat()}
            )
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to fetch icon page {url}: {e}") from e
        except Exception as e:
            raise ScrapingError(f"Failed to parse icon page {url}: {e}") from e
    
    def _extract_icon_name(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract icon name from page.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL for fallback name
            
        Returns:
            Icon name
        """
        # Try multiple strategies to find the name
        
        # Strategy 1: Title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            title = title_tag.text.strip()
            # Clean up common title patterns
            for pattern in [' - Yoto Icons', ' | Yoto Icons', 'Yoto Icons - ']:
                title = title.replace(pattern, '')
            if title:
                return title
        
        # Strategy 2: H1 tag
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.text:
            return h1_tag.text.strip()
        
        # Strategy 3: Meta property
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        # Fallback: Extract from URL
        path_parts = urlparse(url).path.split('/')
        if path_parts:
            return path_parts[-1].replace('-', ' ').replace('_', ' ').title()
        
        return None
    
    def _extract_image_url(self, soup: BeautifulSoup, page_url: str) -> Optional[str]:
        """Extract icon image URL.
        
        Args:
            soup: BeautifulSoup object
            page_url: Page URL for making relative URLs absolute
            
        Returns:
            Image URL
        """
        # Try multiple strategies to find the image
        
        # Strategy 1: Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(page_url, og_image['content'])
        
        # Strategy 2: Main image with common classes/IDs
        for selector in ['img.icon', 'img.main-image', '#main-image', '.icon-image img']:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return urljoin(page_url, img['src'])
        
        # Strategy 3: First image that looks like an icon
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            if src and ('icon' in src.lower() or 'icon' in alt):
                return urljoin(page_url, src)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract icon description.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Description text
        """
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try common description selectors
        for selector in ['.description', '.icon-description', 'p']:
            element = soup.select_one(selector)
            if element and element.text:
                text = element.text.strip()
                if len(text) > 10:  # Avoid very short text
                    return text
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of tags
        """
        tags: Set[str] = set()
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords['content'].split(',')]
            tags.update(keywords)
        
        # Tags in common containers
        for selector in ['.tags', '.keywords', '.categories']:
            container = soup.select_one(selector)
            if container:
                for link in container.find_all('a'):
                    if link.text:
                        tags.add(link.text.strip())
        
        return list(tags)
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract category information.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Category name
        """
        # Try breadcrumbs
        breadcrumbs = soup.select('.breadcrumb a, .breadcrumbs a, nav a')
        if breadcrumbs and len(breadcrumbs) > 1:
            # Usually the category is the second-to-last breadcrumb
            return breadcrumbs[-2].text.strip()
        
        # Try category-specific selectors
        for selector in ['.category', '.icon-category', '[data-category]']:
            element = soup.select_one(selector)
            if element:
                if element.text:
                    return element.text.strip()
                if element.get('data-category'):
                    return element['data-category']
        
        return None
    
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with error handling.
        
        Args:
            url: URL to request
            
        Returns:
            Response object
            
        Raises:
            NetworkError: If request fails
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise NetworkError(f"HTTP request failed for {url}: {e}") from e
    
    def close(self):
        """Clean up resources."""
        self.session.close()
