"""Core service for icon management."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..database.repository import IconRepository
from ..database.connection import db_manager
from ..processors.scraper import YotoIconScraper
from ..models.icon import IconData, ScrapingResult
from ..core.exceptions import IconCuratorError, DatabaseError, ScrapingError


logger = logging.getLogger(__name__)


class IconService:
    """Main service for icon curation operations."""
    
    def __init__(
        self,
        repository: Optional[IconRepository] = None,
        scraper: Optional[YotoIconScraper] = None
    ):
        """Initialize the service.
        
        Args:
            repository: Icon repository instance
            scraper: Web scraper instance
        """
        self.repository = repository or IconRepository()
        self.scraper = scraper or YotoIconScraper()
    
    def scrape_and_store_icons(
        self,
        force_update: bool = False
    ) -> ScrapingResult:
        """Scrape icons from Yoto website and store them in database.
        
        Args:
            force_update: Whether to update existing icons
            
        Returns:
            ScrapingResult with operation statistics
            
        Raises:
            IconCuratorError: If the operation fails
        """
        try:
            logger.info("Starting icon scraping and storage operation")
            
            # Ensure database tables exist
            db_manager.create_tables()
            
            # Scrape icons from website
            scraping_result = self.scraper.scrape_all_icons()
            
            logger.info(
                f"Scraping completed: {scraping_result.successful_scraped}/"
                f"{scraping_result.total_icons} icons scraped successfully"
            )
            
            # Store scraped icons in database
            stored_count = 0
            for icon_data in self._get_scraped_icons(scraping_result):
                try:
                    # Check if icon already exists
                    existing = self.repository.get_icon_by_url(icon_data.url)
                    
                    if existing and not force_update:
                        logger.debug(f"Skipping existing icon: {icon_data.name}")
                        continue
                    
                    # Store the icon
                    self.repository.save_icon(icon_data)
                    stored_count += 1
                    
                    logger.debug(f"Stored icon: {icon_data.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to store icon {icon_data.name}: {e}"
                    scraping_result.errors.append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Stored {stored_count} icons in database")
            
            # Update result with storage information
            scraping_result.successful_scraped = stored_count
            
            return scraping_result
            
        except Exception as e:
            logger.error(f"Icon scraping and storage failed: {e}")
            raise IconCuratorError(f"Failed to scrape and store icons: {e}") from e
        finally:
            self.scraper.close()
            self.repository.close()
    
    def search_icons(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[IconData]:
        """Search for icons in the database.
        
        Args:
            query: Text query to search
            category: Optional category filter
            tags: Optional tags filter
            limit: Maximum number of results
            
        Returns:
            List of matching IconData objects
        """
        try:
            icon_models = self.repository.search_icons(
                query=query,
                category=category,
                tags=tags,
                limit=limit
            )
            
            return [self._model_to_data(model) for model in icon_models]
            
        except Exception as e:
            logger.error(f"Icon search failed: {e}")
            raise IconCuratorError(f"Failed to search icons: {e}") from e
    
    def get_icon_by_id(self, icon_id: int) -> Optional[IconData]:
        """Get icon by ID.
        
        Args:
            icon_id: Icon ID to retrieve
            
        Returns:
            IconData if found, None otherwise
        """
        try:
            model = self.repository.get_icon_by_id(icon_id)
            return self._model_to_data(model) if model else None
        except Exception as e:
            logger.error(f"Failed to get icon by ID: {e}")
            raise IconCuratorError(f"Failed to get icon: {e}") from e
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        try:
            return self.repository.get_all_categories()
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            raise IconCuratorError(f"Failed to get categories: {e}") from e
    
    def get_all_tags(self) -> List[str]:
        """Get all available tags.
        
        Returns:
            List of tag names
        """
        try:
            return self.repository.get_all_tags()
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            raise IconCuratorError(f"Failed to get tags: {e}") from e
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            total_icons = self.repository.get_icon_count()
            categories = self.repository.get_all_categories()
            tags = self.repository.get_all_tags()
            
            return {
                'total_icons': total_icons,
                'total_categories': len(categories),
                'total_tags': len(tags),
                'categories': categories[:10],  # Top 10 categories
                'tags': tags[:20],  # Top 20 tags
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise IconCuratorError(f"Failed to get statistics: {e}") from e
    
    def delete_icon(self, icon_id: int) -> bool:
        """Delete an icon by ID.
        
        Args:
            icon_id: Icon ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            return self.repository.delete_icon(icon_id)
        except Exception as e:
            logger.error(f"Failed to delete icon: {e}")
            raise IconCuratorError(f"Failed to delete icon: {e}") from e
    
    def _get_scraped_icons(self, scraping_result: ScrapingResult) -> List[IconData]:
        """Extract IconData objects from scraping result.
        
        Note: In this simplified version, we assume the scraper stores
        the scraped icons somewhere accessible. In a real implementation,
        this might involve reading from a temporary storage or the scraper
        might return the icons directly.
        
        Args:
            scraping_result: Result of scraping operation
            
        Returns:
            List of scraped IconData objects
        """
        # This is a placeholder - in the real implementation,
        # the scraper would need to be modified to return the actual icons
        # For now, return empty list to avoid breaking the service
        return []
    
    def _model_to_data(self, model) -> IconData:
        """Convert database model to IconData.
        
        Args:
            model: IconModel from database
            
        Returns:
            IconData object
        """
        return IconData(
            name=model.name,
            url=model.url,
            image_url=model.image_url,
            tags=model.tags or [],
            description=model.description,
            category=model.category,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.icon_metadata or {}
        )
