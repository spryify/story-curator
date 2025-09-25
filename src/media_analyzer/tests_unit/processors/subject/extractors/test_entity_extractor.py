"""Unit tests for entity processor using mocked SpaCy models."""
import pytest
from unittest.mock import MagicMock
from media_analyzer.processors.subject.extractors.entity_extractor import EntityExtractor


@pytest.fixture
def mock_entity_processor():
    """Fixture that provides an EntityExtractor with a mocked SpaCy model."""
    # Create a fresh processor instance
    processor = EntityExtractor()
    
    # Store the original nlp for cleanup
    original_nlp = processor.nlp
    
    # Replace with mock
    mock_nlp = MagicMock()
    
    # Create a mock document
    mock_doc = MagicMock()
    
    # Create mock entities
    mock_entity1 = MagicMock()
    mock_entity1.text = "Alice"
    mock_entity1.label_ = "PERSON"
    
    mock_entity2 = MagicMock() 
    mock_entity2.text = "New York"
    mock_entity2.label_ = "GPE"
    
    mock_doc.ents = [mock_entity1, mock_entity2]
    mock_nlp.return_value = mock_doc
    
    # Set the mock
    processor.nlp = mock_nlp
    
    yield processor
    
    # Cleanup: restore original nlp
    processor.nlp = original_nlp


class TestEntityExtractorUnit:
    """Unit test class using a mocked SpaCy model for entity processing."""

    def test_basic_functionality_with_mock_model(self, mock_entity_processor):
        """Test basic entity processing functionality with mocked SpaCy model."""
        text = "Alice went to New York to visit Bob."
        result = mock_entity_processor.process(text)
        
        # Check structure
        assert "metadata" in result
        assert "results" in result
        assert isinstance(result["results"], dict)
        assert result["metadata"]["processor_type"] == "EntityExtractor"
        
        # Check that our mocked entities are returned
        results = result["results"]
        assert "Alice" in results
        assert "New York" in results

    def test_input_validation_mock(self, mock_entity_processor):
        """Test input validation with mocked model."""
        with pytest.raises(ValueError):
            mock_entity_processor.process("")  # Empty text
            
        with pytest.raises(ValueError):
            mock_entity_processor.process(None)  # None input

    def test_mock_entity_processing(self, mock_entity_processor):
        """Test that the mock processor returns expected mock entities."""
        text = "Any text will work with the mock"
        result = mock_entity_processor.process(text)
        results = result["results"]
        
        # Should contain our pre-defined mock entities
        assert "Alice" in results
        assert "New York" in results
        assert len(results) == 2  # Only our two mock entities
        
        # Verify the mock was called
        mock_entity_processor.nlp.assert_called_once_with(text)

    def test_processor_type_metadata(self, mock_entity_processor):
        """Test that processor metadata is correct."""
        text = "Test text"
        result = mock_entity_processor.process(text)
        
        metadata = result["metadata"]
        assert metadata["processor_type"] == "EntityExtractor"
        assert "version" in metadata

    def test_empty_entities_handling(self, mock_entity_processor):
        """Test handling when no entities are found."""
        # Configure mock to return empty entities
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_entity_processor.nlp.return_value = mock_doc
        
        text = "Just some text with no entities"
        result = mock_entity_processor.process(text)
        
        assert "results" in result
        assert len(result["results"]) == 0
