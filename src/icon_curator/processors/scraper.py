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
            # Get all available categories
            categories = self._discover_categories()
            
            total_icons = 0
            successful_scraped = 0
            
            for category in categories:
                try:
                    # Scrape all pages for this category
                    category_icons = self._scrape_category(category)
                    scraped_icons.extend(category_icons)
                    
                    successful_scraped += len(category_icons)
                    total_icons += len(category_icons)
                    
                    print(f"✅ Scraped {len(category_icons)} icons from category '{category}'")
                    
                    # Be respectful with delays between categories
                    time.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    error_msg = f"Failed to scrape category {category}: {e}"
                    errors.append(error_msg)
                    print(f"⚠️  {error_msg}")
            
            processing_time = time.time() - start_time
            
            return ScrapingResult(
                total_icons=total_icons,
                successful_scraped=successful_scraped,
                failed_scraped=0,  # We count successful icons directly
                errors=errors,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise ScrapingError(f"Failed to scrape icons: {e}") from e
    
    def _discover_categories(self) -> List[str]:
        """Discover all available categories on yotoicons.com.
        
        Returns:
            List of category names
            
        Raises:
            NetworkError: If network request fails
            ScrapingError: If page parsing fails
        """
        # Known categories from our testing - we can also discover these dynamically
        # but for now let's use the ones we know work
        known_categories = [
            "animals", "food", "weather", "nature", "transport", "people", 
            "objects", "buildings", "technology", "sports", "music", "health"
        ]
        
        # TODO: Could also discover categories dynamically by parsing the main page
        # but the known categories approach is more reliable for yotoicons.com
        return known_categories

    def _scrape_category(self, category: str) -> List[IconData]:
        """Scrape all icons from a specific category, handling pagination.
        
        Args:
            category: Category name to scrape
            
        Returns:
            List of IconData objects for all icons in the category
            
        Raises:
            NetworkError: If network request fails
            ScrapingError: If page parsing fails
        """
        all_icons: List[IconData] = []
        page = 1
        
        while True:
            try:
                # Build category URL with pagination
                category_url = f"{self.base_url}/icons?tag={category}&page={page}"
                print(f"🔍 Scraping {category_url}")
                
                response = self._make_request(category_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract all icon image URLs from this page
                page_icons = self._extract_icons_from_page(soup, category, category_url)
                
                if not page_icons:
                    # No icons found on this page, we've reached the end
                    break
                
                all_icons.extend(page_icons)
                print(f"   📦 Found {len(page_icons)} icons on page {page}")
                
                # Check if there's a next page
                if not self._has_next_page(soup):
                    break
                    
                page += 1
                
                # Be respectful with delays between pages
                time.sleep(self.delay_between_requests)
                
            except Exception as e:
                print(f"⚠️  Error scraping page {page} of category {category}: {e}")
                break
        
        return all_icons

    def _extract_icons_from_page(self, soup: BeautifulSoup, category: str, page_url: str) -> List[IconData]:
        """Extract all icon data from a category page.
        
        Args:
            soup: BeautifulSoup object of the category page
            category: Category name
            page_url: URL of the page being scraped
            
        Returns:
            List of IconData objects
        """
        icons: List[IconData] = []
        
        # Find all images that are uploaded icons
        images = soup.find_all('img')
        
        for img in images:
            try:
                src = img.get('src') if hasattr(img, 'get') else None
                if not src or not isinstance(src, str):
                    continue
                
                # Look for uploaded icon images (the real icons)
                if 'uploads/' in src and any(ext in src for ext in ['.png', '.jpg', '.svg']):
                    # Make URL absolute
                    if src.startswith('/'):
                        image_url = f"{self.base_url}{src}"
                    elif not src.startswith('http'):
                        image_url = f"{self.base_url}/{src.lstrip('/')}"
                    else:
                        image_url = src
                    
                    # Extract metadata from the image context
                    name = self._extract_icon_name_from_img(img, image_url)
                    tags = [category]  # At minimum, the category is a tag
                    
                    # Try to get additional tags from alt text or surrounding context
                    alt_text = img.get('alt', '') if hasattr(img, 'get') else ''
                    if alt_text and isinstance(alt_text, str) and alt_text != name:
                        # Parse alt text for additional keywords
                        alt_keywords = [word.strip() for word in alt_text.lower().split() if len(word) > 2]
                        tags.extend(alt_keywords)
                    
                    icon_data = IconData(
                        name=name,
                        url=page_url,  # The category page URL
                        image_url=image_url,
                        description=f"Icon from {category} category",
                        tags=list(set(tags)),  # Remove duplicates
                        category=category,
                        metadata={
                            'scraped_at': datetime.now().isoformat(),
                            'source_page': page_url,
                            'category': category
                        }
                    )
                    
                    icons.append(icon_data)
                    
            except Exception as e:
                print(f"   ⚠️  Error processing image: {e}")
                continue
        
        return icons

    def _extract_icon_name_from_img(self, img_tag, image_url: str) -> str:
        """Extract icon name from image tag or URL.
        
        Args:
            img_tag: BeautifulSoup img tag
            image_url: Image URL
            
        Returns:
            Icon name
        """
        # Try alt text first
        alt = img_tag.get('alt', '') if hasattr(img_tag, 'get') else ''
        if alt and isinstance(alt, str) and alt.strip():
            return alt.strip()
        
        # Try title attribute
        title = img_tag.get('title', '') if hasattr(img_tag, 'get') else ''
        if title and isinstance(title, str) and title.strip():
            return title.strip()
        
        # Extract from filename
        try:
            filename = image_url.split('/')[-1]
            name = filename.split('.')[0]  # Remove extension
            # Convert number to more readable format
            if name.isdigit():
                return f"Icon {name}"
            return name.replace('_', ' ').replace('-', ' ').title()
        except:
            return "Unnamed Icon"

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page in pagination.
        
        Args:
            soup: BeautifulSoup object of the current page
            
        Returns:
            True if there's a next page
        """
        # Look for pagination section
        pagination = soup.find('section', {'id': 'pagination'})
        if not pagination:
            return False
        
        # Look for next page link - using CSS selector is more reliable
        next_link = soup.select_one('#pagination a#next_page')
        return next_link is not None
    
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
