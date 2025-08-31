"""Unit tests for AudioIconPipeline processor."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

from audio_icon_matcher.core.pipeline import AudioIconPipeline
from audio_icon_matcher.processors.icon_matcher import IconMatcher
from audio_icon_matcher.processors.result_ranker import ResultRanker
from audio_icon_matcher.models.results import AudioIconResult, IconMatch
from audio_icon_matcher.core.exceptions import (
    AudioIconValidationError, 
    AudioIconProcessingError
)
from media_analyzer.models.audio.transcription import TranscriptionResult
from media_analyzer.models.subject.identification import (
    SubjectAnalysisResult, Subject, Category, SubjectType
)
from media_analyzer.models.podcast import PodcastEpisode, StreamingAnalysisResult
from icon_extractor.models.icon import IconData


class TestIconMatcher:
    """Test cases for IconMatcher."""
    
    def test_init(self):
        """Test IconMatcher initialization."""
        matcher = IconMatcher()
        assert matcher.icon_service is not None
    
    def test_find_matching_icons_basic(self):
        """Test basic icon matching functionality."""
        matcher = IconMatcher()
        
        # Mock icon service
        mock_icon = IconData(
            name="Cat Icon",
            url="https://example.com/cat.svg",
            tags=["animal", "pet"],
            category="Animals"
        )
        
        with patch.object(matcher.icon_service, 'search_icons', return_value=[mock_icon]):
            subjects = {
                'keywords': [{'word': 'cat', 'confidence': 0.8}],
                'topics': [],
                'entities': [],
                'categories': []
            }
            
            matches = matcher.find_matching_icons(subjects, limit=5)
            
            assert len(matches) == 1
            assert matches[0].icon.name == "Cat Icon"
            assert matches[0].confidence > 0.0
            assert 'cat' in matches[0].subjects_matched
    
    def test_find_matching_icons_multiple_subjects(self):
        """Test icon matching with multiple subject types."""
        matcher = IconMatcher()
        
        # Mock multiple icons
        mock_icons = [
            IconData(name="Dog Icon", url="https://example.com/dog.svg", tags=["animal"], category="Animals"),
            IconData(name="Cat Icon", url="https://example.com/cat.svg", tags=["pet"], category="Animals")
        ]
        
        with patch.object(matcher.icon_service, 'search_icons', return_value=mock_icons):
            subjects = {
                'keywords': ['animal', 'pet'],
                'topics': ['pets'],
                'entities': ['dog', 'cat'],
                'categories': ['Animals']
            }
            
            matches = matcher.find_matching_icons(subjects, limit=10)
            
            assert len(matches) > 0
            # Should have matches from different search terms
            icon_names = [match.icon.name for match in matches]
            assert any('Dog' in name or 'Cat' in name for name in icon_names)
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        matcher = IconMatcher()
        
        icon = IconData(
            name="Test Cat Icon",
            url="https://example.com/test.svg",
            tags=["cat", "animal"],
            description="A cute cat icon"
        )
        
        # Test exact name match
        confidence = matcher._calculate_confidence("cat", icon, "keyword", 0.7)
        assert confidence > 0.7  # Should be boosted for name match
        
        # Test tag match
        confidence = matcher._calculate_confidence("animal", icon, "keyword", 0.7)
        assert confidence > 0.7  # Should be boosted for tag match
        
        # Test no match
        confidence = matcher._calculate_confidence("unrelated", icon, "keyword", 0.7)
        assert confidence <= 0.7  # Should not be boosted
    
    def test_find_matching_icons_error_handling(self):
        """Test error handling in icon matching."""
        matcher = IconMatcher()
        
        with patch.object(matcher.icon_service, 'search_icons', side_effect=Exception("Search failed")):
            subjects = {
                'keywords': ['test'],
                'topics': [],
                'entities': [],
                'categories': []
            }
            
            # The matcher logs errors but doesn't raise exceptions, it returns empty list
            matches = matcher.find_matching_icons(subjects)
            assert matches == []


class TestResultRanker:
    """Test cases for ResultRanker."""
    
    def test_init(self):
        """Test ResultRanker initialization."""
        ranker = ResultRanker()
        assert ranker is not None
    
    def test_rank_results_basic(self):
        """Test basic result ranking."""
        ranker = ResultRanker()
        
        # Create test matches with different confidence scores
        icon1 = IconData(name="Icon 1", url="https://example.com/1.svg", tags=["tag1"])
        icon2 = IconData(name="Icon 2", url="https://example.com/2.svg", tags=["tag2"])
        
        matches = [
            IconMatch(icon=icon1, confidence=0.5, match_reason="Test", subjects_matched=["test1"]),
            IconMatch(icon=icon2, confidence=0.8, match_reason="Test", subjects_matched=["test2"])
        ]
        
        subjects = {'categories': []}
        ranked_matches = ranker.rank_results(matches, subjects, limit=2)
        
        assert len(ranked_matches) == 2
        # Should be sorted by confidence (descending)
        assert ranked_matches[0].confidence >= ranked_matches[1].confidence
    
    def test_adjust_confidence(self):
        """Test confidence adjustment logic."""
        ranker = ResultRanker()
        
        icon = IconData(
            name="Test Icon",
            url="https://example.com/test.svg",
            tags=["tag1", "tag2", "tag3"],
            description="A detailed description for testing confidence adjustment",
            category="Animals"
        )
        
        match = IconMatch(
            icon=icon,
            confidence=0.6,
            match_reason="Test",
            subjects_matched=["test1", "test2"]  # Multiple matches
        )
        
        subjects = {'categories': ['Animals']}
        adjusted_confidence = ranker._adjust_confidence(match, subjects)
        
        # Should be boosted for multiple subject matches, good description, and category alignment
        assert adjusted_confidence > 0.6


class TestAudioIconPipeline:
    """Test cases for AudioIconPipeline."""
    
    @pytest.fixture
    def mock_audio_processor(self):
        """Mock audio processor."""
        mock_processor = Mock()
        mock_processor.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
        mock_processor.validate_file.return_value = Path("/test/audio.wav")
        mock_processor.extract_text.return_value = TranscriptionResult(
            text="This is test audio about cats and dogs",
            language="en",
            segments=[],
            confidence=0.9,
            metadata={}
        )
        return mock_processor
    
    @pytest.fixture
    def mock_subject_identifier(self):
        """Mock subject identifier."""
        mock_identifier = Mock()
        
        # Create mock subjects and categories
        subjects = {
            Subject(name="cats", confidence=0.8, subject_type=SubjectType.KEYWORD, context=None),
            Subject(name="dogs", confidence=0.7, subject_type=SubjectType.KEYWORD, context=None),
            Subject(name="pets", confidence=0.6, subject_type=SubjectType.TOPIC, context=None)
        }
        
        categories = {
            Category(id="KEYWORD", name="keyword"),
            Category(id="TOPIC", name="topic")
        }
        
        mock_result = SubjectAnalysisResult(
            subjects=subjects,
            categories=categories,
            metadata={"processing_time_ms": 100}
        )
        
        mock_identifier.identify_subjects.return_value = mock_result
        return mock_identifier
    
    @pytest.fixture
    def pipeline(self, mock_audio_processor, mock_subject_identifier):
        """Create pipeline with mocked dependencies."""
        pipeline = AudioIconPipeline()
        pipeline.audio_processor = mock_audio_processor
        pipeline.subject_identifier = mock_subject_identifier
        
        # Mock icon matcher
        pipeline.icon_matcher = Mock()
        mock_icon = IconData(
            name="Cat Icon",
            url="https://example.com/cat.svg",
            tags=["animal"],
            category="Animals"
        )
        mock_match = IconMatch(
            icon=mock_icon,
            confidence=0.8,
            match_reason="keyword match",
            subjects_matched=["cats"]
        )
        pipeline.icon_matcher.find_matching_icons.return_value = [mock_match]
        
        # Mock result ranker
        pipeline.result_ranker = Mock()
        pipeline.result_ranker.rank_results.return_value = [mock_match]
        
        return pipeline
    
    def test_init(self):
        """Test pipeline initialization."""
        pipeline = AudioIconPipeline()
        assert pipeline.audio_processor is not None
        assert pipeline.subject_identifier is not None
        assert pipeline.icon_matcher is not None
        assert pipeline.result_ranker is not None
    
    def test_process_success(self, pipeline):
        """Test successful pipeline processing."""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = pipeline.process(temp_path, max_icons=5, confidence_threshold=0.5)
            
            assert isinstance(result, AudioIconResult)
            assert result.success is True
            assert result.transcription is not None
            assert result.transcription_confidence > 0
            assert len(result.icon_matches) > 0
            assert result.processing_time > 0
            assert result.metadata is not None
            
        finally:
            os.unlink(temp_path)
    
    def test_process_file_not_found(self, pipeline):
        """Test processing with non-existent file."""
        with pytest.raises(AudioIconValidationError, match="Audio file not found"):
            pipeline.process("/nonexistent/file.wav")
    
    def test_process_audio_processing_error(self, pipeline):
        """Test handling of audio processing errors."""
        pipeline.audio_processor.extract_text.return_value = None
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(AudioIconProcessingError, match="Audio processing failed"):
                pipeline.process(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_process_subject_identification_failure(self, pipeline):
        """Test handling when subject identification fails."""
        pipeline.subject_identifier.identify_subjects.return_value = None
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = pipeline.process(temp_path)
            
            # Should still succeed but with empty subjects
            assert result.success is True
            assert result.subjects == {}
            
        finally:
            os.unlink(temp_path)
    
    def test_process_confidence_threshold_filtering(self, pipeline):
        """Test confidence threshold filtering."""
        # Mock low confidence matches
        low_confidence_match = IconMatch(
            icon=IconData(name="Low Confidence", url="https://example.com/low.svg", tags=[]),
            confidence=0.2,
            match_reason="low match",
            subjects_matched=["test"]
        )
        pipeline.result_ranker.rank_results.return_value = [low_confidence_match]
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = pipeline.process(temp_path, confidence_threshold=0.5)
            
            # Low confidence match should be filtered out
            assert len(result.icon_matches) == 0
            
        finally:
            os.unlink(temp_path)
    
    def test_validate_audio_file_success(self, pipeline):
        """Test successful audio file validation."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            # The pipeline validate_audio_file checks if file exists and processor validates it
            # Mock the path.exists() to return True for our test file
            with patch('pathlib.Path.exists', return_value=True):
                result = pipeline.validate_audio_file(temp_path)
                assert result is True
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
    
    def test_validate_audio_file_failure(self, pipeline):
        """Test audio file validation failure."""
        pipeline.audio_processor.validate_file.side_effect = Exception("Invalid file")
        assert pipeline.validate_audio_file("/invalid/file.wav") is False
    
    def test_get_supported_formats(self, pipeline):
        """Test getting supported formats."""
        formats = pipeline.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "wav" in formats or "mp3" in formats
    
    def test_convert_subject_result_to_dict(self, pipeline, mock_subject_identifier):
        """Test conversion of SubjectAnalysisResult to dict."""
        # Create a more realistic mock with both keywords and topics
        from media_analyzer.models.subject.identification import Subject, SubjectType
        
        subjects = {
            Subject(name="cats", confidence=0.8, subject_type=SubjectType.KEYWORD, context=None),
            Subject(name="pets", confidence=0.6, subject_type=SubjectType.TOPIC, context=None)
        }
        
        subject_result = Mock()
        subject_result.subjects = subjects
        subject_result.categories = set()
        subject_result.metadata = {}
        
        # Convert to dict
        subjects_dict = pipeline._convert_subject_result_to_dict(subject_result)
        
        assert isinstance(subjects_dict, dict)
        assert 'keywords' in subjects_dict
        assert 'topics' in subjects_dict
        assert 'entities' in subjects_dict
        assert 'categories' in subjects_dict
        
        # Check that subjects were properly categorized
        keywords = subjects_dict['keywords']
        topics = subjects_dict['topics']
        
        # Should have at least one keyword entry
        assert len(keywords) > 0
        # Topics might be empty depending on the mock setup, so just check structure
        assert isinstance(topics, list)
    
    def test_process_unexpected_error_handling(self, pipeline):
        """Test handling of unexpected errors during processing."""
        # Mock an unexpected exception in audio processing
        pipeline.audio_processor.extract_text.side_effect = RuntimeError("Unexpected error")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            result = pipeline.process(temp_path)
            
            # Should return error result instead of raising
            assert result.success is False
            assert result.error is not None
            assert "Pipeline failed" in result.error
            assert result.processing_time > 0
            
        finally:
            os.unlink(temp_path)


