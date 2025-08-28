"""Result ranker for ranking and filtering icon results."""

import logging
from typing import Dict, List, Any

from ..models.results import IconMatch

logger = logging.getLogger(__name__)


class ResultRanker:
    """Ranks and filters icon results based on various criteria."""
    
    def rank_results(
        self, 
        icon_matches: List[IconMatch], 
        subjects: Dict[str, Any],
        limit: int = 10
    ) -> List[IconMatch]:
        """Rank icon matches and return top results.
        
        Args:
            icon_matches: List of icon matches to rank
            subjects: Original subject identification results
            limit: Maximum number of results to return
            
        Returns:
            Ranked list of IconMatch objects
        """
        # Apply additional ranking criteria
        for match in icon_matches:
            match.confidence = self._adjust_confidence(match, subjects)
        
        # Sort by confidence (descending) and return top results
        ranked_matches = sorted(icon_matches, key=lambda x: x.confidence, reverse=True)
        return ranked_matches[:limit]
    
    def _adjust_confidence(self, match: IconMatch, subjects: Dict[str, Any]) -> float:
        """Adjust confidence based on additional criteria.
        
        Args:
            match: Icon match to adjust
            subjects: Subject identification results
            
        Returns:
            Adjusted confidence score
        """
        confidence = match.confidence
        
        # Boost for multiple subject matches
        if len(match.subjects_matched) > 1:
            confidence += 0.1
        
        # Boost for category alignment
        categories = subjects.get('categories', [])
        if categories and match.icon.category:
            for category in categories:
                category_str = category if isinstance(category, str) else str(category)
                if category_str.lower() in match.icon.category.lower():
                    confidence += 0.08
                    break
        
        # Slight penalty for very generic icons (fewer than 3 tags)
        if not match.icon.tags or len(match.icon.tags) < 3:
            confidence -= 0.02
        
        # Boost for icons with good descriptions
        if match.icon.description and len(match.icon.description) > 20:
            confidence += 0.03
        
        return min(confidence, 1.0)
