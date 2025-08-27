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
            
    def test_story_character_recognition(self):
        """Test recognition of story character names and titles."""
        processor = EntityProcessor()
        story = """
        Once upon a time, Little Red Riding Hood visited her Grandmother.
        She met her friend Peter and his rabbit Hoppy in the forest.
        They saw Mr. Wolf hiding behind a tree, but Dr. Owl warned them in time.
        """
        result = processor.process(story)
        results = result["results"]
        
        # Test proper name recognition (at least 2 main character names should be found)
        character_names = ["Red", "Peter", "Wolf", "Owl"]
        found_names = [name for name in character_names if any(name in key for key in results)]
        assert len(found_names) >= 2, f"Found only {found_names}"
        
        # At least one character should have high confidence
        high_conf_chars = [name for name, score in results.items() 
                          if score > 0.7 and any(char in name for char in character_names)]
        assert len(high_conf_chars) > 0, "No main character with high confidence found"
        
    def test_story_setting_recognition(self):
        """Test recognition of story locations and settings."""
        processor = EntityProcessor()
        story = """
        Billy lived in New York City with his family. Every summer they visited
        Central Park and the Natural History Museum. His favorite place was 
        the Brooklyn Zoo where he could watch the animals play.
        """
        result = processor.process(story)
        results = result["results"]
        
        # Test location recognition (should find at least 2 locations)
        locations = ["New York", "Central Park", "Brooklyn"]
        found_locations = [loc for loc in locations if any(loc in key for key in results)]
        assert len(found_locations) >= 2, f"Found only {found_locations}"
        
        # Location names should have good confidence
        assert any(score > 0.6 for name, score in results.items() 
                  if any(loc in name for loc in locations))
        
    def test_story_object_recognition(self):
        """Test recognition of important story objects and items."""
        processor = EntityProcessor()
        story = """
        Sarah bought a Nintendo Switch and some LEGO toys from Walmart.
        She also got the latest Harry Potter book and some Crayola crayons
        from Barnes & Noble for her school project.
        """
        result = processor.process(story)
        results = result["results"]
        
        # Test brand/product recognition (should find at least 3)
        brands = ["Nintendo", "LEGO", "Harry Potter", "Crayola", "Walmart", "Barnes & Noble"]
        found_brands = [brand for brand in brands if any(brand in key for key in results)]
        assert len(found_brands) >= 3, f"Found only {found_brands}"
        
        # Character recognition
        assert "Sarah" in results
        
        # Brands should have high confidence
        assert any(score > 0.8 for name, score in results.items() 
                  if any(brand in name for brand in brands))
        
    def test_relationship_recognition(self):
        """Test recognition of character relationships."""
        processor = EntityProcessor()
        story = """
        Principal Wilson and Vice Principal Martinez welcomed everyone.
        Principal Wilson addressed the teachers while 
        Vice Principal Martinez spoke to the students.
        Later, both Principal Wilson and Vice Principal Martinez 
        attended the school board meeting.
        """
        result = processor.process(story)
        results = result["results"]
        
        # Test title recognition (using repeated clear titles)
        titles = ["Principal", "Vice Principal"]
        found_titles = [title for title in titles 
                       if any(title in key for key in results)]
        assert len(found_titles) >= 1, f"Found no titles from {titles}"
        
        # Test full name recognition with titles
        titled_names = ["Principal Wilson", "Vice Principal Martinez"]
        found_titled_names = [name for name in titled_names 
                            if any(name in key for key in results)]
        assert len(found_titled_names) >= 1, \
            f"Found no full titled names from {titled_names}"
        
        # Test that repeated mentions increase confidence
        assert any(results[name] > 0.7 for name in results 
                  if "Principal Wilson" in name or "Vice Principal Martinez" in name), \
            "No repeated titled names with high confidence"