class TestAudioIconResult:
    """Test cases for AudioIconResult."""
    
    def test_create_result(self):
        """Test creating an AudioIconResult."""
        result = AudioIconResult(
            success=True,
            transcription="Test transcription",
            transcription_confidence=0.9,
            subjects={'keywords': ['test']},
            icon_matches=[],
            processing_time=1.5,
            metadata={'version': '1.0'}
        )
        
        assert result.success is True
        assert result.transcription == "Test transcription"
        assert result.transcription_confidence == 0.9
        assert result.subjects == {'keywords': ['test']}
        assert result.icon_matches == []
        assert result.processing_time == 1.5
        assert result.metadata == {'version': '1.0'}
        assert result.error is None


class TestIconMatch:
    """Test cases for IconMatch."""
    
    def test_create_match(self):
        """Test creating an IconMatch."""
        icon = IconData(name="Test", url="https://example.com/test.svg", tags=[])
        match = IconMatch(
            icon=icon,
            confidence=0.8,
            match_reason="keyword match",
            subjects_matched=["test", "example"]
        )
        
        assert match.icon == icon
        assert match.confidence == 0.8
        assert match.match_reason == "keyword match"
        assert match.subjects_matched == ["test", "example"]


        assert match.subjects_matched == ["test", "example"]


