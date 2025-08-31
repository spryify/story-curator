"""Integration tests for SubjectIdentifier using real models."""
import pytest
from pathlib import Path

from media_analyzer.processors.subject.subject_identifier import SubjectIdentifier
from media_analyzer.models.subject import Context, SubjectType


class TestSubjectIdentifierIntegration:
    """Integration tests for SubjectIdentifier with real external dependencies."""

    @pytest.fixture
    def subject_identifier(self):
        """Create a SubjectIdentifier with real dependencies (no mocks)."""
        return SubjectIdentifier(max_workers=2, timeout_ms=2000)

    def test_real_spacy_model_integration(self, subject_identifier):
        """Test integration with real SpaCy model for entity recognition."""
        # Text with clear entities that SpaCy should recognize
        text = """
        Once upon a time, Princess Jasmine lived in the kingdom of Agrabah. 
        She was known throughout India for her wisdom and kindness.
        The evil wizard Jafar threatened the peaceful village with his dark magic.
        Prince Ali traveled from the distant mountains to help defend the kingdom.
        """
        
        result = subject_identifier.identify_subjects(text)
        
        # Should identify real entities using SpaCy
        assert result.subjects
        
        # Check for entity-based subjects (from SpaCy NER)
        entity_subjects = [s for s in result.subjects if s.subject_type == SubjectType.ENTITY]
        assert len(entity_subjects) > 0, "Should identify entities with real SpaCy model"
        
        # Should recognize character names
        entity_names = [s.name.lower() for s in entity_subjects]
        assert any('jasmine' in name or 'ali' in name or 'jafar' in name for name in entity_names)

    def test_multilingual_detection_integration(self, subject_identifier):
        """Test language detection with real langdetect library."""
        # Mixed language text
        mixed_text = """
        Hello, this is an English story about a princess.
        Hola, esta es una historia en español sobre una princesa.
        This story takes place in a magical kingdom.
        """
        
        result = subject_identifier.identify_subjects(mixed_text)
        
        # Should detect multiple languages
        assert "languages_detected" in result.metadata
        languages = result.metadata["languages_detected"]
        assert len(languages) >= 1  # Should detect at least English
        assert any(lang in ['en', 'es'] for lang in languages)

    def test_concurrent_processor_integration(self, subject_identifier):
        """Test real concurrent execution of all processors."""
        # Rich text that should trigger all processors
        text = """
        The brave princess lived in a beautiful castle in the ancient kingdom of Wonderland.
        She was known for her courage and wisdom throughout the land.
        Machine learning and artificial intelligence helped her solve complex problems.
        The magical forest contained mysterious creatures and powerful artifacts.
        Love, friendship, and determination guided her on her quest for justice.
        """
        
        result = subject_identifier.identify_subjects(text)
        
        # Should have processed with all three processors
        assert result.subjects
        assert result.categories
        
        # Check that we have subjects from different processors
        subject_types = {s.subject_type for s in result.subjects}
        assert len(subject_types) >= 2, "Should have subjects from multiple processor types"
        
        # Check performance metrics indicate parallel execution
        assert result.metadata["parallel_execution"] is True
        assert "processing_time_ms" in result.metadata
        
        # Processing time should be reasonable (less than timeout)
        assert result.metadata["processing_time_ms"] < subject_identifier.timeout_ms

    def test_real_story_content_extraction(self, subject_identifier):
        """Test with realistic podcast transcript containing story content."""
        # Simulate a Circle Round podcast transcript
        podcast_text = """
        Hi, Circle Round listeners, Rebecca Sheir here. Before we get to our story today,
        I have some exciting news. We're going back on tour with live recordings. 
        Our first stop is Sunday, April 28th at the Dairy Center in Boulder, Colorado.
        
        Now let's get to our story. Once upon a time, in the faraway kingdom of Eldoria,
        there lived a wise queen named Isabella. She ruled with great compassion and justice.
        The kingdom faced a terrible drought, and the people were losing hope.
        Queen Isabella decided to seek help from the ancient forest spirits.
        
        With courage and determination, she journeyed into the mystical Whispering Woods.
        There she met Sage Willow, an old tree spirit who offered magical wisdom.
        Through patience and understanding, the queen learned the secret of bringing rain.
        """
        
        result = subject_identifier.identify_subjects(podcast_text)
        
        # Should filter out podcast metadata and focus on story content
        assert result.subjects
        
        # Should identify story characters
        subject_names = [s.name.lower() for s in result.subjects]
        assert any('isabella' in name or 'queen' in name for name in subject_names)
        assert any('eldoria' in name or 'kingdom' in name for name in subject_names)
        
        # Should identify themes and values
        assert any('courage' in name or 'wisdom' in name or 'compassion' in name 
                  for name in subject_names)
        
        # Should NOT heavily weight podcast metadata
        metadata_terms = ['rebecca', 'sheir', 'boulder', 'colorado', 'dairy center']
        metadata_subjects = [s for s in result.subjects 
                           if any(term in s.name.lower() for term in metadata_terms)]
        story_subjects = [s for s in result.subjects 
                         if not any(term in s.name.lower() for term in metadata_terms)]
        
        # Story subjects should have higher confidence than metadata
        if metadata_subjects and story_subjects:
            avg_story_conf = sum(s.confidence for s in story_subjects) / len(story_subjects)
            avg_metadata_conf = sum(s.confidence for s in metadata_subjects) / len(metadata_subjects)
            assert avg_story_conf >= avg_metadata_conf

    def test_context_aware_processing(self, subject_identifier):
        """Test context-aware subject identification."""
        # Create context
        context = Context(
            domain="THEMES",
            language="en", 
            confidence=1.0
        )
        
        text = """
        The young princess showed great courage when facing the dragon.
        Her kindness and wisdom helped her make friends with the beast.
        Through love and understanding, she transformed hatred into friendship.
        """
        
        result = subject_identifier.identify_subjects(text, context)
        
        # Should boost theme-related subjects due to context
        theme_subjects = [s for s in result.subjects 
                         if any(theme in s.name.lower() 
                               for theme in ['courage', 'kindness', 'wisdom', 'love'])]
        
        assert len(theme_subjects) > 0
        # Context should boost confidence for theme-related subjects
        high_conf_themes = [s for s in theme_subjects if s.confidence > 0.8]
        assert len(high_conf_themes) > 0

    def test_memory_and_performance_integration(self, subject_identifier):
        """Test memory usage and performance with realistic text sizes."""
        # Large text to test memory management
        base_text = """
        In the magical kingdom of Storytopia, Princess Luna discovered an ancient book
        filled with tales of courage, wisdom, and friendship. Each story taught valuable
        lessons about kindness, perseverance, and the power of believing in oneself.
        """
        
        # Repeat to create larger text
        large_text = base_text * 10
        
        result = subject_identifier.identify_subjects(large_text)
        
        # Should handle large text efficiently
        assert result.subjects
        assert "memory_usage_mb" in result.metadata
        assert "processing_time_ms" in result.metadata
        
        # Memory usage should be reasonable (less than 100MB for this size)
        assert result.metadata["memory_usage_mb"] < 100
        
        # Processing should complete within timeout
        assert result.metadata["processing_time_ms"] < subject_identifier.timeout_ms

    def test_error_handling_integration(self, subject_identifier):
        """Test error handling with real external dependencies."""
        # Very short text that should trigger input validation
        with pytest.raises(Exception):  # Should raise InvalidInputError
            subject_identifier.identify_subjects("Hi")
        
        # Empty text
        with pytest.raises(Exception):  # Should raise InvalidInputError  
            subject_identifier.identify_subjects("")
        
        # Text with unusual characters that might break external libraries
        unusual_text = "∆∂∫∑∏√∞≈≠±×÷•◊◆★☆♠♣♥♦♪♫♬"
        
        # Should handle gracefully without crashing
        result = subject_identifier.identify_subjects(unusual_text)
        assert isinstance(result.metadata, dict)
        assert "errors" in result.metadata
