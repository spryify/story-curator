"""Icon matcher processor for matching subjects to icons."""

import logging
from typing import Dict, List, Any, Optional

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
            
            # Add keywords (rich metadata format)
            for keyword in keywords:
                confidence = keyword.get('confidence', 0)
                name = keyword.get('name', str(keyword))
                keyword_type = keyword.get('type', 'KEYWORD')
                context = keyword.get('context', {})
                
                if confidence > 0.5:  # Quality threshold
                    search_terms.append((name, 'keyword', confidence, keyword_type, context))
                    
            # Add topics (rich metadata format)
            for topic in topics:
                name = topic.get('name', str(topic))
                confidence = topic.get('confidence', 0.7)
                topic_type = topic.get('type', 'TOPIC')
                context = topic.get('context', {})
                search_terms.append((name, 'topic', confidence, topic_type, context))
                    
            # Add entities (rich metadata format)
            for entity in entities:
                name = entity.get('name', str(entity))
                confidence = entity.get('confidence', 0.6)
                entity_type = entity.get('type', 'ENTITY')
                context = entity.get('context', {})
                search_terms.append((name, 'entity', confidence, entity_type, context))
            
            # Search for icons using each search term (unified rich format)
            for term, term_type, base_confidence, subject_type, context in search_terms:
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
                        # Calculate confidence with rich metadata support
                        confidence = self._calculate_confidence(
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
    
    def _calculate_confidence(
        self, 
        term: str, 
        icon: IconData, 
        term_type: str, 
        base_confidence: float,
        subject_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate confidence score for icon match with rich metadata support.
        
        This unified method handles both basic and enhanced confidence calculations
        based on the available metadata.
        
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
        confidence = base_confidence * 0.8  # Start with 80% of base confidence
        
        # Core matching boosts
        term_lower = term.lower()
        
        # Boost for exact name matches
        if term_lower in icon.name.lower():
            confidence += 0.2
            
        # Boost for tag matches
        if icon.tags and any(term_lower in tag.lower() for tag in icon.tags):
            confidence += 0.15
            
        # Boost for description matches
        if icon.description and term_lower in icon.description.lower():
            confidence += 0.1
            
        # Enhanced subject type scoring (if rich metadata available)
        if subject_type:
            subject_type_lower = subject_type.lower()
            if subject_type_lower in ['entity', 'ner']:
                confidence += 0.13  # Named entities are very reliable (0.05 base + 0.08 bonus)
            elif subject_type_lower in ['keyword', 'keywords']:
                confidence += 0.08  # Keywords are reliable (0.05 base + 0.03 bonus)
            elif subject_type_lower in ['topic', 'topics']:
                confidence += 0.05  # Topics are moderately reliable (0.03 base + 0.02 bonus)
        else:
            # Fallback to basic term type scoring
            if term_type == 'keyword':
                confidence += 0.05
            elif term_type == 'topic':
                confidence += 0.03
            # Entities get no fallback boost
        
        # Context-based enhancements (if rich metadata available)
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
        
        # Enhanced exact matching
        if icon.name.lower() == term_lower:
            confidence += 0.15  # Exact name match is very strong
        elif term_lower in icon.name.lower().split():
            confidence += 0.12  # Word match in name
        
        # Enhanced tag matching
        if icon.tags:
            exact_tag_matches = sum(1 for tag in icon.tags if tag.lower() == term_lower)
            if exact_tag_matches > 0:
                confidence += 0.10 * min(exact_tag_matches, 3)  # Cap at 3 tag matches
            else:
                # Partial tag matches
                partial_matches = sum(1 for tag in icon.tags if term_lower in tag.lower())
                if partial_matches > 0:
                    confidence += 0.05 * min(partial_matches, 2)  # Cap at 2 partial matches
        
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
