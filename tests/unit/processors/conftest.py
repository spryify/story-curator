"""Processors test fixtures."""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path


@pytest.fixture
def test_config():
    """Return test configuration."""
    return {
        "audio": {
            "model": "base",
            "device": "cpu",
            "sample_rate": 16000,
            "chunk_size": 30,
            "supported_formats": ["wav", "mp3"],
            "max_duration": 3600  # 1 hour
        },
        "text": {
            "max_summary_length": 1000,
            "min_confidence": 0.8,
            "language": "en"
        }
    }


@pytest.fixture(autouse=True)
def mock_whisper():
    """Mock whisper.load_model for audio processor tests."""
    with patch('whisper.load_model') as mock_load_model:
        # Create a mock model
        mock_model = Mock()
        
        # Mock transcription result with proper structure that includes story elements
        mock_result = {
            'text': 'Once upon a time there was a bunny named Hoppy who lived in a magical forest with a wise owl for format testing that demonstrates speech recognition capabilities.',
            'language': 'en',
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.0,
                    'text': 'Once upon a time there was a bunny named Hoppy',
                    'avg_logprob': -0.2
                },
                {
                    'start': 3.0,
                    'end': 6.0,
                    'text': 'who lived in a magical forest for format testing',
                    'avg_logprob': -0.3
                },
                {
                    'start': 6.0,
                    'end': 9.0,
                    'text': 'that demonstrates speech recognition capabilities.',
                    'avg_logprob': -0.25
                }
            ]
        }
        
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        yield mock_model


@pytest.fixture(autouse=True)
def mock_spacy():
    """Mock spaCy model loading for subject processor tests."""
    with patch('spacy.load') as mock_load:
        mock_nlp = Mock()
        
        # Mock document with entities
        mock_doc = Mock()
        
        # Create comprehensive entity mocks
        entities = [
            Mock(text="Microsoft", label_="ORG"),
            Mock(text="Apple", label_="ORG"),
            Mock(text="Bill Gates", label_="PERSON"),
            Mock(text="Tim Cook", label_="PERSON"),
            Mock(text="Hoppy", label_="PERSON"),
            Mock(text="bunny", label_="ANIMAL"),
            Mock(text="forest", label_="LOCATION"),
            Mock(text="castle", label_="BUILDING"),
            Mock(text="Principal", label_="TITLE"),
            Mock(text="Vice Principal", label_="TITLE"),
        ]
        
        mock_doc.ents = entities
        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp
        yield mock_nlp


@pytest.fixture(autouse=True)  
def mock_subject_identification():
    """Mock subject identification models for all tests."""
    with patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_class:
        mock_instance = Mock()
        
        # Mock identify method to return relevant subjects based on text content
        def mock_identify(text):
            if 'butterfly' in text.lower() or 'garden' in text.lower():
                return ['nature', 'animals', 'children_story', 'friendship']
            elif 'weather' in text.lower() or 'sun' in text.lower():
                return ['education', 'science', 'weather', 'learning']
            else:
                return ['general', 'story']
        
        mock_instance.identify_subjects.side_effect = mock_identify
        mock_class.return_value = mock_instance
        yield mock_instance
