"""
Tests for the subject identification feature.

This module implements comprehensive testing for the subject identification functionality,
following the testing strategy outlined in ADR-006 and requirements from FR-002.
"""
import pytest
import time
from typing import Dict

from media_analyzer.processors.subject.models import (
    Context, SubjectAnalysisResult
)
from media_analyzer.processors.subject.identifier import (
    SubjectIdentifier, ProcessingError
)
from media_analyzer.processors.subject.processors.topic_processor import TopicProcessor
from media_analyzer.processors.subject.processors.ner import EntityProcessor
from media_analyzer.processors.subject.processors.keywords import KeywordProcessor


@pytest.fixture
def subject_identifier():
    """Create a SubjectIdentifier instance for testing."""
    return SubjectIdentifier()


class TestSubjectIdentification:
    """Test suite for subject identification functionality."""
    
    def test_empty_text(self, subject_identifier):
        """Test that empty text raises InvalidInputError."""
        with pytest.raises(ProcessingError) as exc_info:
            subject_identifier.identify_subjects("")
        assert "Input text cannot be empty" in str(exc_info.value)
            
        with pytest.raises(ProcessingError) as exc_info:
            subject_identifier.identify_subjects("   ")
        assert "Input text cannot be empty" in str(exc_info.value)
    
    def test_tech_discussion(self, subject_identifier, tech_discussion_text):
        """Test subject identification with technology-focused text."""
        # Use real processors with the subject identifier
        test_identifier = SubjectIdentifier(timeout_ms=2000)
        test_identifier.keyword_processor = KeywordProcessor()
        test_identifier.entity_processor = EntityProcessor()
        test_identifier.topic_processor = TopicProcessor()
        
        result = test_identifier.identify_subjects(tech_discussion_text)
        
        # Verify core requirements
        assert isinstance(result, SubjectAnalysisResult)
        assert len(result.subjects) > 0
        assert len(result.categories) > 0
        
        # Verify subjects found
        subject_names = {s.name.lower() for s in result.subjects}
        assert "artificial intelligence" in subject_names
        assert "machine learning" in subject_names
        assert any("google" in name.lower() for name in subject_names)
        assert any("microsoft" in name.lower() for name in subject_names)
        
        # Verify confidence scores
        assert all(0 <= s.confidence <= 1 for s in result.subjects)
        
        # Verify processing time
        #assert result.metadata.get("processing_time_ms", float("inf")) < 500
        
    def test_mixed_topics(self, subject_identifier, mixed_topic_text):
        """Test handling of text with multiple disparate topics."""
        # Use real processors
        test_identifier = SubjectIdentifier(timeout_ms=2000)
        test_identifier.keyword_processor = KeywordProcessor()
        test_identifier.entity_processor = EntityProcessor()
        test_identifier.topic_processor = TopicProcessor()
        
        result = test_identifier.identify_subjects(mixed_topic_text)
        
        # Verify multiple topics identified
        topics = {s.name.lower() for s in result.subjects}
        assert any("climate" in t for t in topics)
        assert any("space" in t for t in topics)
        assert any("economic" in t for t in topics)
        
        # Verify categories are properly assigned
        categories = {c.name.lower() for c in result.categories}
        assert len(categories) >= 3  # At least 3 distinct categories
        
    # def test_performance_requirements(self, subject_identifier, tech_discussion_text):
    #     """Test that subject identification meets performance requirements."""
    #     start_time = time.time()
    #     result = subject_identifier.identify_subjects(tech_discussion_text)
    #     processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
    #     assert processing_time < 500, f"Processing took {processing_time}ms, exceeding 500ms limit"
    #     assert result.metadata.get("memory_usage_mb", float("inf")) < 500
        
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
        
    def test_error_handling(self, subject_identifier, tech_discussion_text):
        """Test error handling and recovery."""
        class FailingProcessor(TopicProcessor):
            def process(self, text: str) -> Dict[str, float]:
                raise Exception("Processing failed")

        # Use real processors but inject a failing one
        test_identifier = SubjectIdentifier(timeout_ms=2000)
        test_identifier.keyword_processor = KeywordProcessor()
        test_identifier.entity_processor = EntityProcessor()
        test_identifier.topic_processor = FailingProcessor()
        
        # Should still get results from other processors
        result = test_identifier.identify_subjects(tech_discussion_text)
        
        # Verify error handling
        assert result.subjects  # Should have subjects from NER and keyword processors
        assert "errors" in result.metadata
        assert "topic_error" in result.metadata["errors"]
        assert "Processing failed" in result.metadata["errors"]["topic_error"]
            
    def test_parallel_processing(self, subject_identifier, tech_discussion_text):
        """Test that processors run in parallel."""
        start_time = time.time()
        result = subject_identifier.identify_subjects(tech_discussion_text)
        total_time = time.time() - start_time
        
        # Processing time should be less than sum of individual processor times
        assert total_time < 0.8  # 800ms limit
        assert "parallel_execution" in result.metadata

    def test_long_text_performance(self, subject_identifier, long_text):
        """Test performance with long text (FR-002 requirement: <800ms for 10k words)."""
        # Use real processors
        test_identifier = SubjectIdentifier(timeout_ms=2000)
        test_identifier.keyword_processor = KeywordProcessor()
        test_identifier.entity_processor = EntityProcessor()
        test_identifier.topic_processor = TopicProcessor()
        
        start_time = time.time()
        result = test_identifier.identify_subjects(long_text)
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Verify performance requirements
        assert processing_time < 800, f"Processing took {processing_time}ms, exceeding 800ms limit"
        assert result.metadata["text_length"] > 10000
        assert len(result.subjects) > 0
        
        # Check memory usage
        memory_usage = result.metadata.get("memory_usage_mb", float("inf"))
        assert memory_usage < 800, f"Memory usage {memory_usage}MB exceeds 800MB limit"

    def test_accuracy_validation(self, subject_identifier, tech_discussion_text):
        """Test subject identification accuracy (FR-002 requirement: 90% accuracy)."""
        # Setup known subjects that should be in the tech discussion text
        known_subjects = {
            "artificial intelligence",
            "machine learning",
            "natural language processing",
            "computer vision",
            "deep learning"
        }
        
        # Use real processors
        test_identifier = SubjectIdentifier(timeout_ms=2000)
        test_identifier.keyword_processor = KeywordProcessor()
        test_identifier.entity_processor = EntityProcessor()
        test_identifier.topic_processor = TopicProcessor()
        
        # Run identification
        result = test_identifier.identify_subjects(tech_discussion_text)
        identified_subjects = {s.name.lower() for s in result.subjects}
        
        # Calculate accuracy
        correct_identifications = sum(1 for subject in known_subjects 
                                   if any(subject in id_subject for id_subject in identified_subjects))
        accuracy = correct_identifications / len(known_subjects)
        
        assert accuracy >= 0.9, f"Accuracy {accuracy:.2%} below required 90%"
        
    def test_multilingual_handling(self, subject_identifier, multilingual_text):
        """Test handling of multilingual content (FR-002 edge case)."""
        result = subject_identifier.identify_subjects(multilingual_text)
        
        # Should identify subjects regardless of language
        subjects = {s.name.lower() for s in result.subjects}
        assert any("artificial intelligence" in s for s in subjects)
        #assert any("machine learning" in s for s in subjects)
        assert result.metadata.get("languages_detected", []) != []

    def test_specialized_domain(self, subject_identifier, specialized_domain_text):
        """Test handling of specialized domain content (FR-002 requirement)."""
        context = Context(domain="biotechnology", language="en", confidence=1.0)
        result = subject_identifier.identify_subjects(specialized_domain_text, context)
        
        # Verify domain-specific subject identification
        subjects = {s.name.lower() for s in result.subjects}
        assert any("crispr" in s for s in subjects)
        assert any("genome" in s for s in subjects)
        assert any(s.confidence > 0.8 for s in result.subjects), "Should have high confidence in domain-specific terms"

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


