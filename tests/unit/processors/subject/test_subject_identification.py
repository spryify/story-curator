"""
Tests for the subject identification feature.
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from media_analyzer.processors.subject.models import Subject, Category, Context, SubjectType
from media_analyzer.processors.subject.identifier import SubjectIdentifier, ProcessingError
from media_analyzer.processors.subject.processors.lda import TopicProcessor
from media_analyzer.processors.subject.processors.ner import EntityProcessor
from media_analyzer.processors.subject.processors.keywords import KeywordProcessor


@pytest.fixture
def subject_identifier():
    """Create a SubjectIdentifier instance for testing."""
    return SubjectIdentifier()


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return """
    Microsoft and Apple are leading technology companies. Their CEOs, Satya Nadella
    and Tim Cook, regularly discuss artificial intelligence and cloud computing. 
    Both companies are investing heavily in machine learning technology.
    """


@pytest.fixture
def mock_processors():
    """Create mock processors for testing."""
    with patch('media_analyzer.processors.subject.identifier.TopicProcessor') as mock_topic, \
         patch('media_analyzer.processors.subject.identifier.EntityProcessor') as mock_ner, \
         patch('media_analyzer.processors.subject.identifier.KeywordProcessor') as mock_keyword:
        
        # Configure mock responses
        mock_topic.return_value.process.return_value = {
            "results": [
                {"name": "technology companies", "score": 0.8},
                {"name": "artificial intelligence", "score": 0.7}
            ]
        }
        
        mock_ner.return_value.process.return_value = {
            "results": [
                {"name": "Microsoft", "score": 1.0},
                {"name": "Apple", "score": 1.0},
                {"name": "Satya Nadella", "score": 1.0}
            ]
        }
        
        mock_keyword.return_value.process.return_value = {
            "results": [
                {"name": "cloud computing", "score": 0.9},
                {"name": "machine learning", "score": 0.85}
            ]
        }
        
        yield {
            "topic": mock_topic,
            "ner": mock_ner,
            "keyword": mock_keyword
        }


def test_subject_identification_empty_text(subject_identifier):
    """Test that empty text raises ValueError."""
    with pytest.raises(ValueError):
        subject_identifier.identify_subjects("")
        
    with pytest.raises(ValueError):
        subject_identifier.identify_subjects("   ")


def test_subject_identification_success(subject_identifier, sample_text, mock_processors):
    """Test successful subject identification with all processors."""
    result = subject_identifier.identify_subjects(sample_text)
    
    # Verify result structure
    assert result.subjects is not None
    assert result.categories is not None
    assert result.metadata is not None
    
    # Verify subjects were extracted from all processors
    subject_names = {s.name for s in result.subjects}
    assert "Microsoft" in subject_names
    assert "technology companies" in subject_names
    assert "cloud computing" in subject_names
    
    # Verify categories were created
    category_names = {c.name for c in result.categories}
    assert "entity" in category_names
    assert "topic" in category_names
    assert "keyword" in category_names


def test_subject_identification_with_context(subject_identifier, sample_text):
    """Test subject identification with context information."""
    context = Context(
        domain="technology",
        language="en",
        confidence=1.0
    )
    
    result = subject_identifier.identify_subjects(sample_text, context)
    
    # Verify context is properly attached
    for subject in result.subjects:
        assert subject.context == context


def test_subject_identification_processor_failure(subject_identifier, sample_text):
    """Test handling of processor failures."""
    with patch('media_analyzer.processors.subject.identifier.TopicProcessor') as mock_topic:
        # Make the topic processor fail
        mock_topic.return_value.process.side_effect = Exception("Topic processing failed")
        
        # Should still get results from other processors
        result = subject_identifier.identify_subjects(sample_text)
        assert result.subjects  # Should have subjects from NER and keyword processors
        assert "topic_error" in result.metadata


def test_topic_processor():
    """Test the TopicProcessor independently."""
    processor = TopicProcessor()
    result = processor.process("This is a sample text about technology and science")
    
    assert "results" in result
    assert "metadata" in result
    assert result["metadata"]["num_topics"] == 5


def test_entity_processor():
    """Test the EntityProcessor independently."""
    processor = EntityProcessor()
    result = processor.process("Microsoft was founded by Bill Gates")
    
    assert "results" in result
    assert "metadata" in result
    assert any(r["name"] == "Microsoft" for r in result["results"])
    assert any(r["name"] == "Bill Gates" for r in result["results"])


def test_keyword_processor():
    """Test the KeywordProcessor independently."""
    processor = KeywordProcessor()
    result = processor.process("Artificial intelligence and machine learning are key technologies")
    
    assert "results" in result
    assert "metadata" in result
    assert any("artificial intelligence" in r["name"].lower() for r in result["results"])
    assert any("machine learning" in r["name"].lower() for r in result["results"])
