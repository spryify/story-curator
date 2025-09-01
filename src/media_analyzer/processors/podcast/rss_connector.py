"""RSS feed podcast platform connector."""

import re
import logging
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from media_analyzer.models.podcast import PodcastEpisode
from media_analyzer.processors.podcast.platform_connector import PodcastPlatformConnector
from media_analyzer.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RSSFeedConnector(PodcastPlatformConnector):
    """Connector for RSS/XML podcast feeds."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize RSS connector."""
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    def validate_url(self, url: str) -> bool:
        """Validate RSS feed URL format.
        
        Args:
            url: RSS feed URL to validate
            
        Returns:
            True if URL appears to be an RSS feed
        """
        try:
            self._validate_url_format(url)
            
            # Only allow HTTP/HTTPS URLs
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Basic heuristics for RSS feed URLs
            url_lower = url.lower()
            return (
                url_lower.endswith('.xml') or 
                url_lower.endswith('.rss') or 
                'rss' in url_lower or 
                'feed' in url_lower or
                url_lower.endswith('/feed')
            )
        except ValidationError:
            return False
    
    async def get_episode_metadata(self, url: str, options=None) -> PodcastEpisode:
        """Extract episode metadata from RSS feed.
        
        Args:
            url: RSS feed URL or direct episode URL
            options: Analysis options including episode selection
            
        Returns:
            PodcastEpisode with metadata from RSS feed
        """
        if not self.validate_url(url):
            raise ValidationError(f"Invalid RSS feed URL: {url}")
        
        try:
            session = await self._get_session()
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    raise ConnectionError(f"Failed to fetch RSS feed: HTTP {response.status}")
                
                content = await response.text()
                return self._parse_rss_feed(content, url, options)
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to RSS feed: {str(e)}")
        except ET.ParseError as e:
            raise ValueError(f"Invalid RSS feed format: {str(e)}")
    
    async def get_audio_stream_url(self, episode: PodcastEpisode) -> str:
        """Get audio stream URL from RSS episode.
        
        Args:
            episode: Episode to get audio URL for
            
        Returns:
            Direct audio stream URL
        """
        if not episode.metadata or 'audio_url' not in episode.metadata:
            raise ValueError("Episode metadata missing audio URL")
        
        audio_url = episode.metadata['audio_url']
        
        # Validate that the audio URL is accessible
        try:
            session = await self._get_session()
            # Use allow_redirects=True to handle redirects automatically
            async with session.head(audio_url, timeout=10, allow_redirects=True) as response:
                if response.status not in [200, 206, 301, 302]:  # Include redirects
                    raise ConnectionError(f"Audio stream unavailable: HTTP {response.status}")
                
                # Check if it's actually an audio file (but be lenient for testing)
                content_type = response.headers.get('content-type', '').lower()
                if content_type and not any(audio_type in content_type for audio_type in ['audio/', 'video/mp4', 'application/octet-stream', 'mpeg']):
                    logger.warning(f"Unexpected content type for audio: {content_type}")
                
                # Return the final URL after redirects
                return str(response.url)
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Cannot access audio stream: {str(e)}")
    
    def supports_playlist(self) -> bool:
        """RSS feeds contain multiple episodes by nature."""
        return True
    
    def _parse_rss_feed(self, content: str, feed_url: str, options=None) -> PodcastEpisode:
        """Parse RSS feed XML and extract specific episode.
        
        Args:
            content: RSS feed XML content
            feed_url: Original feed URL for reference
            options: Analysis options including episode selection
            
        Returns:
            PodcastEpisode from the selected episode in the feed
        """
        root = ET.fromstring(content)
        
        # Find the channel
        channel = root.find('channel')
        if channel is None:
            raise ValueError("Invalid RSS feed: no channel element found")
        
        # Extract show information
        show_name = self._get_text(channel, 'title', 'Unknown Podcast')
        show_description = self._get_text(channel, 'description', '')
        
        # Find episodes
        items = channel.findall('item')
        if not items:
            raise ValueError("No episodes found in RSS feed")
        
        # Select episode based on options
        item = self._select_episode_from_items(items, options)
        
        # Extract episode information
        title = self._get_text(item, 'title', 'Unknown Episode')
        description = self._get_text(item, 'description', '')
        
        # Parse publication date
        pub_date_str = self._get_text(item, 'pubDate', '')
        pub_date = self._parse_rfc2822_date(pub_date_str) if pub_date_str else None
        
        # Find audio enclosure
        audio_url = None
        audio_type = None
        audio_length = None
        duration_seconds = None
        
        enclosure = item.find('enclosure')
        if enclosure is not None:
            audio_url = enclosure.get('url')
            audio_type = enclosure.get('type')
            try:
                audio_length = int(enclosure.get('length', 0))
            except (ValueError, TypeError):
                audio_length = None
            
            # Try to get duration from iTunes tags or other sources
            duration_text = self._get_text(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration', '') or \
                           self._get_text(item, 'duration', '')
            duration_seconds = self._parse_duration(duration_text) if duration_text else None
        
        if not audio_url:
            # Look for alternative audio links
            link = self._get_text(item, 'link', '')
            if link and any(ext in link.lower() for ext in ['.mp3', '.m4a', '.wav', '.aac']):
                audio_url = link
        
        if not audio_url:
            raise ValueError("No audio URL found in episode")
        
        # Extract episode ID from GUID or generate one
        guid_element = item.find('guid')
        if guid_element is not None and guid_element.text:
            episode_id = guid_element.text.strip()
        else:
            episode_id = self._generate_episode_id(audio_url, title)
        
        # Create episode object
        episode = PodcastEpisode(
            platform="rss",
            episode_id=episode_id,
            url=feed_url,
            title=title,
            description=self._clean_html(description),
            duration_seconds=duration_seconds,
            publication_date=pub_date,
            show_name=show_name,
            author=(self._get_text(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author') or
                   self._get_text(channel, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author') or 
                   self._get_text(channel, 'managingEditor')) or None,
            metadata={
                'audio_url': audio_url,
                'audio_type': audio_type,
                'audio_length': audio_length,
                'show_description': self._clean_html(show_description),
                'feed_url': feed_url
            }
        )
        
        return episode
    
    def _select_episode_from_items(self, items: List, options=None):
        """Select episode from RSS items based on options.
        
        Args:
            items: List of RSS item elements
            options: Analysis options with episode selection criteria
            
        Returns:
            Selected RSS item element
        """
        if not options:
            # Default to most recent episode (first item)
            return items[0]
        
        episode_index = getattr(options, 'episode_index', 0)
        episode_title = getattr(options, 'episode_title', None)
        
        # Select by title if specified
        if episode_title:
            episode_title_lower = episode_title.lower()
            for item in items:
                title = self._get_text(item, 'title', '')
                if episode_title_lower in title.lower():
                    logger.info(f"Found episode by title: {title}")
                    return item
            
            raise ValueError(f"Episode with title '{episode_title}' not found in RSS feed")
        
        # Select by index
        if episode_index >= len(items):
            raise ValueError(
                f"Episode index {episode_index} not found. RSS feed has {len(items)} episodes."
            )
        
        selected_item = items[episode_index]
        title = self._get_text(selected_item, 'title', f'Episode {episode_index}')
        logger.info(f"Selected episode {episode_index}: {title}")
        
        return selected_item
    
    def _get_text(self, element: ET.Element, tag: str, default: str = '') -> str:
        """Safely extract text from XML element."""
        child = element.find(tag)
        return child.text if child is not None and child.text else default
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub('<[^<]+?>', '', text).strip()
    
    def _parse_rfc2822_date(self, date_str: str) -> datetime:
        """Parse RFC 2822 date format used in RSS."""
        try:
            # Common RSS date formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S %z',
                '%d %b %Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            # If no format works, return current time
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return datetime.now()
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds."""
        if not duration_str:
            return None
        
        try:
            # Handle HH:MM:SS format
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    return minutes * 60 + seconds
            else:
                # Assume it's just seconds
                return int(float(duration_str))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse duration: {duration_str}")
        
        return None
    
    def _generate_episode_id(self, audio_url: str, title: str) -> str:
        """Generate unique episode ID."""
        # Use a hash of the audio URL or title
        import hashlib
        content = f"{audio_url}:{title}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            headers = {
                'User-Agent': 'Story-Curator-Podcast-Analyzer/1.0'
            }
            # Create connector with redirect handling
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                headers=headers, 
                connector=connector
            )
        return self.session
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