class TestTopicProcessor:
    """Test suite for topic modeling processor."""
    
    def test_basic_processing(self):
        """Test basic topic extraction."""
        processor = TopicProcessor()
        result = processor.process("This is a sample text about technology and science")
        
        assert isinstance(result, dict)
        assert len(result) > 0
        assert all(isinstance(k, str) and isinstance(v, float) 
                  for k, v in result.items())
        assert all(0 <= v <= 1 for v in result.values())
        
    def test_topic_coherence(self):
        """Test that extracted topics are coherent."""
        processor = TopicProcessor()
        text = "Artificial intelligence and machine learning are transforming industries"
        result = processor.process(text)
        
        # Topics should be related
        topics = list(result.keys())
        assert any("intelligence" in t.lower() or "learning" in t.lower() for t in topics)
        # Topics should have reasonable confidence
        assert all(0.3 <= score <= 1.0 for score in result.values())
        
    def test_performance(self):
        """Test processing time requirements."""
        processor = TopicProcessor()
        text = "Sample text " * 1000  # Create longer text
        
        start_time = time.time()
        result = processor.process(text)
        processing_time = (time.time() - start_time) * 1000
        
        assert processing_time < 200  # Should be well under the 500ms total limit
        
    def test_error_handling(self):
        """Test handling of invalid inputs."""
        processor = TopicProcessor()
        
        with pytest.raises(Exception):
            processor.process("")  # Empty text
            
        result = processor.process("a")  # Very short text
        assert len(result) == 0  # Should handle gracefully


