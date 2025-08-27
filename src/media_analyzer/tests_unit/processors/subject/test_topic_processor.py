"""Tests for topic processor."""
import pytest
import time

from media_analyzer.processors.subject.processors.topic_processor import TopicProcessor


class TestTopicProcessor:
    """Test suite for topic modeling processor."""
    
    def test_basic_processing(self):
        """Test basic topic extraction."""
        processor = TopicProcessor()
        result = processor.process("This is a sample text about technology and science")
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        results = result["results"]
        assert len(results) > 0
        assert all(isinstance(k, str) and isinstance(v, float) 
                  for k, v in results.items())
        assert all(0 <= v <= 1 for v in results.values())
        
        # Check metadata
        assert result["metadata"]["processor_type"] == "TopicProcessor"
        assert "version" in result["metadata"]
        
    def test_topic_coherence(self):
        """Test that extracted topics are coherent."""
        processor = TopicProcessor()
        text = "Artificial intelligence and machine learning are transforming industries"
        result = processor.process(text)
        
        results = result["results"]
        # Topics should be related
        topics = list(results.keys())
        assert any("intelligence" in t.lower() or "learning" in t.lower() for t in topics)
        # Topics should have reasonable confidence
        assert all(0.3 <= score <= 1.0 for score in results.values())
        
    def test_performance(self):
        """Test processing time requirements."""
        processor = TopicProcessor()
        text = "Sample text " * 1000  # Create longer text
        
        start_time = time.time()
        result = processor.process(text)
        processing_time = (time.time() - start_time) * 1000
        
        assert processing_time < 200  # Should be well under the 500ms total limit
        
    def test_input_validation(self):
        """Test handling of invalid inputs."""
        processor = TopicProcessor()
        
        with pytest.raises(ValueError):
            processor.process("")  # Empty text
            
        result = processor.process("a")  # Very short text
        assert len(result["results"]) == 0  # Should handle gracefully
        
    def test_empty_text(self):
        """Test handling of empty text."""
        processor = TopicProcessor()
        
        with pytest.raises(ValueError):
            processor.process("")
            
        with pytest.raises(ValueError):
            processor.process("   ")
