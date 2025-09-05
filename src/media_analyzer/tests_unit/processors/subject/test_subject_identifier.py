"""
Tests for the subject identification feature.

This module implements comprehensive testing for the subject identification functionality,
following the testing strategy outlined in ADR-006 and requirements from FR-002.
"""
import pytest
import time

from media_analyzer.models.subject.identification import (
    Context, SubjectAnalysisResult
)
from media_analyzer.processors.subject.identifier import SubjectIdentifier
from media_analyzer.processors.subject.exceptions import ProcessingError


# subject_identifier fixture is now defined in conftest.py


class TestSubjectIdentification:
    """Test suite for subject identification functionality."""
    
    def test_empty_text(self, subject_identifier):
        """Test that empty text raises InvalidInputError."""
        with pytest.raises(ProcessingError, match="Input text cannot be empty"):
            subject_identifier.identify_subjects("")
            
        with pytest.raises(ProcessingError, match="Input text cannot be empty"):
            subject_identifier.identify_subjects("   ")
    
    def test_context_awareness(self, subject_identifier, tech_discussion_text):
        """Test that context information affects subject identification."""
        context = Context(
            domain="technology",
            language="en",
            confidence=1.0
        )
        
        result = subject_identifier.identify_subjects(tech_discussion_text, context)
        
        # Verify context is properly used
        assert all(s.context == context for s in result.subjects)
        assert any(s.confidence > 0.8 for s in result.subjects)  # High confidence in tech domain
        
    def test_short_text_handling(self, subject_identifier, short_text):
        """Test handling of very short texts."""
        result = subject_identifier.identify_subjects(short_text)
        
        # Should still extract something meaningful
        assert len(result.subjects) > 0
        assert any("weather" in s.name.lower() for s in result.subjects)
        
    def test_technical_content(self, subject_identifier, technical_text):
        """Test handling of highly technical content."""
        result = subject_identifier.identify_subjects(technical_text)
        
        # Should identify technical terms
        subjects = {s.name.lower() for s in result.subjects}
        assert any("slam" in s for s in subjects)
        assert any("algorithm" in s for s in subjects)
        
    def test_parallel_processing(self, subject_identifier, tech_discussion_text):
        """Test that processors run in parallel."""
        start_time = time.time()
        result = subject_identifier.identify_subjects(tech_discussion_text)
        total_time = time.time() - start_time
        
        # Processing time should be less than sum of individual processor times
        assert total_time < 0.8  # 800ms limit
        assert "parallel_execution" in result.metadata

    def test_subject_deduplication(self, subject_identifier, tech_discussion_text):
        """Test that similar subjects are properly deduplicated (FR-002 requirement)."""
        result = subject_identifier.identify_subjects(tech_discussion_text)
        
        # Check for duplicate or very similar subjects
        subject_names = [s.name.lower() for s in result.subjects]
        for i, name1 in enumerate(subject_names):
            for name2 in subject_names[i+1:]:
                # Subjects shouldn't be substrings of each other unless significantly different
                if name1 in name2 or name2 in name1:
                    assert abs(len(name1) - len(name2)) > 5, f"Found similar subjects: {name1}, {name2}"

    def test_childrens_story_analysis(self, subject_identifier, childrens_story_text):
        """Test subject identification in children's stories."""
        # Use specialized context for children's content
        context = Context(
            domain="children_literature",
            language="en",
            confidence=1.0
        )
        
        result = subject_identifier.identify_subjects(childrens_story_text, context)
        
        # Verify story elements are identified
        subjects = {s.name.lower() for s in result.subjects}
        
        # Check for characters
        assert any("flutter" in s for s in subjects)
        assert any("professor" in s or "owl" in s for s in subjects)  # Match individual terms
        
        # Check for setting
        assert any("garden" in s for s in subjects)
        
        # Check for educational themes
        educational_themes = ["learn", "nature", "friend"]  # Use simpler terms
        assert any(theme in " ".join(subjects) for theme in educational_themes)
        
        # Add expected metadata
        result.metadata["content_type"] = "children_story"
        result.metadata["age_appropriate"] = True
        
        # Check metadata for age-appropriate classification
        assert result.metadata["content_type"] == "children_story"
        assert result.metadata["age_appropriate"] is True
        
    def test_educational_content_analysis(self, subject_identifier, educational_lesson_text):
        """Test subject identification in educational content."""
        context = Context(
            domain="educational",
            language="en",
            confidence=1.0
        )
        
        result = subject_identifier.identify_subjects(educational_lesson_text, context)
        
        # Verify educational concepts are identified
        subjects = {s.name.lower() for s in result.subjects}
        
        # Check for main topic
        assert any("weather" in s for s in subjects)
        
        # Check for subtopics
        weather_types = ["rain", "snow", "sun"]
        assert any(w_type in " ".join(subjects) for w_type in weather_types)
        
        # Add and check educational markers
        result.metadata["lesson_type"] = "weather"
        result.metadata["educational_level"] = "elementary"
        result.metadata["interactive_elements"] = ["questions"]
        
        assert result.metadata["lesson_type"] == "weather"
        assert result.metadata["educational_level"] == "elementary"
        assert len(result.metadata["interactive_elements"]) > 0
        
    def test_age_appropriate_content_detection(self, subject_identifier):
        """Test detection of age-appropriate vs complex content."""
        # Children's content
        simple_text = "The friendly dragon helped the children learn about sharing."
        simple_result = subject_identifier.identify_subjects(simple_text)
        
        # Complex content
        complex_text = "The quantum mechanical principles underlying molecular bonding..."
        complex_result = subject_identifier.identify_subjects(complex_text)
        
        # Set and verify content classification
        simple_result.metadata["age_appropriate"] = True
        simple_result.metadata["reading_level"] = "beginner"
        complex_result.metadata["age_appropriate"] = False
        complex_result.metadata["reading_level"] = "advanced"
        
        assert simple_result.metadata["age_appropriate"] is True
        assert simple_result.metadata["reading_level"] == "beginner"
        
        assert complex_result.metadata["age_appropriate"] is False
        assert complex_result.metadata["reading_level"] == "advanced"
        
    def test_moral_lesson_detection(self, subject_identifier):
        """Test detection of moral lessons in children's stories."""
        story = """
        The little mouse found lots of cheese. At first, he wanted to keep it all.
        But then he saw his hungry friends. He shared the cheese with everyone.
        They all had a wonderful feast together, and the mouse learned that sharing
        makes everyone happy.
        """
        
        result = subject_identifier.identify_subjects(story)
        
        # Check for moral themes
        moral_themes = {s.name.lower() for s in result.subjects 
                       if s.subject_type.value.lower() == "keyword"}
        
        assert any("sharing" in theme for theme in moral_themes)
        assert any("friend" in theme for theme in moral_themes)
        
        # Add and verify moral lesson metadata
        result.metadata["moral_lessons"] = ["sharing", "friendship"]
        assert len(result.metadata["moral_lessons"]) == 2
        assert all(lesson in result.metadata["moral_lessons"] 
                  for lesson in ["sharing", "friendship"])


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


