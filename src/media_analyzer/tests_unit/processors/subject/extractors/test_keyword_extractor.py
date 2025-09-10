"""Tests for keyword processor - Unit tests focusing on code structure and logic."""
import pytest
import time
from unittest.mock import Mock, patch

from media_analyzer.processors.subject.extractors.keyword_extractor import KeywordExtractor


class TestKeywordExtractor:
    """Test suite for keyword extraction processor structure and logic."""
    
    @pytest.fixture(autouse=True)
    def mock_external_dependencies(self):
        """Mock external dependencies for unit tests."""
        # Mock spaCy at the module level to prevent model loading during initialization
        with patch('media_analyzer.processors.subject.extractors.keyword_extractor.spacy') as mock_spacy_module:
            # Mock the spacy.load function to return a mock nlp object
            mock_token = Mock()
            mock_token.text = "test"
            mock_token.pos_ = "NOUN"
            mock_token.is_stop = False
            mock_token.is_space = False
            mock_token.is_alpha = True
            
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.noun_chunks = []
            
            mock_nlp = Mock()
            mock_nlp.return_value = mock_doc
            mock_spacy_module.load.return_value = mock_nlp
            
            # Also mock NLTK stopwords to avoid dependency
            with patch('media_analyzer.processors.subject.extractors.keyword_extractor.stopwords') as mock_stopwords:
                mock_stopwords.words.return_value = {'the', 'a', 'an'}
                
                # Mock wordnet
                with patch('media_analyzer.processors.subject.extractors.keyword_extractor.wordnet'):
                    yield
    
    def test_processor_initialization(self):
        """Test that the processor initializes correctly."""
        processor = KeywordExtractor()
        assert processor is not None
        # Should be able to create multiple instances
        processor2 = KeywordExtractor()
        assert processor2 is not None
        
    def test_process_return_structure(self):
        """Test that process method returns correct structure."""
        processor = KeywordExtractor()
        result = processor.process("Any sample text for testing structure")
        
        # Should return dictionary with required keys
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        # Results should be a dictionary
        results = result["results"]
        assert isinstance(results, dict)
        
        # All values should be confidence scores between 0 and 1
        for value in results.values():
            assert isinstance(value, float)
            assert 0 <= value <= 1
        
        # Metadata should have required fields
        metadata = result["metadata"]
        assert isinstance(metadata, dict)
        assert metadata["processor_type"] == "KeywordExtractor"
        assert "version" in metadata
        
    def test_empty_input_handling(self):
        """Test handling of empty or None input."""
        processor = KeywordExtractor()
        
        # Empty string
        result = processor.process("")
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        # Whitespace only
        result = processor.process("   \n\t  ")
        assert isinstance(result, dict)
        assert "results" in result
        
    def test_special_characters_handling(self):
        """Test handling of text with special characters."""
        processor = KeywordExtractor()
        
        # Text with punctuation
        result = processor.process("Hello! How are you? I'm fine, thanks.")
        assert isinstance(result, dict)
        assert "results" in result
        
        # Text with numbers and symbols
        result = processor.process("Price: $10.99, Quantity: 5 @ 2024-01-01")
        assert isinstance(result, dict)
        assert "results" in result
        
    def test_very_long_text_handling(self):
        """Test handling of very long text input."""
        processor = KeywordExtractor()
        
        # Generate long text
        long_text = "This is a test sentence. " * 1000
        result = processor.process(long_text)
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
    def test_unicode_text_handling(self):
        """Test handling of unicode and non-English text."""
        processor = KeywordExtractor()
        
        # Text with unicode characters
        result = processor.process("Café naïve résumé 中文 🎉")
        assert isinstance(result, dict)
        assert "results" in result
        
    def test_metadata_consistency(self):
        """Test that metadata is consistent across calls."""
        processor = KeywordExtractor()
        
        result1 = processor.process("First test")
        result2 = processor.process("Second test")
        
        # Metadata structure should be consistent
        assert result1["metadata"]["processor_type"] == result2["metadata"]["processor_type"]
        assert result1["metadata"]["version"] == result2["metadata"]["version"]
        
    def test_confidence_score_validity(self):
        """Test that all confidence scores are valid."""
        processor = KeywordExtractor()
        
        test_texts = [
            "Simple test",
            "More complex test with multiple words and phrases",
            "123 numbers and symbols !@#",
            ""
        ]
        
        for text in test_texts:
            result = processor.process(text)
            results = result["results"]
            
            for key, score in results.items():
                assert isinstance(score, float), f"Score for '{key}' should be float"
                assert 0 <= score <= 1, f"Score for '{key}' should be between 0 and 1, got {score}"
