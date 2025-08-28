"""Icon matcher processor for matching subjects to icons."""

import logging
from typing import Dict, List, Any

from ..core.exceptions import IconMatchingError
from ..models.results import IconMatch

# Import existing components
from icon_extractor.core.service import IconService
from icon_extractor.models.icon import IconData

logger = logging.getLogger(__name__)


class IconMatcher:
    """Matches subjects to icons using the icon database."""
    
    def __init__(self):
        """Initialize the icon matcher with icon service."""
        self.icon_service = IconService()
        
    def find_matching_icons(
        self, 
        subjects: Dict[str, Any], 
        limit: int = 10
    ) -> List[IconMatch]:
        """Find icons that match the identified subjects.
        
        Args:
            subjects: Subject identification results
            limit: Maximum number of icon matches to return
            
        Returns:
            List of IconMatch objects sorted by confidence
        """
        try:
            icon_matches = []
            
            # Extract different types of subjects
            keywords = subjects.get('keywords', [])
            topics = subjects.get('topics', [])
            entities = subjects.get('entities', [])
            categories = subjects.get('categories', [])
            
            # Search for icons using different subject types
            search_terms = []
            
            # Add keywords with high confidence (>0.7)
            for keyword in keywords:
                if isinstance(keyword, dict) and keyword.get('confidence', 0) > 0.7:
                    search_terms.append((keyword['word'], 'keyword', keyword['confidence']))
                elif isinstance(keyword, str):
                    search_terms.append((keyword, 'keyword', 0.8))
                    
            # Add topics
            for topic in topics:
                if isinstance(topic, dict):
                    search_terms.append((topic.get('name', str(topic)), 'topic', topic.get('confidence', 0.7)))
                elif isinstance(topic, str):
                    search_terms.append((topic, 'topic', 0.7))
                    
            # Add entities
            for entity in entities:
                if isinstance(entity, dict):
                    search_terms.append((entity.get('text', str(entity)), 'entity', entity.get('confidence', 0.6)))
                elif isinstance(entity, str):
                    search_terms.append((entity, 'entity', 0.6))
            
            # Search for icons using each search term
            for term, term_type, base_confidence in search_terms:
                try:
                    # Search icons by term
                    icons = self.icon_service.search_icons(
                        query=term,
                        limit=5  # Limit per search term
                    )
                    
                    # Also try category-based search if we have categories
                    category_icons = []
                    if categories:
                        for category in categories:
                            category_str = category if isinstance(category, str) else str(category)
                            category_icons.extend(
                                self.icon_service.search_icons(
                                    query=term,
                                    category=category_str,
                                    limit=3
                                )
                            )
                    
                    # Combine results
                    all_icons = icons + category_icons
                    
                    # Create IconMatch objects
                    for icon in all_icons:
                        # Calculate confidence based on term type and match quality
                        confidence = self._calculate_confidence(
                            term, icon, term_type, base_confidence
                        )
                        
                        # Avoid duplicates
                        existing_match = next(
                            (m for m in icon_matches if m.icon.url == icon.url), 
                            None
                        )
                        
                        if existing_match:
                            # Update existing match with higher confidence
                            if confidence > existing_match.confidence:
                                existing_match.confidence = confidence
                                existing_match.subjects_matched.append(term)
                        else:
                            # Create new match
                            match = IconMatch(
                                icon=icon,
                                confidence=confidence,
                                match_reason=f"Matched {term_type}: {term}",
                                subjects_matched=[term]
                            )
                            icon_matches.append(match)
                            
                except Exception as e:
                    logger.warning(f"Failed to search icons for term '{term}': {e}")
                    continue
            
            # Sort by confidence and limit results
            icon_matches.sort(key=lambda x: x.confidence, reverse=True)
            return icon_matches[:limit]
            
        except Exception as e:
            logger.error(f"Icon matching failed: {e}")
            raise IconMatchingError(f"Failed to find matching icons: {e}") from e
    
    def _calculate_confidence(
        self, 
        term: str, 
        icon: IconData, 
        term_type: str, 
        base_confidence: float
    ) -> float:
        """Calculate confidence score for icon match.
        
        Args:
            term: Search term used
            icon: Matched icon
            term_type: Type of term (keyword, topic, entity)
            base_confidence: Base confidence from subject identification
            
        Returns:
            Calculated confidence score (0.0-1.0)
        """
        confidence = base_confidence * 0.8  # Start with 80% of base confidence
        
        # Boost for exact name matches
        if term.lower() in icon.name.lower():
            confidence += 0.2
            
        # Boost for tag matches
        if icon.tags and any(term.lower() in tag.lower() for tag in icon.tags):
            confidence += 0.15
            
        # Boost for description matches
        if icon.description and term.lower() in icon.description.lower():
            confidence += 0.1
            
        # Boost based on term type
        if term_type == 'keyword':
            confidence += 0.05  # Keywords are most reliable
        elif term_type == 'topic':
            confidence += 0.03  # Topics are moderately reliable
        # Entities get no boost (base level)
        
        # Boost for popular icons (if num_downloads available)
        if (icon.metadata and 
            icon.metadata.get('num_downloads') and 
            isinstance(icon.metadata['num_downloads'], (int, str))):
            try:
                downloads = int(str(icon.metadata['num_downloads']).replace(',', ''))
                if downloads > 1000:
                    confidence += 0.05
                elif downloads > 500:
                    confidence += 0.03
            except (ValueError, TypeError):
                pass
        
        # Cap at 1.0
        return min(confidence, 1.0)
