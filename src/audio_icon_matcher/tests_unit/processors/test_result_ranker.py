"""Unit tests for result_ranker.py."""

import pytest
from unittest.mock import Mock

from audio_icon_matcher.processors.result_ranker import ResultRanker
from audio_icon_matcher.models.results import IconMatch
from icon_extractor.models.icon import IconData


class TestResultRanker:
    """Test ResultRanker functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ranker = ResultRanker()
        
        # Create test icons and matches
        self.icon1 = IconData(
            name="high-confidence-icon",
            url="https://example.com/high.svg",
            tags=["test", "quality"],
            metadata={'num_downloads': '5000'}
        )
        
        self.icon2 = IconData(
            name="medium-confidence-icon", 
            url="https://example.com/medium.svg",
            tags=["test"],
            metadata={'num_downloads': '1000'}
        )
        
        self.icon3 = IconData(
            name="low-confidence-icon",
            url="https://example.com/low.svg", 
            tags=["other"],
            metadata={'num_downloads': '100'}
        )
        
        self.match1 = IconMatch(
            icon=self.icon1,
            confidence=0.9,
            match_reason="high confidence match",
            subjects_matched=["test", "quality"]
        )
        
        self.match2 = IconMatch(
            icon=self.icon2,
            confidence=0.7,
            match_reason="medium confidence match", 
            subjects_matched=["test"]
        )
        
        self.match3 = IconMatch(
            icon=self.icon3,
            confidence=0.3,
            match_reason="low confidence match",
            subjects_matched=["other"]
        )
    
    def test_rank_results_by_confidence_descending(self):
        """Test that results are ranked by confidence in descending order."""
        matches = [self.match2, self.match3, self.match1]  # Mixed order
        subjects = {'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]}
        
        ranked = self.ranker.rank_results(matches, subjects)
        
        # Should be sorted by adjusted confidence descending
        # match1: 0.9 + 0.1 (multiple subjects) - 0.02 (few tags) = 0.98
        # match2: 0.7 - 0.02 (few tags) = 0.68  
        # match3: 0.3 - 0.02 (few tags) = 0.28
        assert abs(ranked[0].confidence - 0.98) < 0.01  # adjusted match1
        assert abs(ranked[1].confidence - 0.68) < 0.01  # adjusted match2
        assert abs(ranked[2].confidence - 0.28) < 0.01  # adjusted match3
    
    def test_rank_results_empty_list(self):
        """Test ranking with empty list."""
        subjects = {'keywords': []}
        ranked = self.ranker.rank_results([], subjects)
        assert ranked == []
    
    def test_rank_results_single_match(self):
        """Test ranking with single match."""
        subjects = {'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]}
        ranked = self.ranker.rank_results([self.match1], subjects)
        assert len(ranked) == 1
        assert ranked[0] == self.match1
    
    def test_rank_results_with_equal_confidence(self):
        """Test ranking with equal confidence scores."""
        # Create matches with same confidence
        equal_match1 = IconMatch(
            icon=self.icon1,
            confidence=0.8,
            match_reason="match 1",
            subjects_matched=["test"]
        )
        
        equal_match2 = IconMatch(
            icon=self.icon2, 
            confidence=0.8,
            match_reason="match 2",
            subjects_matched=["test"]
        )
        
        matches = [equal_match2, equal_match1]
        subjects = {'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]}
        ranked = self.ranker.rank_results(matches, subjects)
        
        # Order should be maintained when confidence is equal after adjustments
        # Both should have 0.8 - 0.02 (few tags) = 0.78
        assert len(ranked) == 2
        assert all(match.confidence == 0.78 for match in ranked)
    
    def test_rank_results_preserves_match_objects(self):
        """Test that ranking preserves original match objects."""
        matches = [self.match1, self.match2, self.match3]
        subjects = {'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]}
        
        ranked = self.ranker.rank_results(matches, subjects)
        
        # Original matches should be preserved (not modified)
        assert ranked[0] is self.match1
        assert ranked[1] is self.match2
        assert ranked[2] is self.match3
        
        # Original objects should have same properties
        assert ranked[0].subjects_matched == ["test", "quality"]
        assert ranked[1].subjects_matched == ["test"]
        assert ranked[2].subjects_matched == ["other"]
    
    def test_rank_results_with_limit(self):
        """Test ranking with result limit."""
        matches = [self.match1, self.match2, self.match3]
        subjects = {'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]}
        
        ranked = self.ranker.rank_results(matches, subjects, limit=2)
        
        # Should return only top 2 results with adjusted confidence
        assert len(ranked) == 2
        assert abs(ranked[0].confidence - 0.98) < 0.01  # adjusted match1
        assert abs(ranked[1].confidence - 0.68) < 0.01  # adjusted match2
