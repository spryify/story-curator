"""Unit tests for podcast analyzer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from media_analyzer.processors.podcast.analyzer import PodcastAnalyzer
from media_analyzer.models.podcast import PodcastEpisode, AnalysisOptions, StreamingAnalysisResult
from media_analyzer.models.audio.transcription import TranscriptionResult
from media_analyzer.models.subject.identification import Subject, SubjectType


@pytest.fixture
def sample_episode():
    """Sample podcast episode for testing."""
    return PodcastEpisode(
        platform="rss",
        episode_id="test123",
        url="https://example.com/feed.xml",
        title="Test Episode",
        description="A test podcast episode",
        duration_seconds=1800,  # 30 minutes
        publication_date=datetime(2025, 8, 29),
        show_name="Test Podcast",
        author="Test Author",
        metadata={"audio_url": "https://example.com/audio.mp3"}
    )


@pytest.fixture
def sample_transcription():
    """Sample transcription result for testing."""
    return TranscriptionResult(
        text="This is a test transcription of a podcast episode about technology.",
        language="en",
        segments=[],
        confidence=0.85,
        metadata={"duration": 1800.0, "service": "whisper"}
    )


@pytest.fixture
def sample_subjects():
    """Sample subjects for testing."""
    return [
        Subject(
            name="technology",
            subject_type=SubjectType.KEYWORD,
            confidence=0.9
        ),
        Subject(
            name="podcast",
            subject_type=SubjectType.KEYWORD,
            confidence=0.8
        )
    ]


class TestPodcastAnalyzer:
    """Test cases for PodcastAnalyzer."""
    
    def test_init(self):
        """Test analyzer initialization."""
        analyzer = PodcastAnalyzer()
        assert analyzer is not None
        assert 'rss' in analyzer.connectors
        assert analyzer.transcription_service is not None
        assert analyzer.subject_identifier is not None
    
    def test_init_with_config(self):
        """Test analyzer initialization with custom config."""
        config = {
            'transcription': {'model_size': 'small'},
            'subject_identification': {'max_workers': 2}
        }
        analyzer = PodcastAnalyzer(config)
        assert analyzer.config == config
    
    def test_get_connector_for_url(self):
        """Test connector selection for different URLs."""
        analyzer = PodcastAnalyzer()
        
        # RSS URLs should return RSS connector
        rss_urls = [
            "https://example.com/feed.xml",
            "https://example.com/podcast.rss",
            "https://example.com/podcast/feed",
            "https://feeds.megaphone.fm/example"
        ]
        
        for url in rss_urls:
            connector = analyzer._get_connector_for_url(url)
            assert connector is not None
            assert connector.platform_name == "rssfeed"
        
        # Invalid URLs should return None
        invalid_urls = [
            "https://example.com/webpage.html",
            "not-a-url",
            ""
        ]
        
        for url in invalid_urls:
            connector = analyzer._get_connector_for_url(url)
            assert connector is None
    
    @pytest.mark.asyncio
    async def test_get_episode_metadata(self, sample_episode):
        """Test episode metadata extraction."""
        analyzer = PodcastAnalyzer()
        
        # Mock the RSS connector - use MagicMock for sync methods, AsyncMock for async methods
        mock_connector = MagicMock()
        mock_connector.validate_url.return_value = True  # Synchronous method
        mock_connector.get_episode_metadata = AsyncMock(return_value=sample_episode)  # Async method
        analyzer.connectors['rss'] = mock_connector
        
        result = await analyzer.get_episode_metadata("https://example.com/feed.xml")
        
        assert result == sample_episode
        mock_connector.get_episode_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_episode_success(self, sample_episode, sample_transcription, sample_subjects):
        """Test successful episode analysis."""
        analyzer = PodcastAnalyzer()
        
        # Mock connector
        mock_connector = AsyncMock()
        mock_connector.validate_url.return_value = True
        mock_connector.get_episode_metadata.return_value = sample_episode
        mock_connector.get_audio_stream_url.return_value = "https://example.com/audio.mp3"
        mock_connector.platform_name = "rss"
        analyzer.connectors['rss'] = mock_connector
        
        # Mock transcription service
        mock_transcription = AsyncMock()
        mock_transcription.transcribe_stream.return_value = sample_transcription
        analyzer.transcription_service = mock_transcription
        
        # Mock subject identifier
        mock_subject_result = MagicMock()
        mock_subject_result.subjects = sample_subjects
        analyzer.subject_identifier = MagicMock()
        analyzer.subject_identifier.identify_subjects.return_value = mock_subject_result
        
        # Run analysis
        options = AnalysisOptions(confidence_threshold=0.7)
        result = await analyzer.analyze_episode("https://example.com/feed.xml", options)
        
        # Verify results
        assert result.success is True
        assert result.episode == sample_episode
        assert result.transcription == sample_transcription
        assert len(result.subjects) == 2  # Both subjects above 0.7 threshold
        assert result.error_message is None
        
        # Verify method calls
        mock_connector.get_episode_metadata.assert_called_once()
        mock_connector.get_audio_stream_url.assert_called_once()
        mock_transcription.transcribe_stream.assert_called_once()
        analyzer.subject_identifier.identify_subjects.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_episode_no_connector(self):
        """Test analysis with unsupported URL."""
        analyzer = PodcastAnalyzer()
        
        result = await analyzer.analyze_episode("https://unsupported.com/file.html")
        
        assert result.success is False
        assert result.error_message is not None
        assert "No connector found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_analyze_episode_duration_limit(self, sample_episode):
        """Test analysis with episode exceeding duration limit."""
        analyzer = PodcastAnalyzer()
        
        # Make episode too long
        long_episode = sample_episode
        long_episode.duration_seconds = 7200  # 2 hours
        
        mock_connector = AsyncMock()
        mock_connector.validate_url.return_value = True
        mock_connector.get_episode_metadata.return_value = long_episode
        analyzer.connectors['rss'] = mock_connector
        
        options = AnalysisOptions(max_duration_minutes=60)  # 1 hour limit
        result = await analyzer.analyze_episode("https://example.com/feed.xml", options)
        
        assert result.success is False
        assert result.error_message is not None
        assert "exceeds limit" in result.error_message
    
    @pytest.mark.asyncio
    async def test_analyze_episode_skip_subjects(self, sample_episode, sample_transcription):
        """Test analysis with subject extraction disabled."""
        analyzer = PodcastAnalyzer()
        
        # Mock connector and transcription
        mock_connector = AsyncMock()
        mock_connector.validate_url.return_value = True
        mock_connector.get_episode_metadata.return_value = sample_episode
        mock_connector.get_audio_stream_url.return_value = "https://example.com/audio.mp3"
        mock_connector.platform_name = "rss"
        analyzer.connectors['rss'] = mock_connector
        
        mock_transcription = AsyncMock()
        mock_transcription.transcribe_stream.return_value = sample_transcription
        analyzer.transcription_service = mock_transcription
        
        # Mock subject identifier  
        mock_subject_identifier = MagicMock()
        analyzer.subject_identifier = mock_subject_identifier
        
        # Run analysis with subjects disabled
        options = AnalysisOptions(subject_extraction=False)
        result = await analyzer.analyze_episode("https://example.com/feed.xml", options)
        
        assert result.success is True
        assert len(result.subjects) == 0
        # Subject identifier should not be called
        mock_subject_identifier.identify_subjects.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test resource cleanup."""
        analyzer = PodcastAnalyzer()
        
        # Mock services with cleanup methods
        mock_transcription = AsyncMock()
        mock_transcription.cleanup = AsyncMock()
        analyzer.transcription_service = mock_transcription
        
        mock_connector = AsyncMock()
        mock_connector.cleanup = AsyncMock()
        analyzer.connectors['test'] = mock_connector
        
        # Run cleanup
        await analyzer.cleanup()
        
        # Verify cleanup was called
        mock_transcription.cleanup.assert_called_once()
        mock_connector.cleanup.assert_called_once()


class TestAnalysisOptions:
    """Test cases for AnalysisOptions."""
    
    def test_defaults(self):
        """Test default option values."""
        options = AnalysisOptions()
        assert options.language == "en"
        assert options.transcription_service == "whisper"
        assert options.subject_extraction is True
        assert options.icon_matching is True
        assert options.max_duration_minutes == 180
        assert options.segment_length_seconds == 300
        assert options.confidence_threshold == 0.5
    
    def test_validation_errors(self):
        """Test option validation."""
        # Invalid duration
        with pytest.raises(ValueError, match="max_duration_minutes must be positive"):
            AnalysisOptions(max_duration_minutes=0)
        
        # Invalid segment length
        with pytest.raises(ValueError, match="segment_length_seconds must be positive"):
            AnalysisOptions(segment_length_seconds=-1)
        
        # Invalid confidence threshold
        with pytest.raises(ValueError, match="confidence_threshold must be between 0 and 1"):
            AnalysisOptions(confidence_threshold=1.5)
        
        with pytest.raises(ValueError, match="confidence_threshold must be between 0 and 1"):
            AnalysisOptions(confidence_threshold=-0.1)
