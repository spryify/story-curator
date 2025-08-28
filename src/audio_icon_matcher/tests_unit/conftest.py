"""Test configuration and fixtures for audio_icon_matcher."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import os

from media_analyzer.models.audio.transcription import TranscriptionResult
from media_analyzer.models.subject.identification import (
    SubjectAnalysisResult, Subject, Category, SubjectType
)
from icon_extractor.models.icon import IconData
from audio_icon_matcher.models.results import IconMatch


@pytest.fixture
def sample_transcription_result():
    """Create a sample TranscriptionResult for testing."""
    return TranscriptionResult(
        text="This is a test audio about cats and music",
        language="en",
        segments=[],
        confidence=0.9,
        metadata={"duration": 10.5}
    )


@pytest.fixture
def sample_subject_analysis_result():
    """Create a sample SubjectAnalysisResult for testing."""
    subjects = {
        Subject(name="cats", confidence=0.8, subject_type=SubjectType.KEYWORD, context=None),
        Subject(name="music", confidence=0.7, subject_type=SubjectType.TOPIC, context=None),
        Subject(name="pets", confidence=0.6, subject_type=SubjectType.ENTITY, context=None)
    }
    
    categories = {
        Category(id="KEYWORD", name="keyword"),
        Category(id="TOPIC", name="topic"),
        Category(id="ENTITY", name="entity")
    }
    
    return SubjectAnalysisResult(
        subjects=subjects,
        categories=categories,
        metadata={"processing_time_ms": 150}
    )


@pytest.fixture
def sample_icon_data():
    """Create sample IconData for testing."""
    return [
        IconData(
            name="Cat Icon",
            url="https://example.com/cat.svg",
            tags=["animal", "pet", "cat"],
            category="Animals",
            description="A cute cat icon"
        ),
        IconData(
            name="Music Note Icon",
            url="https://example.com/music.svg",
            tags=["music", "note", "sound"],
            category="Music",
            description="Musical note icon"
        ),
        IconData(
            name="Pet Care Icon",
            url="https://example.com/petcare.svg",
            tags=["pet", "care", "animal"],
            category="Animals",
            description="Pet care and veterinary icon"
        )
    ]


@pytest.fixture
def sample_icon_matches(sample_icon_data):
    """Create sample IconMatch objects for testing."""
    return [
        IconMatch(
            icon=sample_icon_data[0],
            confidence=0.85,
            match_reason="keyword match: cats",
            subjects_matched=["cats"]
        ),
        IconMatch(
            icon=sample_icon_data[1],
            confidence=0.75,
            match_reason="topic match: music",
            subjects_matched=["music"]
        ),
        IconMatch(
            icon=sample_icon_data[2],
            confidence=0.65,
            match_reason="entity match: pets",
            subjects_matched=["pets"]
        )
    ]


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_audio_processor():
    """Create a mock AudioProcessor for testing."""
    mock_processor = Mock()
    mock_processor.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
    
    def mock_validate_file(file_path):
        return Path(file_path)
    
    mock_processor.validate_file = mock_validate_file
    mock_processor.extract_text.return_value = TranscriptionResult(
        text="Test audio transcription",
        language="en",
        segments=[],
        confidence=0.9,
        metadata={}
    )
    
    return mock_processor


@pytest.fixture
def mock_subject_identifier(sample_subject_analysis_result):
    """Create a mock SubjectIdentifier for testing."""
    mock_identifier = Mock()
    mock_identifier.identify_subjects.return_value = sample_subject_analysis_result
    return mock_identifier


@pytest.fixture
def mock_icon_service(sample_icon_data):
    """Create a mock IconExtractionService for testing."""
    mock_service = Mock()
    mock_service.search_icons.return_value = sample_icon_data
    return mock_service


@pytest.fixture
def subjects_dict():
    """Create a sample subjects dictionary for testing."""
    return {
        'keywords': [
            {'name': 'cats', 'confidence': 0.8},
            {'name': 'test', 'confidence': 0.7}
        ],
        'topics': [
            {'name': 'music', 'confidence': 0.7},
            {'name': 'entertainment', 'confidence': 0.6}
        ],
        'entities': [
            {'name': 'pets', 'confidence': 0.6}
        ],
        'categories': []
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark performance tests
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests
        if any(keyword in item.nodeid.lower() for keyword in ["slow", "large", "concurrent"]):
            item.add_marker(pytest.mark.slow)


# Custom assertions for testing
def assert_valid_audio_icon_result(result):
    """Assert that an AudioIconResult has valid structure."""
    from audio_icon_matcher.models.results import AudioIconResult
    
    assert isinstance(result, AudioIconResult)
    assert isinstance(result.success, bool)
    assert isinstance(result.processing_time, (int, float))
    assert result.processing_time > 0
    
    if result.success:
        assert result.transcription is not None
        assert isinstance(result.transcription_confidence, (int, float))
        assert 0 <= result.transcription_confidence <= 1
        assert isinstance(result.subjects, dict)
        assert isinstance(result.icon_matches, list)
        assert isinstance(result.metadata, dict)
        assert result.error is None
    else:
        assert result.error is not None
        assert isinstance(result.error, str)


def assert_valid_icon_match(match):
    """Assert that an IconMatch has valid structure."""
    from audio_icon_matcher.models.results import IconMatch
    from icon_extractor.models.icon import IconData
    
    assert isinstance(match, IconMatch)
    assert isinstance(match.icon, IconData)
    assert isinstance(match.confidence, (int, float))
    assert 0 <= match.confidence <= 1
    assert isinstance(match.match_reason, str)
    assert isinstance(match.subjects_matched, list)
    assert len(match.subjects_matched) > 0


# Utility functions for tests
def create_test_audio_file(suffix=".wav"):
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        return f.name


def cleanup_test_file(file_path):
    """Clean up a test file safely."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except (OSError, FileNotFoundError):
        pass
