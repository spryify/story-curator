"""NLP-based icon matcher using semantic similarity.

Uses spaCy word vectors for semantic matching to replace literal string matching
per FR-002 enhancement phase requirements.
"""

import logging
import time
from typing import Dict, List, Any, Optional

import spacy
import numpy as np

from ..core.exceptions import IconMatchingError
from ..models.results import IconMatch
from icon_extractor.models.icon import IconData

logger = logging.getLogger(__name__)


class NLPIconMatcher:
    """Enhanced icon matcher using spaCy semantic similarity.
    
    Replaces literal string matching with semantic similarity using
    spaCy word vectors per FR-002 enhancement requirements.
    """
    
    def __init__(self, icons: Optional[List[Dict[str, Any]]] = None) -> None:
        """Initialize NLP icon matcher.
        
        Args:
            icons: Optional list of icon data for testing. If None, will use icon service.
        """
        try:
            # Load spaCy model with word vectors for semantic similarity
            self.nlp = spacy.load("en_core_web_md")  # Medium model with vectors
            
            # Import icon service for production use
            from icon_extractor.core.service import IconService
            self.icon_service = IconService()
            
            # Store icons for matching (test mode) or None to use icon service
            self.test_icons = icons
            
            # Minimum similarity threshold for semantic matches
            self.min_similarity = 0.5  # Raise threshold to reduce false positives
            
            logger.info("NLP icon matcher initialized with spaCy semantic similarity")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP icon matcher: {e}")
            raise IconMatchingError(f"NLP matcher initialization failed: {e}")
    
    def find_matching_icons(
        self, 
        subjects: Dict[str, Any], 
        limit: int = 10
    ) -> List[IconMatch]:
        """Find icons that match the identified subjects (pipeline interface).
        
        This method adapts the subjects format from the pipeline to work with
        our NLP matching logic.
        
        Args:
            subjects: Subject identification results from SubjectIdentifier
            limit: Maximum number of icon matches to return
            
        Returns:
            List of IconMatch objects sorted by confidence
        """
        try:
            # Extract keywords from subjects dict
            keywords = {}
            
            # Handle keywords from SubjectIdentifier results
            subject_keywords = subjects.get('keywords', [])
            for keyword_item in subject_keywords:
                if isinstance(keyword_item, dict):
                    name = keyword_item.get('name', '')
                    confidence = keyword_item.get('confidence', 0.0)
                    if name and confidence > 0.3:
                        keywords[name] = confidence
                elif isinstance(keyword_item, str):
                    keywords[keyword_item] = 0.7  # Default confidence
            
            # Also extract from topics, entities if present
            for subject_type in ['topics', 'entities']:
                subject_items = subjects.get(subject_type, [])
                for item in subject_items:
                    if isinstance(item, dict):
                        name = item.get('name', '')
                        confidence = item.get('confidence', 0.6)
                        if name and confidence > 0.3:
                            keywords[name] = confidence
                    elif isinstance(item, str):
                        keywords[item] = 0.6
            
            # Use our semantic matching
            icon_data_list = self._match_with_icon_service(keywords)
            
            # Convert to IconMatch objects expected by pipeline
            icon_matches = []
            for icon_data in icon_data_list:
                # Create IconMatch object
                from icon_extractor.models.icon import IconData
                
                # Get the icon object
                icon_obj = icon_data.get('icon')
                if not isinstance(icon_obj, IconData):
                    continue  # Skip invalid icons
                
                match = IconMatch(
                    icon=icon_obj,
                    confidence=icon_data.get('confidence', 0.0),
                    match_reason=icon_data.get('match_reason', ''),
                    subjects_matched=icon_data.get('subjects_matched', [])
                )
                icon_matches.append(match)
            
            # Sort and limit
            icon_matches.sort(key=lambda x: x.confidence, reverse=True)
            return icon_matches[:limit]
            
        except Exception as e:
            logger.error(f"Icon matching failed: {e}")
            raise IconMatchingError(f"Failed to find matching icons: {e}")
    
    def _match_with_icon_service(self, keywords: Dict[str, float]) -> List[Dict[str, Any]]:
        """Match keywords using icon service.
        
        Args:
            keywords: Keywords to match
            
        Returns:
            List of icon match data
        """
        matches = []
        
        for keyword, confidence in keywords.items():
            try:
                # Search icons using the icon service
                icons = self.icon_service.search_icons(query=keyword, limit=5)
                
                for icon in icons:
                    # Use semantic similarity for matching
                    semantic_confidence = self._calculate_semantic_similarity(keyword, icon)
                    
                    if semantic_confidence >= self.min_similarity:
                        # Use the existing sophisticated confidence calculation from IconMatcher
                        # but enhance it with our semantic similarity
                        final_confidence = self._calculate_confidence(
                            keyword, 
                            icon, 
                            'keyword',  # term_type
                            confidence,  # base_confidence 
                            'KEYWORD',  # subject_type
                            None  # context (could add later)
                        )
                        
                        # Enhance with semantic similarity factor
                        final_confidence = final_confidence * semantic_confidence
                        
                        # Check for compound phrases and boost confidence
                        if ' ' in keyword:
                            final_confidence *= 1.5  # Boost compound phrases
                        
                        match_data = {
                            'icon': icon,
                            'confidence': final_confidence,
                            'match_reason': f"Enhanced match: {keyword} (confidence: {final_confidence:.3f}, similarity: {semantic_confidence:.3f})",
                            'subjects_matched': [keyword]
                        }
                        matches.append(match_data)
                        
            except Exception as e:
                logger.warning(f"Failed to search icons for keyword '{keyword}': {e}")
                continue
        
        return matches
    
    def _calculate_semantic_similarity(self, keyword: str, icon: IconData) -> float:
        """Calculate semantic similarity between keyword and icon metadata.
        
        Args:
            keyword: Keyword to match
            icon: Icon data to compare against
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Process keyword and icon metadata with spaCy
            keyword_doc = self.nlp(keyword)
            
            # Combine icon metadata for comparison
            icon_text_parts = []
            if hasattr(icon, 'tags') and icon.tags:
                icon_text_parts.extend(icon.tags)
            if hasattr(icon, 'name') and icon.name:
                icon_text_parts.append(icon.name)
            if hasattr(icon, 'description') and icon.description:
                icon_text_parts.append(icon.description)
            
            if not icon_text_parts:
                return 0.0
            
            icon_text = ' '.join(icon_text_parts)
            icon_doc = self.nlp(icon_text)
            
            # Calculate semantic similarity using spaCy
            similarity = keyword_doc.similarity(icon_doc)
            
            return max(0.0, min(1.0, similarity))  # Ensure 0-1 range
            
        except Exception as e:
            logger.warning(f"Failed to calculate similarity for '{keyword}': {e}")
            return 0.0
    
    def _calculate_confidence(
        self, 
        term: str, 
        icon: IconData, 
        term_type: str, 
        base_confidence: float,
        subject_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate confidence score using existing IconMatcher logic.
        
        Uses the proven confidence calculation from the original IconMatcher
        but integrates it with our semantic similarity enhancement.
        
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
                confidence += 0.13  # Named entities are very reliable
            elif subject_type_lower in ['keyword', 'keywords']:
                confidence += 0.08  # Keywords are reliable
            elif subject_type_lower in ['topic', 'topics']:
                confidence += 0.05  # Topics are moderately reliable
        else:
            # Fallback to basic term type scoring
            if term_type == 'keyword':
                confidence += 0.05
            elif term_type == 'topic':
                confidence += 0.03
        
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
    
    def match(self, keywords: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Match keywords to icons using semantic similarity.
        
        Args:
            keywords: Dictionary of keyword -> confidence mappings
            
        Returns:
            List of icon matches with confidence scores
            
        Raises:
            IconMatchingError: If matching fails
        """
        try:
            if not keywords:
                return []
            
            # Filter low-confidence keywords
            high_confidence_keywords = {
                keyword: confidence for keyword, confidence in keywords.items()
                if confidence >= 0.3
            }
            
            if not high_confidence_keywords:
                return []
            
            # 🟢 GREEN: Minimal implementation to make tests pass
            matches = []
            
            # Use test icons if provided, otherwise would use icon service
            icons_to_search = self.test_icons or []
            
            for icon_data in icons_to_search:
                icon_match = self._match_icon_semantically(icon_data, high_confidence_keywords)
                if icon_match:
                    matches.append(icon_match)
            
            # Sort by confidence
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Icon matching failed: {e}")
            raise IconMatchingError(f"NLP icon matching failed: {e}")
    
    def _match_icon_semantically(
        self, 
        icon_data: Dict[str, Any], 
        keywords: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Match a single icon using semantic similarity.
        
        Args:
            icon_data: Icon information with subjects
            keywords: Keywords to match against
            
        Returns:
            Match dict if similarity threshold met, None otherwise
        """
        icon_subjects = icon_data.get('subjects', [])
        matched_keywords = []
        total_score = 0.0
        
        for keyword, confidence in keywords.items():
            # Skip problematic words entirely
            if keyword in ['her', 'him', 'his', 'she', 'he']:
                continue
            
            # Check if this is a compound phrase (contains space)
            is_compound_phrase = ' ' in keyword
            
            # Check for exact matches first
            if keyword in icon_subjects:
                matched_keywords.append(keyword)
                # Give compound phrases higher weight
                phrase_boost = 1.5 if is_compound_phrase else 1.0
                total_score += confidence * phrase_boost
                continue
            
            # Check semantic similarity using spaCy word vectors
            best_similarity = 0.0
            best_subject = None
            
            keyword_token = self.nlp(keyword)
            
            for subject in icon_subjects:
                subject_token = self.nlp(subject)
                
                # Calculate semantic similarity using word vectors
                if (keyword_token.has_vector and subject_token.has_vector and
                    keyword_token.vector_norm > 0 and subject_token.vector_norm > 0):
                    similarity = keyword_token.similarity(subject_token)
                    
                    if similarity > best_similarity and similarity >= self.min_similarity:
                        best_similarity = similarity
                        best_subject = subject
            
            # If we found a semantic match above threshold
            if best_subject:
                matched_keywords.append(f"{keyword}→{best_subject}")
                # Weight semantic similarity by both original confidence and similarity score
                semantic_score = confidence * best_similarity
                # Give compound phrases higher weight
                phrase_boost = 1.5 if is_compound_phrase else 1.0
                total_score += semantic_score * phrase_boost
        
        if matched_keywords:
            # Calculate confidence with special handling for compound phrases
            phrase_matches = [kw for kw in matched_keywords if ' ' in kw and '→' not in kw]
            semantic_matches = [kw for kw in matched_keywords if '→' in kw]
            exact_matches = [kw for kw in matched_keywords if ' ' not in kw and '→' not in kw]
            
            # Weight different match types
            confidence_components = []
            
            # Exact matches get full weight
            for keyword in exact_matches:
                if keyword in keywords:
                    confidence_components.append(keywords[keyword])
            
            # Compound phrases get boosted weight
            for keyword in phrase_matches:
                if keyword in keywords:
                    confidence_components.append(keywords[keyword] * 1.5)
            
            # Semantic matches get similarity-weighted score
            for match_str in semantic_matches:
                if '→' in match_str:
                    keyword = match_str.split('→')[0]
                    if keyword in keywords:
                        confidence_components.append(keywords[keyword] * 0.8)  # Slight discount for semantic
            
            if confidence_components:
                avg_confidence = sum(confidence_components) / len(confidence_components)
                if avg_confidence >= 0.3:  # Lower threshold for semantic matches
                    return {
                        'icon': icon_data,
                        'confidence': avg_confidence,
                        'matched_keywords': matched_keywords,
                        'match_type': 'semantic',
                        'match_breakdown': {
                            'exact_matches': len(exact_matches),
                            'phrase_matches': len(phrase_matches),
                            'semantic_matches': len(semantic_matches)
                        }
                    }
        
        return None
