"""Data models for icon information."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class IconData:
    """Represents an icon with its metadata."""
    
    name: str
    url: str  # This will be the image URL - serves as both unique identifier and image location
    tags: List[str]
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class ScrapingResult:
    """Represents the result of a scraping operation."""
    
    total_icons: int
    successful_scraped: int
    failed_scraped: int
    errors: List[str]
    processing_time: float
    timestamp: datetime
    icons: List['IconData']  # Add the icons field
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of scraping."""
        if self.total_icons == 0:
            return 0.0
        return (self.successful_scraped / self.total_icons) * 100.0