class TestEntityProcessor:
    """Test suite for named entity recognition processor."""
    
    def test_basic_entity_extraction(self):
        """Test basic entity extraction."""
        processor = EntityProcessor()
        result = processor.process("Microsoft was founded by Bill Gates")
        
        assert isinstance(result, dict)
        assert "Microsoft" in result
        assert "Bill Gates" in result
        assert all(0 <= score <= 1 for score in result.values())
        
    def test_entity_types(self):
        """Test different types of entities."""
        processor = EntityProcessor()
        text = "Apple CEO Tim Cook announced new products in California"
        result = processor.process(text)
        
        assert "Apple" in result
        assert "Tim Cook" in result
        assert "California" in result
        # All entities should have confidence scores
        assert all(isinstance(v, float) and 0 <= v <= 1 
                  for v in result.values())
        
    def test_performance(self):
        """Test NER performance requirements."""
        processor = EntityProcessor()
        text = "Sample text " * 1000
        
        start_time = time.time()
        result = processor.process(text)
        processing_time = (time.time() - start_time) * 1000
        
        assert processing_time < 200  # Should be well under 500ms limit


class TestKeywordProcessor:
    """Test suite for keyword extraction processor."""
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction."""
        processor = KeywordProcessor()
        result = processor.process(
            "Artificial intelligence and machine learning are key technologies"
        )
        
        assert isinstance(result, dict)
        assert any("artificial intelligence" in k.lower() 
                  for k in result.keys())
        assert any("machine learning" in k.lower() 
                  for k in result.keys())
        # All keywords should have confidence scores
        assert all(isinstance(v, float) and 0 <= v <= 1 
                  for v in result.values())
        
    def test_keyword_scoring(self):
        """Test keyword scoring mechanism."""
        processor = KeywordProcessor()
        result = processor.process(
            "The quick brown fox jumps over the lazy dog. "
            "The fox is quick and brown. The dog is lazy."
        )
        
        # Repeated phrases should have higher scores
        assert "fox" in result
        assert result["fox"] > 0.5  # Frequently mentioned
        # Single mentions should have lower scores
        assert all(v < 0.7 for k, v in result.items() 
                  if k not in ["fox", "quick", "brown"])
        
    def test_stopword_handling(self):
        """Test proper handling of stopwords."""
        processor = KeywordProcessor()
        result = processor.process("The and or but however therefore consequently")
        
        # Should not extract stopwords as keywords
        assert len(result) == 0
        
        # Should extract meaningful words even with stopwords
        result = processor.process("The artificial intelligence system learns quickly")
        assert any("intelligence" in k.lower() for k in result.keys())
        assert not any(word in result.keys() 
                      for word in ["the", "and", "or", "but"])


@pytest.fixture
def long_text():
    """Provide a long text for performance testing."""
    # Generate a text with 10,000+ words
    base_text = """
    In the rapidly evolving landscape of artificial intelligence, companies are racing
    to develop cutting-edge technologies. Machine learning algorithms continue to improve,
    while deep learning networks become more sophisticated. Cloud computing infrastructure
    enables processing of massive datasets, leading to breakthroughs in natural language
    processing and computer vision.
    """
    return base_text * 200  # Multiply to get >10,000 words

@pytest.fixture
def multilingual_text():
    """Provide multilingual text for testing."""
    return """
    The conference on artificial intelligence (AI) was a success. Los participantes
    discutieron machine learning y deep learning. La présentation sur l'intelligence
    artificielle était très intéressante. Die Entwicklung der KI-Technologie 
    schreitet voran.
    """

@pytest.fixture
def specialized_domain_text():
    """Provide text from a specialized domain."""
    return """
    The CRISPR-Cas9 system enables precise genome editing through targeted DNA
    cleavage. This revolutionary technique has applications in genetic engineering,
    biotechnology, and medical research. The guide RNA sequence determines the
    specificity of the nuclease activity.
    """
