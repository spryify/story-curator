"""Integration tests for RSS connector episode selection functionality."""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from media_analyzer.processors.podcast.rss_connector import RSSFeedConnector
from media_analyzer.models.podcast import PodcastEpisode, AnalysisOptions
from media_analyzer.core.exceptions import ValidationError

# Configure logging for test output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRSSConnectorEpisodeSelection:
    """Integration tests for RSS connector episode selection features."""
    
    @pytest.fixture
    def circle_round_feed_url(self) -> str:
        """Circle Round podcast RSS feed URL for testing."""
        return "https://rss.wbur.org/circleround/podcast"
    
    @pytest.fixture
    def rss_connector(self) -> RSSFeedConnector:
        """Create an RSS connector instance."""
        return RSSFeedConnector()

    @pytest.mark.asyncio
    async def test_default_episode_selection(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test default episode selection (most recent episode)."""
        logger.info("Testing default episode selection (most recent)...")
        
        # Test without any options - should get most recent episode
        episode = await rss_connector.get_episode_metadata(circle_round_feed_url)
        
        # Basic validation
        assert isinstance(episode, PodcastEpisode)
        assert episode.platform == "rss"
        assert episode.show_name == "Circle Round"
        assert episode.title is not None and len(episode.title) > 0
        assert episode.episode_id is not None
        assert episode.metadata is not None and 'audio_url' in episode.metadata
        
        logger.info(f"Default selection found: '{episode.title}'")
        logger.info(f"   Published: {episode.publication_date}")
        logger.info(f"   Duration: {episode.duration_seconds}s" if episode.duration_seconds else "   Duration: Not specified")
        
        return episode

    @pytest.mark.asyncio
    async def test_episode_selection_by_index(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test episode selection by index."""
        logger.info("Testing episode selection by index...")
        
        # Test getting episode at index 0 (most recent)
        options_index_0 = AnalysisOptions(episode_index=0)
        episode_0 = await rss_connector.get_episode_metadata(circle_round_feed_url, options_index_0)
        
        # Test getting episode at index 1 (second most recent)
        options_index_1 = AnalysisOptions(episode_index=1)
        episode_1 = await rss_connector.get_episode_metadata(circle_round_feed_url, options_index_1)
        
        # Test getting episode at index 2 (third most recent)
        options_index_2 = AnalysisOptions(episode_index=2)
        episode_2 = await rss_connector.get_episode_metadata(circle_round_feed_url, options_index_2)
        
        # Validate that we got different episodes
        assert episode_0.episode_id != episode_1.episode_id, "Episodes at different indices should be different"
        assert episode_1.episode_id != episode_2.episode_id, "Episodes at different indices should be different"
        assert episode_0.title != episode_1.title, "Episode titles should be different"
        
        # Validate episode structure for all episodes
        for i, episode in enumerate([episode_0, episode_1, episode_2]):
            assert isinstance(episode, PodcastEpisode)
            assert episode.platform == "rss"
            assert episode.show_name == "Circle Round"
            assert episode.title is not None and len(episode.title) > 0
            assert episode.episode_id is not None
            assert episode.metadata is not None and 'audio_url' in episode.metadata
            
            logger.info(f"Episode {i}: '{episode.title}'")
            logger.info(f"   Published: {episode.publication_date}")
            logger.info(f"   Duration: {episode.duration_seconds}s" if episode.duration_seconds else "   Duration: Not specified")
        
        # Test that newer episodes are typically published later (RSS feeds are usually chronological)
        if episode_0.publication_date and episode_1.publication_date:
            assert episode_0.publication_date >= episode_1.publication_date, \
                "Episode at index 0 should be published on or after episode at index 1"

    @pytest.mark.asyncio
    async def test_episode_selection_by_title(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test episode selection by title matching."""
        logger.info("Testing episode selection by title matching...")
        
        # First, get several recent episodes to find available titles
        episodes_for_title_search = []
        for i in range(5):  # Get first 5 episodes to have title options
            try:
                options = AnalysisOptions(episode_index=i)
                episode = await rss_connector.get_episode_metadata(circle_round_feed_url, options)
                episodes_for_title_search.append(episode)
                logger.info(f"Available episode {i}: '{episode.title}'")
            except ValueError as e:
                logger.warning(f"Could not fetch episode {i}: {e}")
                break
        
        assert len(episodes_for_title_search) >= 2, "Need at least 2 episodes for title testing"
        
        # Test exact title matching (using a distinctive word from the title)
        test_episode = episodes_for_title_search[1]  # Use second episode to ensure it's not default
        
        # Extract a unique word from the title for partial matching
        title_words = test_episode.title.split()
        # Find a distinctive word (longer than 3 chars, not common words)
        distinctive_word = None
        common_words = {'the', 'and', 'of', 'to', 'in', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'with'}
        
        for word in title_words:
            clean_word = word.strip('.,!?:;"()').lower()
            if len(clean_word) > 3 and clean_word not in common_words:
                distinctive_word = clean_word
                break
        
        if not distinctive_word:
            # If no distinctive word found, use the first word
            distinctive_word = title_words[0].strip('.,!?:;"()').lower()
        
        logger.info(f"Testing title search with word: '{distinctive_word}'")
        
        # Test title-based selection
        options_title = AnalysisOptions(episode_title=distinctive_word)
        episode_by_title = await rss_connector.get_episode_metadata(circle_round_feed_url, options_title)
        
        # Validate that we found the expected episode (should contain the search term)
        assert distinctive_word.lower() in episode_by_title.title.lower(), \
            f"Found episode title '{episode_by_title.title}' should contain '{distinctive_word}'"
        
        # Basic episode validation
        assert isinstance(episode_by_title, PodcastEpisode)
        assert episode_by_title.platform == "rss"
        assert episode_by_title.show_name == "Circle Round"
        assert episode_by_title.title is not None and len(episode_by_title.title) > 0
        assert episode_by_title.metadata is not None and 'audio_url' in episode_by_title.metadata
        
        logger.info(f"Found episode by title: '{episode_by_title.title}'")
        logger.info(f"   Published: {episode_by_title.publication_date}")
        
        # Test case-insensitive title matching
        options_title_upper = AnalysisOptions(episode_title=distinctive_word.upper())
        episode_by_title_upper = await rss_connector.get_episode_metadata(circle_round_feed_url, options_title_upper)
        assert episode_by_title.episode_id == episode_by_title_upper.episode_id, \
            "Case-insensitive title matching should work"
        
        logger.info("Case-insensitive title matching works")

    @pytest.mark.asyncio
    async def test_invalid_episode_selection(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test error handling for invalid episode selection."""
        logger.info("Testing error handling for invalid episode selection...")
        
        # Test invalid episode index (too high)
        options_invalid_index = AnalysisOptions(episode_index=999)
        with pytest.raises(ValueError) as exc_info:
            await rss_connector.get_episode_metadata(circle_round_feed_url, options_invalid_index)
        
        assert "Episode index 999 not found" in str(exc_info.value)
        logger.info("Invalid episode index properly raises ValueError")
        
        # Test non-existent episode title
        options_invalid_title = AnalysisOptions(episode_title="NonExistentEpisodeTitle12345XYZ")
        with pytest.raises(ValueError) as exc_info:
            await rss_connector.get_episode_metadata(circle_round_feed_url, options_invalid_title)
        
        assert "Episode with title 'NonExistentEpisodeTitle12345XYZ' not found" in str(exc_info.value)
        logger.info("Non-existent episode title properly raises ValueError")

    @pytest.mark.asyncio
    async def test_audio_url_accessibility(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test that selected episodes have accessible audio URLs."""
        logger.info("Testing audio URL accessibility for selected episodes...")
        
        # Test audio URLs for multiple episodes
        test_indices = [0, 1, 2]
        accessible_episodes = []
        
        for index in test_indices:
            try:
                options = AnalysisOptions(episode_index=index)
                episode = await rss_connector.get_episode_metadata(circle_round_feed_url, options)
                
                # Get audio stream URL (this tests accessibility)
                audio_url = await rss_connector.get_audio_stream_url(episode)
                
                assert audio_url.startswith('http'), "Audio URL should be valid HTTP URL"
                assert any(ext in audio_url.lower() for ext in ['.mp3', '.m4a', '.wav', 'audio']), \
                    "Audio URL should indicate audio content"
                
                accessible_episodes.append({
                    'index': index,
                    'title': episode.title,
                    'audio_url': audio_url,
                    'duration': episode.duration_seconds
                })
                
                logger.info(f"Episode {index} audio URL accessible: {audio_url[:60]}...")
                
            except Exception as e:
                logger.warning(f"Episode {index} audio URL not accessible: {e}")
        
        assert len(accessible_episodes) >= 1, "At least one episode should have accessible audio"
        logger.info(f"{len(accessible_episodes)}/{len(test_indices)} episodes have accessible audio URLs")

    @pytest.mark.asyncio
    async def test_episode_metadata_consistency(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test that episode metadata is consistent across different selection methods."""
        logger.info("Testing episode metadata consistency...")
        
        # Get the same episode via index and title
        options_index = AnalysisOptions(episode_index=1)
        episode_by_index = await rss_connector.get_episode_metadata(circle_round_feed_url, options_index)
        
        # Extract title for search
        title_words = episode_by_index.title.split()
        search_term = title_words[0] if title_words else episode_by_index.title[:10]
        
        try:
            options_title = AnalysisOptions(episode_title=search_term)
            episode_by_title = await rss_connector.get_episode_metadata(circle_round_feed_url, options_title)
            
            # If we found the same episode, metadata should be identical
            if episode_by_index.episode_id == episode_by_title.episode_id:
                assert episode_by_index.title == episode_by_title.title
                assert episode_by_index.duration_seconds == episode_by_title.duration_seconds
                assert episode_by_index.publication_date == episode_by_title.publication_date
                assert (episode_by_index.metadata is not None and 
                       episode_by_title.metadata is not None and
                       episode_by_index.metadata['audio_url'] == episode_by_title.metadata['audio_url'])
                
                logger.info("Episode metadata is consistent between selection methods")
            else:
                logger.info("Title search returned different episode (partial match)")
                
        except ValueError:
            logger.info("Title search didn't find matching episode (expected for unique titles)")

    @pytest.mark.asyncio  
    async def test_comprehensive_episode_analysis_workflow(self, circle_round_feed_url: str, rss_connector: RSSFeedConnector):
        """Test complete workflow: RSS feed → episode selection → metadata → audio URL."""
        logger.info("Testing comprehensive episode analysis workflow...")
        
        # Step 1: Validate RSS feed URL
        assert rss_connector.validate_url(circle_round_feed_url), "RSS feed URL should be valid"
        logger.info("Step 1: RSS feed URL validated")
        
        # Step 2: Get episode metadata with specific selection
        options = AnalysisOptions(
            episode_index=1,  # Select second most recent episode
            language="en",
            max_duration_minutes=30,  # Reasonable limit for testing
            segment_length_seconds=60,
            confidence_threshold=0.5
        )
        
        episode = await rss_connector.get_episode_metadata(circle_round_feed_url, options)
        logger.info(f"Step 2: Episode metadata extracted - '{episode.title}'")
        
        # Step 3: Validate episode structure
        assert isinstance(episode, PodcastEpisode)
        assert episode.platform == "rss"
        assert episode.show_name == "Circle Round"
        assert episode.title and len(episode.title) > 0
        assert episode.episode_id and len(episode.episode_id) > 0
        assert episode.url == circle_round_feed_url
        assert isinstance(episode.metadata, dict)
        assert 'audio_url' in episode.metadata
        logger.info("Step 3: Episode structure validated")
        
        # Step 4: Get audio stream URL
        audio_url = await rss_connector.get_audio_stream_url(episode)
        assert audio_url.startswith('http'), "Audio URL should be valid"
        logger.info(f"Step 4: Audio stream URL obtained - {audio_url[:60]}...")
        
        # Step 5: Validate episode has reasonable duration for Circle Round
        if episode.duration_seconds:
            assert 5*60 <= episode.duration_seconds <= 45*60, \
                f"Circle Round episode duration {episode.duration_seconds}s should be reasonable (5-45 minutes)"
            logger.info(f"Step 5: Duration validated - {episode.duration_seconds}s ({episode.duration_seconds/60:.1f} minutes)")
        
        # Summary
        logger.info("Complete episode analysis workflow successful!")
        logger.info(f"   Show: {episode.show_name}")
        logger.info(f"   Episode: '{episode.title}'")
        logger.info(f"   Duration: {episode.duration_seconds}s" if episode.duration_seconds else "   Duration: Not specified")
        logger.info(f"   Published: {episode.publication_date}")
        logger.info(f"   Audio URL: {audio_url[:100]}...")
        
        return episode

    async def cleanup(self, rss_connector: RSSFeedConnector):
        """Cleanup resources after testing."""
        await rss_connector.cleanup()


@pytest.mark.asyncio
async def test_rss_connector_supports_new_features():
    """Test that RSS connector supports required features for episode selection."""
    connector = RSSFeedConnector()
    
    # Test playlist support (RSS feeds are playlists by nature)
    assert connector.supports_playlist(), "RSS connector should support playlists"
    
    # Test URL validation for various RSS feed formats
    valid_urls = [
        "https://rss.wbur.org/circleround/podcast",
        "http://example.com/feed.xml",
        "https://example.com/podcast.rss",
        "https://feeds.example.com/podcast/feed",
        "https://example.com/rss"
    ]
    
    for url in valid_urls:
        assert connector.validate_url(url), f"URL {url} should be valid RSS feed URL"
    
    invalid_urls = [
        "ftp://example.com/feed.xml",
        "https://example.com/video.mp4", 
        "not-a-url",
        "https://",
        ""
    ]
    
    for url in invalid_urls:
        assert not connector.validate_url(url), f"URL {url} should be invalid RSS feed URL"
    
    await connector.cleanup()