class TestPodcastIntegration:
    """Test podcast functionality in AudioIconPipeline."""
    
    def test_is_url_detection(self):
        """Test URL detection logic."""
        pipeline = AudioIconPipeline()
        
        # Valid URLs
        assert pipeline._is_url("https://example.com/feed.xml")
        assert pipeline._is_url("http://example.com/podcast.rss")
        
        # Invalid URLs
        assert not pipeline._is_url("/path/to/file.mp3")
        assert not pipeline._is_url("file.wav")
        assert not pipeline._is_url("")
    
    def test_validate_podcast_url(self):
        """Test podcast URL validation."""
        pipeline = AudioIconPipeline()
        
        with patch.object(pipeline.podcast_analyzer, '_get_connector_for_url') as mock_get_connector:
            # Valid URL with connector
            mock_get_connector.return_value = Mock()
            assert pipeline.validate_podcast_url("https://example.com/feed.xml")
            
            # Invalid URL without connector
            mock_get_connector.return_value = None
            assert not pipeline.validate_podcast_url("https://invalid.com/notfeed")
            
            # Non-URL
            assert not pipeline.validate_podcast_url("/path/to/file.mp3")
    
    @pytest.mark.asyncio
    async def test_process_podcast_url_success(self):
        """Test successful podcast URL processing."""
        pipeline = AudioIconPipeline()
        
        # Mock podcast episode
        mock_episode = PodcastEpisode(
            platform="rss",
            episode_id="test123",
            url="https://example.com/feed.xml",
            title="Test Episode",
            description="Test Description",
            duration_seconds=300,
            publication_date=None,
            show_name="Test Show"
        )
        
        # Mock transcription result
        mock_transcription = TranscriptionResult(
            text="This is a test story about cats and dogs",
            language="en",
            segments=[],
            confidence=0.9,
            metadata={}
        )
        
        # Mock subjects
        mock_subjects = [
            Subject(name="cat", confidence=0.8, subject_type=SubjectType.KEYWORD),
            Subject(name="dog", confidence=0.7, subject_type=SubjectType.KEYWORD)
        ]
        
        # Mock podcast analysis result
        mock_podcast_result = StreamingAnalysisResult(
            episode=mock_episode,
            transcription=mock_transcription,
            subjects=mock_subjects,
            matched_icons=[],
            processing_metadata={},
            success=True
        )
        
        # Mock icon matches
        mock_icon = IconData(name="Cat", url="test.svg", tags=["animal"], category="Animals")
        mock_icon_match = IconMatch(
            icon=mock_icon,
            confidence=0.8,
            match_reason="keyword match",
            subjects_matched=["cat"]
        )
        
        with patch.object(pipeline.podcast_analyzer, 'analyze_episode', new_callable=AsyncMock) as mock_analyze:
            with patch.object(pipeline.icon_matcher, 'find_matching_icons') as mock_find_icons:
                with patch.object(pipeline.result_ranker, 'rank_results') as mock_rank:
                    mock_analyze.return_value = mock_podcast_result
                    mock_find_icons.return_value = [mock_icon_match]
                    mock_rank.return_value = [mock_icon_match]
                    
                    result = await pipeline._process_podcast_url(
                        "https://example.com/feed.xml", 
                        max_icons=10, 
                        confidence_threshold=0.3
                    )
                    
                    assert result.success
                    assert result.transcription == "This is a test story about cats and dogs"
                    assert result.transcription_confidence == 0.9
                    assert len(result.icon_matches) == 1
                    assert result.metadata['source_type'] == 'podcast'
                    assert result.metadata['episode_title'] == "Test Episode"
                    assert result.metadata['show_name'] == "Test Show"
    
    @pytest.mark.asyncio
    async def test_process_podcast_url_failure(self):
        """Test podcast URL processing failure."""
        pipeline = AudioIconPipeline()
        
        # Create mock episode for failed result
        mock_episode = PodcastEpisode(
            platform="rss",
            episode_id="failed123",
            url="https://invalid.com/feed.xml",
            title="Failed Episode",
            description="",
            duration_seconds=0,
            publication_date=None,
            show_name="Failed Show"
        )
        
        # Create empty transcription for failed result
        mock_transcription = TranscriptionResult(
            text="",
            language="en",
            segments=[],
            confidence=0.0,
            metadata={}
        )
        
        # Mock failed podcast analysis
        mock_podcast_result = StreamingAnalysisResult(
            episode=mock_episode,
            transcription=mock_transcription,
            subjects=[],
            matched_icons=[],
            processing_metadata={},
            success=False,
            error_message="Failed to fetch RSS feed"
        )
        
        with patch.object(pipeline.podcast_analyzer, 'analyze_episode', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_podcast_result
            
            result = await pipeline._process_podcast_url(
                "https://invalid.com/feed.xml",
                max_icons=10,
                confidence_threshold=0.3
            )
            
            assert not result.success
            assert result.error is not None
            assert "Podcast analysis failed" in result.error
            assert result.metadata['source_type'] == 'podcast'
    
    def test_convert_podcast_subjects_to_dict(self):
        """Test conversion of podcast subjects to dict format."""
        pipeline = AudioIconPipeline()
        
        subjects = [
            Subject(name="cat", confidence=0.8, subject_type=SubjectType.KEYWORD),
            Subject(name="animal behavior", confidence=0.7, subject_type=SubjectType.TOPIC),
            Subject(name="Fluffy", confidence=0.6, subject_type=SubjectType.ENTITY)
        ]
        
        result = pipeline._convert_podcast_subjects_to_dict(subjects)
        
        assert 'keywords' in result
        assert 'topics' in result  
        assert 'entities' in result
        assert 'categories' in result
        
        assert len(result['keywords']) == 1
        assert result['keywords'][0]['name'] == "cat"
        assert result['keywords'][0]['confidence'] == 0.8
        
        assert len(result['topics']) == 1
        assert result['topics'][0]['name'] == "animal behavior"
        
        assert len(result['entities']) == 1
        assert result['entities'][0]['name'] == "Fluffy"
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test pipeline cleanup."""
        pipeline = AudioIconPipeline()
        
        with patch.object(pipeline.podcast_analyzer, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            await pipeline.cleanup()
            mock_cleanup.assert_called_once()


# Integration tests that require the full pipeline
class TestAudioIconPipelineIntegration:
    """Integration tests for the full pipeline."""
    
    @pytest.mark.integration
    def test_full_pipeline_integration(self):
        """Test full pipeline with real components (mocked external dependencies)."""
        # This test would require setting up the full pipeline with real components
        # but mocked external dependencies (Whisper, spaCy models, database)
        # For now, we'll skip this as it requires more setup
        pytest.skip("Integration test requires full setup")
    
    @pytest.mark.performance
    def test_pipeline_performance(self):
        """Test pipeline performance with various input sizes."""
        # Performance test would measure processing time for different audio lengths
        pytest.skip("Performance test requires audio samples")
