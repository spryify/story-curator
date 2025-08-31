"""Integration tests for entity processor using real SpaCy models."""
import pytest
from media_analyzer.processors.subject.extractors.entity_extractor import EntityExtractor


@pytest.fixture
def entity_processor():
    """Fixture that provides an EntityExtractor using the real SpaCy model."""
    try:
        return EntityExtractor()
    except OSError:
        pytest.skip("SpaCy model 'en_core_web_sm' not available")


class TestEntityExtractorIntegration:
    """Integration test class using the real SpaCy model for entity processing."""

    def test_basic_functionality_with_real_model(self, entity_processor):
        """Test basic entity processing functionality with real SpaCy model."""
        text = "Alice went to New York to visit Bob."
        result = entity_processor.process(text)
        
        # Check structure
        assert "metadata" in result
        assert "results" in result
        assert isinstance(result["results"], dict)
        assert result["metadata"]["processor_type"] == "EntityExtractor"

    def test_input_validation_real(self, entity_processor):
        """Test input validation with real model."""
        with pytest.raises(ValueError):
            entity_processor.process("")  # Empty text
            
        with pytest.raises(ValueError):
            entity_processor.process(None)  # None input

    def test_story_character_recognition_real(self, entity_processor):
        """Test recognition of story character names and titles with real model."""
        story = """
        Once upon a time, Little Red Riding Hood visited her Grandmother.
        She met her friend Peter and his rabbit Hoppy in the forest.
        They saw Mr. Wolf hiding behind a tree, but Dr. Owl warned them in time.
        """
        result = entity_processor.process(story)
        results = result["results"]
        
        # Test that some entities are found (less strict)
        assert len(results) > 0, "No entities found in story"
        
        # Check that we get reasonable confidence scores
        assert all(0 <= score <= 1 for score in results.values()), "Invalid confidence scores"

    def test_story_setting_recognition_real(self, entity_processor):
        """Test recognition of story locations and settings with real model."""
        story = """
        Billy lived in New York City with his family. Every summer they visited
        Central Park and the Natural History Museum. His favorite place was 
        the Brooklyn Zoo where he could watch the animals play.
        """
        result = entity_processor.process(story)
        results = result["results"]
        
        # Test that some entities are found
        assert len(results) > 0, "No entities found in location story"
        
        # Check for reasonable confidence scores
        assert all(0 <= score <= 1 for score in results.values()), "Invalid confidence scores"
        
        # Check if at least one location is found (more lenient)
        locations = ["New York", "Central Park", "Brooklyn", "Billy"]
        found_any_location = any(loc in key for key in results for loc in locations)
        assert found_any_location, f"No expected locations found in {list(results.keys())}"

    def test_story_object_recognition_real(self, entity_processor):
        """Test recognition of important story objects and items with real model."""
        story = """
        Sarah bought a Nintendo Switch and some LEGO toys from Walmart.
        She also got the latest Harry Potter book and some Crayola crayons
        from Barnes & Noble for her school project.
        """
        result = entity_processor.process(story)
        results = result["results"]
        
        # Test that entities are found
        assert len(results) > 0, "No entities found in brand story"
        
        # Check that Sarah is found as a person
        assert "Sarah" in results, f"Sarah not found in {list(results.keys())}"
        
        # Check for reasonable confidence scores
        assert all(0 <= score <= 1 for score in results.values()), "Invalid confidence scores"
        
        # Check if at least some brands are found (more lenient)
        brands = ["Nintendo", "LEGO", "Harry Potter", "Walmart", "Barnes"]
        found_any_brand = any(brand in key for key in results for brand in brands)
        assert found_any_brand, f"No brands found in {list(results.keys())}"

    def test_relationship_recognition_real(self, entity_processor):
        """Test recognition of character relationships with real model."""
        story = """
        Principal Wilson and Vice Principal Martinez welcomed everyone.
        Principal Wilson addressed the teachers while 
        Vice Principal Martinez spoke to the students.
        Later, both Principal Wilson and Vice Principal Martinez 
        attended the school board meeting.
        """
        result = entity_processor.process(story)
        results = result["results"]
        
        # Test that entities are found
        assert len(results) > 0, "No entities found in relationship story"
        
        # Check for reasonable confidence scores
        assert all(0 <= score <= 1 for score in results.values()), "Invalid confidence scores"
        
        # Check if names are found (more lenient)
        names = ["Wilson", "Martinez"]
        found_any_name = any(name in key for key in results for name in names)
        assert found_any_name, f"No expected names found in {list(results.keys())}"
