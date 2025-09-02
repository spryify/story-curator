"""Tests for NLPIconMatcher using TDD methodology.

This test suite implements the enhanced icon matching using NLP libraries
as specified in FR-002 feature specification.

Test-Driven Development approach:
1. 🔴 RED: Write failing test
2. 🟢 GREEN: Minimal implementation to pass
3. ♻️ REFACTOR: Improve code quality

Author: GitHub Copilot
Date: 2025-09-02
"""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock

from audio_icon_matcher.processors.nlp_icon_matcher import NLPIconMatcher
from audio_icon_matcher.core.exceptions import IconMatchingError


class TestNLPIconMatcher:
    """Test suite for NLP-based icon matcher using spaCy semantic similarity."""
    
    @pytest.fixture
    def sample_icons(self) -> List[Dict[str, Any]]:
        """Sample icon data for testing."""
        return [
            {
                'title': 'Frozen',
                'subjects': ['princess', 'snow', 'ice', 'winter', 'royal'],
                'url': 'https://example.com/frozen.jpg'
            },
            {
                'title': 'VeggieTales', 
                'subjects': ['vegetables', 'stories', 'children', 'moral'],
                'url': 'https://example.com/veggietales.jpg'
            },
            {
                'title': 'Fairy Tales',
                'subjects': ['fairy', 'tale', 'magic', 'enchanted', 'folk'],
                'url': 'https://example.com/fairytales.jpg'
            },
            {
                'title': 'Animal Stories',
                'subjects': ['animals', 'owl', 'forest', 'wildlife', 'nature'],
                'url': 'https://example.com/animals.jpg'
            }
        ]
    
    @pytest.fixture
    def matcher(self, sample_icons: List[Dict[str, Any]]) -> NLPIconMatcher:
        """Create NLP icon matcher instance with sample icons."""
        return NLPIconMatcher(sample_icons)
    
    def test_literal_matching_avoidance(self, matcher: NLPIconMatcher) -> None:
        """Test that literal string matching is avoided in favor of semantic similarity.
        
        Per FR-002, the original issue was that 'her' matched 'Frozen' through literal
        string matching. NLP approach should use semantic similarity instead.
        
        Args:
            matcher: NLP icon matcher instance
        """
        # 🔴 RED: This test will fail until we implement semantic similarity
        keywords_with_problematic_word = {
            'her': 0.8,  # This should NOT match Frozen anymore
            'story': 0.6,
            'tale': 0.9
        }
        
        matches = matcher.match(keywords_with_problematic_word)
        
        # Should not match Frozen based on 'her' anymore
        frozen_matches = [m for m in matches if m['icon']['title'] == 'Frozen']
        if frozen_matches:
            # If Frozen is matched, it should be based on semantic similarity, not 'her'
            frozen_match = frozen_matches[0]
            assert 'her' not in frozen_match['matched_keywords'], \
                f"'her' should not be a matched keyword for Frozen: {frozen_match['matched_keywords']}"
    
    def test_semantic_similarity_matching(self, matcher: NLPIconMatcher) -> None:
        """Test semantic similarity using spaCy word vectors.
        
        Per FR-002, should use spaCy word vectors to find semantically similar
        concepts even when exact string matches don't exist.
        
        Args:
            matcher: NLP icon matcher instance
        """
        # 🔴 RED: This test will fail until we implement semantic similarity
        keywords_with_similar_concepts = {
            'monarch': 0.9,  # Should match 'royal' in Frozen through semantic similarity
            'woodland': 0.8,  # Should match 'forest' in Animal Stories
            'fable': 0.7     # Should match 'tale' in Fairy Tales
        }
        
        matches = matcher.match(keywords_with_similar_concepts)
        
        # Should find semantic matches even without exact string matches
        assert len(matches) >= 2, f"Should find semantic matches, found {len(matches)}: {[m['icon']['title'] for m in matches]}"
        
        # Check that similarity scores are reasonable
        for match in matches:
            assert match['confidence'] > 0.3, f"Semantic match confidence too low: {match['confidence']}"
    
    def test_compound_phrase_matching(self, matcher: NLPIconMatcher) -> None:
        """Test matching compound phrases against icon subjects.
        
        Per FR-002, compound phrases should be matched as complete units
        and should have higher relevance than individual word matches.
        
        Args:
            matcher: NLP icon matcher instance  
        """
        # 🔴 RED: This test will fail until we implement compound phrase matching
        keywords_with_compound_phrases = {
            'fairy tale': 0.9,   # Should strongly match Fairy Tales icon
            'folk': 0.4,         # Individual word should have lower relevance
            'tale': 0.5          # Individual word should have lower relevance
        }
        
        matches = matcher.match(keywords_with_compound_phrases)
        
        # Should find the Fairy Tales icon
        fairy_matches = [m for m in matches if m['icon']['title'] == 'Fairy Tales']
        assert len(fairy_matches) >= 1, f"Should match Fairy Tales icon, found: {[m['icon']['title'] for m in matches]}"
        
        # Compound phrase match should have higher confidence than individual words
        fairy_match = fairy_matches[0]
        assert fairy_match['confidence'] > 0.6, \
            f"Compound phrase match should have high confidence: {fairy_match['confidence']}"
    
    def test_empty_keywords_handling(self, matcher: NLPIconMatcher) -> None:
        """Test handling of empty or invalid keyword inputs."""
        # Empty keywords
        matches = matcher.match({})
        assert matches == [], "Empty keywords should return empty matches"
        
        # None keywords  
        matches = matcher.match(None)
        assert matches == [], "None keywords should return empty matches"
        
        # All low-confidence keywords
        low_confidence_keywords = {'word': 0.1, 'another': 0.2}
        matches = matcher.match(low_confidence_keywords)
        assert len(matches) == 0, "Low confidence keywords should not produce matches"
