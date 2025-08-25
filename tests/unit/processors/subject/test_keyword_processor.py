"""Tests for keyword processor."""
import pytest
import time

from media_analyzer.processors.subject.processors.keyword_processor import KeywordProcessor


class TestKeywordProcessor:
    """Test suite for keyword extraction processor."""
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction."""
        processor = KeywordProcessor()
        result = processor.process(
            "Artificial intelligence and machine learning are key technologies"
        )
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        results = result["results"]
        assert any("artificial intelligence" in k.lower() 
                  for k in results.keys())
        assert any("machine learning" in k.lower() 
                  for k in results.keys())
        # All keywords should have confidence scores
        assert all(isinstance(v, float) and 0 <= v <= 1 
                  for v in results.values())
        
        # Check metadata
        assert result["metadata"]["processor_type"] == "KeywordProcessor"
        assert "version" in result["metadata"]
        
    def test_keyword_scoring(self):
        """Test keyword scoring mechanism."""
        processor = KeywordProcessor()
        result = processor.process(
            "The quick brown fox jumps over the lazy dog. "
            "The fox is quick and brown. The dog is lazy."
        )
        
        results = result["results"]
        # Repeated phrases should have higher scores
        assert "fox" in results
        assert results["fox"] > 0.5  # Frequently mentioned
        # Single mentions should have lower scores
        assert all(v < 0.7 for k, v in results.items() 
                  if k not in ["fox", "quick", "brown"])
        
    def test_stopword_handling(self):
        """Test proper handling of stopwords."""
        processor = KeywordProcessor()
        result = processor.process("The and or but however therefore consequently")
        
        # Should not extract stopwords as keywords
        assert len(result["results"]) == 0
        
        # Should extract meaningful words even with stopwords
        result = processor.process("The artificial intelligence system learns quickly")
        results = result["results"]
        assert any("intelligence" in k.lower() for k in results.keys())
        assert not any(word in results.keys() 
                      for word in ["the", "and", "or", "but"])
