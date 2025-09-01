"""Unit tests for RSS connector episode selection functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import xml.etree.ElementTree as ET
from datetime import datetime

from media_analyzer.processors.podcast.rss_connector import RSSFeedConnector
from media_analyzer.models.podcast import AnalysisOptions
from media_analyzer.core.exceptions import ValidationError


class TestRSSConnectorEpisodeSelectionUnit:
    """Unit tests for RSS connector episode selection."""

    @pytest.fixture
    def rss_connector(self):
        """Create RSS connector instance."""
        return RSSFeedConnector()

    @pytest.fixture
    def sample_rss_xml(self):
        """Sample RSS feed XML with multiple episodes."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
          <channel>
            <title>Test Podcast</title>
            <description>A test podcast feed</description>
            <itunes:author>Test Author</itunes:author>
            <item>
              <title>Latest Episode</title>
              <description>The most recent episode</description>
              <enclosure url="https://example.com/latest.mp3" length="12345" type="audio/mpeg"/>
              <guid>latest-episode</guid>
              <pubDate>Fri, 30 Aug 2025 10:00:00 GMT</pubDate>
              <itunes:duration>1800</itunes:duration>
            </item>
            <item>
              <title>Previous Episode</title>
              <description>The previous episode</description>
              <enclosure url="https://example.com/previous.mp3" length="23456" type="audio/mpeg"/>
              <guid>previous-episode</guid>
              <pubDate>Thu, 29 Aug 2025 10:00:00 GMT</pubDate>
              <itunes:duration>1900</itunes:duration>
            </item>
            <item>
              <title>First Episode Ever</title>
              <description>The very first episode</description>
              <enclosure url="https://example.com/first.mp3" length="34567" type="audio/mpeg"/>
              <guid>first-episode</guid>
              <pubDate>Wed, 28 Aug 2025 10:00:00 GMT</pubDate>
              <itunes:duration>2000</itunes:duration>
            </item>
          </channel>
        </rss>"""

    def test_select_episode_default(self, rss_connector, sample_rss_xml):
        """Test default episode selection (most recent)."""
        episode = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml")
        
        assert episode.title == "Latest Episode"
        assert episode.episode_id == "latest-episode"
        assert episode.metadata['audio_url'] == "https://example.com/latest.mp3"

    def test_select_episode_by_index(self, rss_connector, sample_rss_xml):
        """Test episode selection by index."""
        # Test index 0 (most recent)
        options_0 = AnalysisOptions(episode_index=0)
        episode_0 = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_0)
        assert episode_0.title == "Latest Episode"
        
        # Test index 1
        options_1 = AnalysisOptions(episode_index=1)
        episode_1 = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_1)
        assert episode_1.title == "Previous Episode"
        
        # Test index 2
        options_2 = AnalysisOptions(episode_index=2)
        episode_2 = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_2)
        assert episode_2.title == "First Episode Ever"

    def test_select_episode_by_title(self, rss_connector, sample_rss_xml):
        """Test episode selection by title."""
        # Test exact title match
        options_exact = AnalysisOptions(episode_title="Previous Episode")
        episode_exact = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_exact)
        assert episode_exact.title == "Previous Episode"
        assert episode_exact.episode_id == "previous-episode"
        
        # Test partial title match
        options_partial = AnalysisOptions(episode_title="First")
        episode_partial = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_partial)
        assert episode_partial.title == "First Episode Ever"
        
        # Test case insensitive match
        options_case = AnalysisOptions(episode_title="LATEST")
        episode_case = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_case)
        assert episode_case.title == "Latest Episode"

    def test_select_episode_invalid_index(self, rss_connector, sample_rss_xml):
        """Test error handling for invalid episode index."""
        options_invalid = AnalysisOptions(episode_index=10)  # Only 3 episodes in feed
        
        with pytest.raises(ValueError) as exc_info:
            rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_invalid)
        
        assert "Episode index 10 not found" in str(exc_info.value)
        assert "has 3 episodes" in str(exc_info.value)

    def test_select_episode_invalid_title(self, rss_connector, sample_rss_xml):
        """Test error handling for non-existent episode title."""
        options_invalid = AnalysisOptions(episode_title="Nonexistent Episode")
        
        with pytest.raises(ValueError) as exc_info:
            rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options_invalid)
        
        assert "Episode with title 'Nonexistent Episode' not found" in str(exc_info.value)

    def test_select_episode_from_items_unit(self, rss_connector, sample_rss_xml):
        """Test the _select_episode_from_items method directly."""
        root = ET.fromstring(sample_rss_xml)
        channel = root.find('channel')
        assert channel is not None, "Channel should exist in RSS feed"
        items = channel.findall('item')
        
        # Test default selection (None options)
        selected_default = rss_connector._select_episode_from_items(items, None)
        title_default = rss_connector._get_text(selected_default, 'title')
        assert title_default == "Latest Episode"
        
        # Test index selection
        options_index = AnalysisOptions(episode_index=1)
        selected_index = rss_connector._select_episode_from_items(items, options_index)
        title_index = rss_connector._get_text(selected_index, 'title')
        assert title_index == "Previous Episode"
        
        # Test title selection
        options_title = AnalysisOptions(episode_title="Ever")
        selected_title = rss_connector._select_episode_from_items(items, options_title)
        title_title = rss_connector._get_text(selected_title, 'title')
        assert title_title == "First Episode Ever"

    def test_url_validation(self, rss_connector):
        """Test RSS URL validation."""
        # Valid RSS URLs
        valid_urls = [
            "https://example.com/feed.xml",
            "http://example.com/podcast.rss",
            "https://feeds.example.com/rss",
            "https://example.com/feed",
            "https://example.com/rss/podcast"
        ]
        
        for url in valid_urls:
            assert rss_connector.validate_url(url), f"URL {url} should be valid"
        
        # Invalid URLs
        invalid_urls = [
            "ftp://example.com/feed.xml",  # Wrong protocol
            "https://example.com/video.mp4",  # Not RSS-like
            "not-a-url",  # Invalid format
            ""  # Empty string
        ]
        
        for url in invalid_urls:
            assert not rss_connector.validate_url(url), f"URL {url} should be invalid"

    def test_playlist_support(self, rss_connector):
        """Test playlist support indication."""
        assert rss_connector.supports_playlist() is True, "RSS feeds should support playlists"

    def test_episode_metadata_extraction(self, rss_connector, sample_rss_xml):
        """Test that episode metadata is properly extracted."""
        options = AnalysisOptions(episode_index=1)
        episode = rss_connector._parse_rss_feed(sample_rss_xml, "https://example.com/feed.xml", options)
        
        # Check basic episode properties
        assert episode.platform == "rss"
        assert episode.episode_id == "previous-episode"
        assert episode.title == "Previous Episode"
        assert episode.description == "The previous episode"
        assert episode.show_name == "Test Podcast"
        assert episode.author == "Test Author"
        assert episode.url == "https://example.com/feed.xml"
        assert episode.duration_seconds == 1900
        
        # Check metadata
        assert episode.metadata is not None
        assert episode.metadata['audio_url'] == "https://example.com/previous.mp3"
        assert episode.metadata['audio_type'] == "audio/mpeg"
        assert episode.metadata['audio_length'] == 23456
        assert episode.metadata['feed_url'] == "https://example.com/feed.xml"

    def test_html_cleaning(self, rss_connector):
        """Test HTML tag removal from descriptions."""
        html_text = "<p>This is a <strong>test</strong> description with <a href='#'>links</a></p>"
        cleaned_text = rss_connector._clean_html(html_text)
        assert cleaned_text == "This is a test description with links"

    def test_duration_parsing(self, rss_connector):
        """Test duration string parsing."""
        # Test HH:MM:SS format
        assert rss_connector._parse_duration("01:30:45") == 5445  # 1h 30m 45s
        
        # Test MM:SS format
        assert rss_connector._parse_duration("15:30") == 930  # 15m 30s
        
        # Test seconds only
        assert rss_connector._parse_duration("300") == 300
        
        # Test invalid format
        assert rss_connector._parse_duration("invalid") is None
        
        # Test empty string
        assert rss_connector._parse_duration("") is None

    def test_episode_id_generation(self, rss_connector):
        """Test episode ID generation."""
        audio_url = "https://example.com/audio.mp3"
        title = "Test Episode"
        
        episode_id = rss_connector._generate_episode_id(audio_url, title)
        
        assert isinstance(episode_id, str)
        assert len(episode_id) == 16  # MD5 hash truncated to 16 chars
        
        # Same inputs should generate same ID
        episode_id_2 = rss_connector._generate_episode_id(audio_url, title)
        assert episode_id == episode_id_2
        
        # Different inputs should generate different IDs
        episode_id_3 = rss_connector._generate_episode_id(audio_url, "Different Title")
        assert episode_id != episode_id_3
