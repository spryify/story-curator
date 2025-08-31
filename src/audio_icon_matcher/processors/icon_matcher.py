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
            
            # Add keywords with confidence filtering
            for keyword in keywords:
                if isinstance(keyword, dict):
                    confidence = keyword.get('confidence', 0)
                    name = keyword.get('name', str(keyword))
                    keyword_type = keyword.get('type', 'KEYWORD')
                    context = keyword.get('context', {})
                    
                    # Use higher threshold for better quality matches
                    if confidence > 0.5:  # Reduced from 0.7 to include more good matches
                        search_terms.append((name, 'keyword', confidence, keyword_type, context))
                elif isinstance(keyword, str):
                    search_terms.append((keyword, 'keyword', 0.8, 'KEYWORD', {}))
                    
            # Add topics with enhanced metadata
            for topic in topics:
                if isinstance(topic, dict):
                    name = topic.get('name', str(topic))
                    confidence = topic.get('confidence', 0.7)
                    topic_type = topic.get('type', 'TOPIC')
                    context = topic.get('context', {})
                    search_terms.append((name, 'topic', confidence, topic_type, context))
                elif isinstance(topic, str):
                    search_terms.append((topic, 'topic', 0.7, 'TOPIC', {}))
                    
            # Add entities with enhanced metadata
            for entity in entities:
                if isinstance(entity, dict):
                    name = entity.get('name', str(entity))
                    confidence = entity.get('confidence', 0.6)
                    entity_type = entity.get('type', 'ENTITY')
                    context = entity.get('context', {})
                    search_terms.append((name, 'entity', confidence, entity_type, context))
                elif isinstance(entity, str):
                    search_terms.append((entity, 'entity', 0.6, 'ENTITY', {}))
            
            # Search for icons using each search term
            for term_data in search_terms:
                if len(term_data) == 5:
                    # Enhanced format with metadata
                    term, term_type, base_confidence, subject_type, context = term_data
                else:
                    # Legacy format for backward compatibility
                    term, term_type, base_confidence = term_data[:3]
                    subject_type = term_type.upper()
                    context = {}
                
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
                        # Calculate confidence with enhanced metadata
                        confidence = self._calculate_confidence_enhanced(
                            term, icon, term_type, base_confidence, subject_type, context
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
    
    def _calculate_confidence_enhanced(
        self, 
        term: str, 
        icon: IconData, 
        term_type: str, 
        base_confidence: float,
        subject_type: str,
        context: Dict[str, Any]
    ) -> float:
        """Enhanced confidence calculation with subject metadata.
        
        This method builds on the base confidence calculation and adds
        metadata-aware enhancements for richer subject analysis.
        
        Args:
            term: Search term used
            icon: Matched icon
            term_type: Type of term (keyword, topic, entity)
            base_confidence: Base confidence from subject identification
            subject_type: Enhanced subject type (KEYWORD, ENTITY, TOPIC, etc.)
            context: Additional context information (domain, language, etc.)
            
        Returns:
            Calculated confidence score (0.0-1.0)
        """
        # Start with the base calculation (handles core matching logic)
        confidence = self._calculate_confidence(term, icon, term_type, base_confidence)
        
        # Enhanced scoring based on rich subject type metadata
        if subject_type:
            subject_type_lower = subject_type.lower()
            
            # Boost for high-quality subject types (beyond base term_type handling)
            if subject_type_lower in ['ner', 'entity']:
                confidence += 0.08  # Named entities are very reliable
            elif subject_type_lower in ['keyword', 'keywords']:
                confidence += 0.03  # Additional boost for verified keywords (base method already adds 0.05)
            elif subject_type_lower in ['topic', 'topics']:
                confidence += 0.02  # Additional boost for verified topics (base method already adds 0.03)
        
        # Context-based enhancements (new functionality not in base method)
        if context:
            domain = context.get('domain')
            language = context.get('language', 'en')
            
            # Boost for relevant domain matching
            if domain and any(domain_word in icon.name.lower() or 
                            (icon.tags and any(domain_word in tag.lower() for tag in icon.tags))
                            for domain_word in domain.lower().split()):
                confidence += 0.05
            
            # Language consistency boost
            if language == 'en':  # English content typically has better icon coverage
                confidence += 0.02
        
        # Additional exact matching enhancements (builds on base method's name matching)
        term_lower = term.lower()
        
        # Enhanced tag matching (more granular than base method)
        if icon.tags:
            exact_tag_matches = sum(1 for tag in icon.tags if tag.lower() == term_lower)
            if exact_tag_matches > 1:  # Only boost if more than 1 exact match (base method covers 1 match)
                confidence += 0.05 * min(exact_tag_matches - 1, 2)  # Additional boost for multiple exact matches
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
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
