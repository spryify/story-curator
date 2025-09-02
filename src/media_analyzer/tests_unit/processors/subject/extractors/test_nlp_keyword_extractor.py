"""Tests for NLP-based enhanced keyword extractor.

Following TDD approach per docs/ai-agents/prompts/tdd-implementation-prompt.md
Tests are co-located with source code per project conventions.
"""

import pytest
from typing import Dict, Any, Set
from unittest.mock import Mock, patch

import sys
import os
sys.path.append('/Users/saparya/Documents/Projects/story-curator/src')

# Test imports - will fail until we create the NLP implementation
from media_analyzer.processors.subject.extractors.nlp_keyword_extractor import NLPKeywordExtractor


class TestNLPKeywordExtractor:
    """Test class for NLP-based keyword extractor following ADR-006 testing strategy."""
    
    @pytest.fixture
    def extractor(self) -> NLPKeywordExtractor:
        """Create a keyword extractor instance for testing.
        
        Returns:
            NLPKeywordExtractor: Test instance with NLP libraries configured
        """
        return NLPKeywordExtractor()
    
    def test_problematic_words_filtered_out(self, extractor: NLPKeywordExtractor) -> None:
        """Test that problematic generic words are filtered out using NLTK stop words.
        
        This addresses the core issue from FR-002: words like 'her', 'very', 'end' 
        should not appear in keyword results as they cause irrelevant icon matches.
        Uses NLTK stopwords corpus instead of custom lists per enhancement goals.
        
        Args:
            extractor: NLP keyword extractor instance
        """
        # 🔴 RED: This test will fail because NLPKeywordExtractor doesn't exist yet
        problematic_text = """
        Have you ever taken more than you needed? When we're tempted by something, 
        we sometimes end up going a little overboard. But in today's story, 
        whether you believe in her or not, leprechauns are very special.
        """
        
        result = extractor.process(problematic_text)
        keywords = result.get('results', {})
        
        # These problematic words should NOT appear in results (filtered by NLTK stopwords)
        problematic_words = {'her', 'very', 'end', 'ever', 'you', 'we', 'in', 'or', 'not', 'up', 'by'}
        found_problematic = set(keywords.keys()) & problematic_words
        
        assert len(found_problematic) == 0, f"Found problematic words: {found_problematic}"
        
        # But meaningful words should still be extracted
        meaningful_words = {'leprechauns', 'story', 'special'}
        found_meaningful = set(keywords.keys()) & meaningful_words
        
        assert len(found_meaningful) > 0, "Should find at least some meaningful words"
    
    def test_semantic_relevance_scoring(self, extractor: NLPKeywordExtractor) -> None:
        """Test that keywords receive semantic relevance scores using spaCy.
        
        Per FR-002 enhancement goals, keywords should be scored based on 
        semantic relevance, not just frequency. Uses spaCy word vectors.
        
        Args:
            extractor: NLP keyword extractor instance
        """
        # 🔴 RED: This test will fail until we implement semantic scoring
        story_text = """
        The brave knight rode through the enchanted forest to rescue the princess 
        from the dragon's tower. His shining armor reflected the golden sunlight.
        """
        
        result = extractor.process(story_text, context={'domain': 'story'})
        keywords = result.get('results', {})
        
        # Story-relevant words should have higher confidence than generic words
        story_words = {'knight', 'princess', 'dragon', 'tower', 'armor', 'enchanted'}
        
        story_confidences = [keywords.get(word, 0) for word in story_words if word in keywords]
        
        # Story words should have meaningful confidence scores using semantic relevance
        assert any(conf > 0.5 for conf in story_confidences), "Story words should have high confidence"
        assert len([c for c in story_confidences if c > 0]) >= 3, "Should find multiple story-relevant keywords"
    
    def test_compound_phrase_detection(self, extractor: NLPKeywordExtractor) -> None:
        """Test that compound phrases are detected using spaCy dependency parsing.
        
        Per FR-002, compound phrases like 'folk tale' should be extracted as single units
        rather than separate words, using spaCy's dependency parsing capabilities.
        
        Args:
            extractor: NLP keyword extractor instance
        """
        # 🔴 RED: This test will fail until we implement compound phrase detection
        text_with_phrases = """
        This folk tale from ancient times tells of a wise old owl who lived 
        in an enchanted forest. The fairy tale has been passed down through generations.
        """
        
        result = extractor.process(text_with_phrases)
        keywords = result.get('results', {})
        
        # Should detect compound phrases using spaCy dependency parsing
        expected_phrases = ['folk tale', 'fairy tale', 'enchanted forest']
        found_phrases = [phrase for phrase in expected_phrases if phrase in keywords]
        
        assert len(found_phrases) >= 1, f"Should find compound phrases, found: {found_phrases}"
        
        # Compound phrases should have reasonable confidence scores
        for phrase in found_phrases:
            assert keywords[phrase] > 0.3, f"Compound phrase '{phrase}' should have decent confidence"
