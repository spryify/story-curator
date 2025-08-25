"""Tests for entity processor."""
import pytest
import time

from media_analyzer.processors.subject.processors.entity_processor import EntityProcessor


class TestEntityProcessor:
    """Test suite for named entity recognition processor."""
    
    def test_basic_entity_extraction(self):
        """Test basic entity extraction."""
        processor = EntityProcessor()
        result = processor.process("Microsoft was founded by Bill Gates")
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        results = result["results"]
        assert "Microsoft" in results
        assert "Bill Gates" in results
        assert all(0 <= score <= 1 for score in results.values())
        
        # Check metadata
        assert result["metadata"]["processor_type"] == "EntityProcessor"
        assert "version" in result["metadata"]
        
    def test_entity_types(self):
        """Test different types of entities."""
        processor = EntityProcessor()
        text = "Apple CEO Tim Cook announced new products in California"
        result = processor.process(text)
        
        results = result["results"]
        assert "Apple" in results
        assert "Tim Cook" in results
        assert "California" in results
        # All entities should have confidence scores
        assert all(isinstance(v, float) and 0 <= v <= 1 
                  for v in results.values())
        
    def test_performance(self):
        """Test NER performance requirements."""
        processor = EntityProcessor()
        text = "Sample text " * 1000
        
        start_time = time.time()
        result = processor.process(text)
        processing_time = (time.time() - start_time) * 1000
        
        assert processing_time < 200  # Should be well under 500ms limit
        
    def test_input_validation(self):
        """Test input validation."""
        processor = EntityProcessor()
        
        with pytest.raises(ValueError):
            processor.process("")  # Empty text
            
        with pytest.raises(ValueError):
            processor.process(None)  # None input
