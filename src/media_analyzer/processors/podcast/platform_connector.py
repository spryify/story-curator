"""Abstract base class for podcast platform connectors."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator
from urllib.parse import urlparse

from media_analyzer.models.podcast import PodcastEpisode
from media_analyzer.core.exceptions import ValidationError


class PodcastPlatformConnector(ABC):
    """Abstract base class for podcast platform integrations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the connector with optional configuration."""
        self.config = config or {}
        self.platform_name = self.__class__.__name__.replace('Connector', '').lower()
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Validate platform-specific URL format.
        
        Args:
            url: The podcast episode URL to validate
            
        Returns:
            True if URL is valid for this platform
        """
        pass
    
    @abstractmethod  
    async def get_episode_metadata(self, url: str) -> PodcastEpisode:
        """Extract episode metadata from platform.
        
        Args:
            url: The podcast episode URL
            
        Returns:
            PodcastEpisode with metadata
            
        Raises:
            ValidationError: If URL is invalid
            ConnectionError: If platform is unavailable
            ValueError: If episode not found
        """
        pass
    
    @abstractmethod
    async def get_audio_stream_url(self, episode: PodcastEpisode) -> str:
        """Get streamable audio URL for transcription.
        
        Args:
            episode: The podcast episode to get audio for
            
        Returns:
            Direct URL to audio stream
            
        Raises:
            ConnectionError: If audio stream unavailable
            ValueError: If episode doesn't have audio
        """
        pass
    
    def _validate_url_format(self, url: str) -> None:
        """Basic URL validation.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If URL format is invalid
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(f"Invalid URL format: {url}")
        except Exception as e:
            raise ValidationError(f"Invalid URL: {str(e)}")
    
    def supports_playlist(self) -> bool:
        """Check if platform supports playlist/batch processing.
        
        Returns:
            True if platform supports playlist processing
        """
        return False
