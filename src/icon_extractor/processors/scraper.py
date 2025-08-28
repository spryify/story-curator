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
                timestamp=datetime.now(),
                icons=scraped_icons
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

    def _scrape_category(self, category: str, max_pages: Optional[int] = None) -> List[IconData]:
        """Scrape icons from a specific category, handling pagination.
        
        Args:
            category: Category name to scrape
            max_pages: Maximum number of pages to scrape (None for all pages)
            
        Returns:
            List of IconData objects for all icons in the category
            
        Raises:
            NetworkError: If network request fails
            ScrapingError: If page parsing fails
        """
        all_icons: List[IconData] = []
        page = 1
        
        while True:
            # Check page limit
            if max_pages and page > max_pages:
                print(f"🛑 Reached maximum page limit ({max_pages}) for category {category}")
                break
                
            try:
                # Build category URL with pagination
                category_url = f"{self.base_url}/icons?tag={category}&page={page}"
                if max_pages:
                    print(f"🔍 Scraping {category_url} (page {page}/{max_pages})")
                else:
                    print(f"🔍 Scraping {category_url} (page {page})")
                
                response = self._make_request(category_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract all icon image URLs from this page
                page_icons = self._extract_icons_from_page(soup, category, category_url)
                
                if not page_icons:
                    # No icons found on this page, we've reached the end
                    if max_pages:
                        print(f"✅ Category {category} completed - no more icons found (scraped {page-1} pages)")
                    else:
                        print(f"✅ Category {category} completed - no more icons found")
                    break
                
                all_icons.extend(page_icons)
                if max_pages:
                    print(f"📦 Found {len(page_icons)} icons on page {page} (total: {len(all_icons)})")
                else:
                    print(f"   📦 Found {len(page_icons)} icons on page {page}")
                
                # Check if there's a next page (only if no max_pages limit)
                if not max_pages and not self._has_next_page(soup):
                    break
                    
                page += 1
                
                # Be respectful with delays between pages
                time.sleep(self.delay_between_requests)
                
            except Exception as e:
                print(f"⚠️  Error scraping page {page} of category {category}: {e}")
                break
        
        return all_icons

    def scrape_category(self, category: str, max_pages: Optional[int] = None) -> ScrapingResult:
        """Scrape icons from a specific category with optional page limit.
        
        Args:
            category: Category name to scrape
            max_pages: Maximum number of pages to scrape (None for all pages)
            
        Returns:
            ScrapingResult with statistics and any errors encountered
            
        Raises:
            ScrapingError: If scraping fails completely
            NetworkError: If network requests fail
        """
        start_time = time.time()
        errors: List[str] = []
        
        try:
            category_icons = self._scrape_category(category, max_pages)
            
            processing_time = time.time() - start_time
            total_icons = len(category_icons)
            successful_scraped = len([icon for icon in category_icons if icon is not None])
            
            return ScrapingResult(
                total_icons=total_icons,
                successful_scraped=successful_scraped,
                failed_scraped=total_icons - successful_scraped,
                processing_time=processing_time,
                errors=errors,
                timestamp=datetime.now(),
                icons=category_icons
            )
            
        except Exception as e:
            errors.append(f"Failed to scrape category {category}: {e}")
            processing_time = time.time() - start_time
            
            return ScrapingResult(
                total_icons=0,
                successful_scraped=0,
                failed_scraped=1,
                processing_time=processing_time,
                errors=errors,
                timestamp=datetime.now(),
                icons=[]
            )

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
        
        # Find all icon divs with onclick attributes - this contains the rich metadata
        icon_divs = soup.find_all('div', class_='icon')
        
        for icon_div in icon_divs:
            try:
                # Extract onclick metadata first
                onclick_data = self._extract_onclick_metadata(icon_div)
                if not onclick_data:
                    continue
                
                # Find the image within this icon div
                img = icon_div.find('img')
                if not img:
                    continue
                    
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
                    
                    # Use rich metadata from onclick attribute
                    icon_id = onclick_data.get('icon_id', '')
                    primary_tag = onclick_data.get('primary_tag', '')
                    secondary_tag = onclick_data.get('secondary_tag', '')
                    artist = onclick_data.get('artist', '')
                    num_downloads = onclick_data.get('num_downloads', '')

                    # Build comprehensive name from available data
                    name = self._build_icon_name(primary_tag, secondary_tag, icon_id)
                    
                    # Build comprehensive tags list
                    tags = [category]  # Always include category
                    if primary_tag and primary_tag not in tags:
                        tags.append(primary_tag)
                    if secondary_tag and secondary_tag not in tags:
                        tags.append(secondary_tag)
                    
                    # Build description with available context
                    description_parts = []
                    if primary_tag:
                        description_parts.append(primary_tag)
                    if secondary_tag and secondary_tag != primary_tag:
                        description_parts.append(secondary_tag)
                    description = f"{', '.join(description_parts)} icon from {category} category" if description_parts else f"Icon from {category} category"
                    
                    # Build metadata with all extracted information
                    metadata = {
                        'scraped_at': datetime.now().isoformat(),
                        'source_page': page_url,
                        'category': category,
                        'icon_id': icon_id,
                        'primary_tag': primary_tag,
                        'secondary_tag': secondary_tag,
                        'artist': artist,
                        'num_downloads': num_downloads
                    }
                    
                    icon_data = IconData(
                        name=name,
                        url=image_url,  # Store the actual image URL in the url field
                        description=description,
                        tags=list(set(tags)),  # Remove duplicates
                        category=category,
                        metadata=metadata
                    )
                    
                    icons.append(icon_data)
                    
            except Exception as e:
                print(f"   ⚠️  Error processing icon div: {e}")
                continue
        
        return icons

    def _extract_onclick_metadata(self, icon_div) -> dict:
        """Extract metadata from onclick attribute of icon div.
        
        Args:
            icon_div: BeautifulSoup div element with class='icon'
            
        Returns:
            Dictionary with extracted metadata
        """
        onclick = icon_div.get('onclick') if hasattr(icon_div, 'get') else None
        if not onclick or not isinstance(onclick, str):
            return {}
        
        try:
            # Parse onclick like: populate_icon_modal('278', 'animals', 'dinosaur', 't-rex', 'pangolinpaw', '1914');
            # Extract parameters between quotes
            import re
            matches = re.findall(r"'([^']*)'", onclick)
            
            if len(matches) >= 6:
                return {
                    'icon_id': matches[0],
                    'category': matches[1], 
                    'primary_tag': matches[2],
                    'secondary_tag': matches[3],
                    'artist': matches[4],
                    'num_downloads': matches[5]
                }
            elif len(matches) >= 4:
                return {
                    'icon_id': matches[0],
                    'category': matches[1],
                    'primary_tag': matches[2], 
                    'secondary_tag': matches[3],
                    'artist': '',
                    'num_downloads': ''
                }
            else:
                return {}
                
        except Exception as e:
            print(f"   ⚠️  Error parsing onclick: {onclick[:100]}... - {e}")
            return {}

    def _build_icon_name(self, primary_tag: str, secondary_tag: str, icon_id: str) -> str:
        """Build a meaningful icon name from available metadata.
        
        Args:
            primary_tag: Primary tag (e.g., 'dinosaur')
            secondary_tag: Secondary tag (e.g., 't-rex')
            icon_id: Icon ID (e.g., '278')
            
        Returns:
            Human-readable icon name
        """
        name_parts = []
        
        if primary_tag and primary_tag.strip():
            name_parts.append(primary_tag.strip().title())
            
        if secondary_tag and secondary_tag.strip() and secondary_tag != primary_tag:
            name_parts.append(secondary_tag.strip().title())
        
        if name_parts:
            name = ' '.join(name_parts)
            # Add icon ID for uniqueness if needed
            if icon_id:
                name = f"{name} (#{icon_id})"
            return name
        else:
            # Fallback to icon ID
            return f"Icon {icon_id}" if icon_id else "Unnamed Icon"

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
