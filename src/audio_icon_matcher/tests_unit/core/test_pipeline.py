"""Unit tests for AudioIconPipeline processor."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

# Mock the spaCy import in IconMatcher before importing
with patch('audio_icon_matcher.processors.icon_matcher.spacy') as mock_spacy:
    # Setup spaCy mock
    mock_nlp = Mock()
    mock_spacy.load.return_value = mock_nlp
    
    # Now safely import the modules
    from audio_icon_matcher.core.pipeline import AudioIconPipeline
    from audio_icon_matcher.processors.icon_matcher import IconMatcher
    from audio_icon_matcher.processors.result_ranker import ResultRanker

# Import other modules that don't have spaCy issues
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
                'keywords': [{'name': 'cat', 'confidence': 0.8}],
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
                'keywords': [
                    {'name': 'animal', 'confidence': 0.8, 'type': 'KEYWORD', 'context': {}},
                    {'name': 'pet', 'confidence': 0.7, 'type': 'KEYWORD', 'context': {}}
                ],
                'topics': [
                    {'name': 'pets', 'confidence': 0.6, 'type': 'TOPIC', 'context': {}}
                ],
                'entities': [
                    {'name': 'dog', 'confidence': 0.9, 'type': 'ENTITY', 'context': {}},
                    {'name': 'cat', 'confidence': 0.8, 'type': 'ENTITY', 'context': {}}
                ],
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
                'keywords': [
                    {'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD', 'context': {}}
                ],
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
    @patch('spacy.load')
    def pipeline(self, mock_spacy_load, mock_audio_processor, mock_subject_identifier):
        """Create pipeline with mocked dependencies."""
        # Mock spaCy model loading
        mock_nlp = Mock()
        mock_spacy_load.return_value = mock_nlp
        
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
        """Test successful pipeline processing with mocks."""
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
        pipeline.audio_processor.validate_file.side_effect = ValueError("Invalid file")
        assert pipeline.validate_audio_file("/invalid/file.wav") is False
    
    def test_get_supported_formats(self, pipeline):
        """Test getting supported formats."""
        formats = pipeline.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "wav" in formats or "mp3" in formats
    
    def test_convert_subject_result_to_rich_dict(self, pipeline, mock_subject_identifier):
        """Test conversion of SubjectAnalysisResult to rich dict format using unified method."""
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
        
        # Convert to rich dict format using unified method
        subjects_dict = pipeline._convert_subjects_to_rich_dict(subject_result)
        
        assert isinstance(subjects_dict, dict)
        assert 'keywords' in subjects_dict
        assert 'topics' in subjects_dict
        assert 'entities' in subjects_dict
        assert 'categories' in subjects_dict
        
        # Check that subjects were properly categorized with rich metadata
        keywords = subjects_dict['keywords']
        topics = subjects_dict['topics']
        
        # Should have at least one keyword entry with rich format
        assert len(keywords) > 0
        keyword = keywords[0]
        assert 'name' in keyword
        assert 'confidence' in keyword
        assert 'type' in keyword
        
        # Topics should be properly formatted
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
            assert "pipeline failed" in result.error.lower()  # More flexible assertion
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
            subjects={
                'keywords': [
                    {'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD', 'context': {}}
                ]
            },
            icon_matches=[],
            processing_time=1.5,
            metadata={'version': '1.0'}
        )
        
        assert result.success is True
        assert result.transcription == "Test transcription"
        assert result.transcription_confidence == 0.9
        assert result.subjects == {
            'keywords': [
                {'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD', 'context': {}}
            ]
        }
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


class TestPodcastUnitTests:
    """Unit tests for podcast functionality with mocks."""
    
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
    
    def test_validate_podcast_url_with_mocks(self):
        """Test podcast URL validation with mocked components."""
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
    
    def test_convert_subjects_to_rich_dict_unit(self):
        """Test the unified subjects conversion method with mocks."""
        pipeline = AudioIconPipeline()
        
        subjects = [
            Subject(name="cat", confidence=0.8, subject_type=SubjectType.KEYWORD),
            Subject(name="animal behavior", confidence=0.7, subject_type=SubjectType.TOPIC),
            Subject(name="Fluffy", confidence=0.6, subject_type=SubjectType.ENTITY)
        ]
        
        result = pipeline._convert_subjects_to_rich_dict(subjects)
        
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
