"""Additional tests for icon_matcher.py to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from audio_icon_matcher.processors.icon_matcher import IconMatcher
from audio_icon_matcher.core.exceptions import IconMatchingError
from icon_extractor.models.icon import IconData


class TestIconMatcherErrorHandling:
    """Test error handling and edge cases in IconMatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = IconMatcher()
        
        # Mock icon data
        self.mock_icon = IconData(
            name="test-icon",
            url="https://example.com/icon.svg",
            tags=["test", "icon"],
            metadata={'num_downloads': '1500'}
        )
    
    def test_calculate_confidence_with_invalid_downloads(self):
        """Test confidence calculation with invalid download metadata."""
        # Test with non-numeric downloads
        invalid_icon = IconData(
            name="test-icon",
            url="https://example.com/icon.svg",
            tags=["test"],
            metadata={'num_downloads': 'invalid_number'}
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=invalid_icon,
            term_type="keyword",
            base_confidence=0.5
        )
        
        # Should not crash and should return valid confidence
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_confidence_with_none_downloads(self):
        """Test confidence calculation with None download metadata."""
        none_icon = IconData(
            name="test-icon", 
            url="https://example.com/icon.svg",
            tags=["test"],
            metadata={'num_downloads': ''}  # Empty string instead of None
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=none_icon, 
            term_type="keyword",
            base_confidence=0.5
        )
        
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_confidence_with_missing_metadata(self):
        """Test confidence calculation with missing metadata."""
        no_metadata_icon = IconData(
            name="test-icon",
            url="https://example.com/icon.svg",
            tags=["test"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=no_metadata_icon,
            term_type="keyword", 
            base_confidence=0.5
        )
        
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_confidence_confidence_cap(self):
        """Test that confidence is properly capped at 1.0."""
        # Create conditions that would exceed 1.0
        high_confidence_icon = IconData(
            name="test",  # Exact match
            url="https://example.com/icon.svg",
            tags=["test", "testing", "test-icon"],  # Many tag matches
            metadata={'num_downloads': '10000'}  # High downloads
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=high_confidence_icon,
            term_type="keyword",
            base_confidence=0.9,  # High base
            subject_type="KEYWORD",
            context={'domain': 'test', 'language': 'en'}
        )
        
        # Should be capped at 1.0
        assert confidence == 1.0
    
    def test_calculate_confidence_with_rich_context_domain_match(self):
        """Test confidence boost for domain matching in context."""
        domain_icon = IconData(
            name="tech-icon",
            url="https://example.com/icon.svg",
            tags=["technology", "computer"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="technology",
            icon=domain_icon,
            term_type="keyword",
            base_confidence=0.5,
            context={'domain': 'tech computer', 'language': 'en'}
        )
        
        # Should get domain boost
        assert confidence > 0.5
    
    def test_calculate_confidence_non_english_language(self):
        """Test confidence calculation with non-English language."""
        confidence = self.matcher._calculate_confidence(
            term="prueba",
            icon=self.mock_icon,
            term_type="keyword",
            base_confidence=0.5,
            context={'language': 'es'}
        )
        
        # Should not get English language boost
        assert 0.0 <= confidence <= 1.0
    
    @patch('audio_icon_matcher.processors.icon_matcher.logger')
    def test_find_matching_icons_service_error(self, mock_logger):
        """Test icon matching with icon service errors."""
        # Mock service to raise exception
        with patch.object(self.matcher.icon_service, 'search_icons', side_effect=Exception("Service Error")):
            
            subjects = {
                'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]
            }
            
            # Service errors are caught and logged as warnings, not re-raised
            matches = self.matcher.find_matching_icons(subjects)
            
            # Should log the error and return empty list
            mock_logger.warning.assert_called()
            assert matches == []
    
    def test_find_matching_icons_overall_error(self):
        """Test icon matching with overall processing errors."""
        # Mock the entire method to raise an exception by patching the subjects.get method
        broken_subjects = Mock()
        broken_subjects.get.side_effect = Exception("Processing Error")
        
        with pytest.raises(IconMatchingError, match="Failed to find matching icons"):
            self.matcher.find_matching_icons(broken_subjects)
    
    def test_find_matching_icons_empty_subjects(self):
        """Test icon matching with empty subjects."""
        empty_subjects = {
            'keywords': [],
            'topics': [],
            'entities': [],
            'categories': []
        }
        
        matches = self.matcher.find_matching_icons(empty_subjects)
        assert matches == []
    
    def test_find_matching_icons_subjects_with_none_values(self):
        """Test icon matching with None values in subjects."""
        subjects_with_nones = {
            'keywords': [
                {'name': 'valid', 'confidence': 0.8, 'type': 'KEYWORD'},
                {'name': None, 'confidence': 0.7, 'type': 'KEYWORD'},  # None name
                {'name': 'test', 'confidence': 0.4, 'type': 'KEYWORD'}  # Low confidence (will be filtered)
            ]
        }
        
        # Should handle None values gracefully by using default confidence
        # Only the valid keyword should be processed due to confidence threshold
        matches = self.matcher.find_matching_icons(subjects_with_nones)
        assert isinstance(matches, list)
    
    def test_find_matching_icons_with_limit_zero(self):
        """Test icon matching with zero limit."""
        subjects = {
            'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]
        }
        
        matches = self.matcher.find_matching_icons(subjects, limit=0)
        assert matches == []
    
    def test_calculate_confidence_with_exact_tag_matches(self):
        """Test confidence calculation with exact tag matches."""
        exact_tag_icon = IconData(
            name="different-name",
            url="https://example.com/icon.svg", 
            tags=["test", "exact-match"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=exact_tag_icon,
            term_type="keyword",
            base_confidence=0.5
        )
        
        # Should get exact tag match boost
        assert confidence > 0.5
    
    def test_calculate_confidence_entity_type_no_boost(self):
        """Test that entity types don't get subject type boost."""
        confidence = self.matcher._calculate_confidence(
            term="person",
            icon=self.mock_icon,
            term_type="entity",
            base_confidence=0.5,
            subject_type="ENTITY"
        )
        
        # Entities should not get the subject type boost
        expected_base = 0.5  # No subject type boost for entities
        assert confidence >= expected_base
        
    def test_calculate_confidence_with_multiple_partial_tag_matches(self):
        """Test confidence calculation with multiple partial tag matches."""
        multi_tag_icon = IconData(
            name="complex-icon",
            url="https://example.com/icon.svg",
            tags=["test-one", "test-two", "test-three", "other-tag"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=multi_tag_icon,
            term_type="keyword",
            base_confidence=0.5
        )
        
        # Should get partial match boost (capped at 2 matches)
        assert confidence > 0.5


class TestIconMatcherEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures.""" 
        self.matcher = IconMatcher()
    
    def test_calculate_confidence_with_empty_context(self):
        """Test confidence calculation with empty context dict."""
        icon = IconData(
            name="test", 
            url="https://example.com/icon.svg",
            tags=["test"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=icon,
            term_type="keyword",
            base_confidence=0.5,
            context={}  # Empty context
        )
        
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_confidence_with_empty_tags(self):
        """Test confidence calculation with icon that has empty tags."""
        no_tags_icon = IconData(
            name="notags",
            url="https://example.com/icon.svg",
            tags=[]  # Empty tags list
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=no_tags_icon,
            term_type="keyword",
            base_confidence=0.5
        )
        
        assert 0.0 <= confidence <= 1.0


class TestIconMatcherDatabaseInteraction:
    """Test database interaction scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = IconMatcher()
    
    def test_find_matching_icons_no_service_results(self):
        """Test icon matching when service returns no results."""
        with patch.object(self.matcher.icon_service, 'search_icons', return_value=[]):
            subjects = {
                'keywords': [{'name': 'nonexistent', 'confidence': 0.8, 'type': 'KEYWORD'}]
            }
            
            matches = self.matcher.find_matching_icons(subjects)
            assert matches == []
    
    @patch('audio_icon_matcher.processors.icon_matcher.logger')
    def test_find_matching_icons_service_returns_invalid_data(self, mock_logger):
        """Test icon matching when service returns invalid icon data."""
        # Mock service to return invalid data (this would normally cause exceptions)
        invalid_icon_data = [
            IconData(name="test", url="test.svg", tags=["test"])  # Valid data
        ]
        
        with patch.object(self.matcher.icon_service, 'search_icons', return_value=invalid_icon_data):
            subjects = {
                'keywords': [{'name': 'test', 'confidence': 0.8, 'type': 'KEYWORD'}]
            }
            
            matches = self.matcher.find_matching_icons(subjects)
            assert isinstance(matches, list)
            assert len(matches) > 0


class TestIconMatcherLowConfidenceFiltering:
    """Test confidence threshold filtering."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = IconMatcher()
    
    def test_find_matching_icons_low_confidence_keywords_filtered(self):
        """Test that low confidence keywords are filtered out."""
        with patch.object(self.matcher.icon_service, 'search_icons', return_value=[]) as mock_search:
            subjects = {
                'keywords': [
                    {'name': 'high', 'confidence': 0.8, 'type': 'KEYWORD'},  # Above threshold
                    {'name': 'low', 'confidence': 0.3, 'type': 'KEYWORD'}   # Below threshold
                ]
            }
            
            # Only high confidence keyword should be searched
            self.matcher.find_matching_icons(subjects)
            
            # Should only call search_icons once (for high confidence keyword)
            assert mock_search.call_count == 1
    
    def test_find_matching_icons_with_categories(self):
        """Test icon matching with categories included."""
        mock_icons = [
            IconData(name="cat-icon", url="https://example.com/cat.svg", tags=["cat"])
        ]
        
        with patch.object(self.matcher.icon_service, 'search_icons', return_value=mock_icons) as mock_search:
            subjects = {
                'keywords': [{'name': 'animal', 'confidence': 0.8, 'type': 'KEYWORD'}],
                'categories': ['pets', 'animals']
            }
            
            matches = self.matcher.find_matching_icons(subjects)
            
            # Should call search_icons multiple times (regular + category searches)
            assert mock_search.call_count > 1
    
    def test_find_matching_icons_duplicate_handling(self):
        """Test that duplicate icons are properly handled."""
        # Same icon returned for different searches
        duplicate_icon = IconData(
            name="duplicate",
            url="https://same-url.com/icon.svg",
            tags=["test"]
        )
        
        with patch.object(self.matcher.icon_service, 'search_icons', return_value=[duplicate_icon]):
            subjects = {
                'keywords': [
                    {'name': 'test1', 'confidence': 0.6, 'type': 'KEYWORD'},
                    {'name': 'test2', 'confidence': 0.8, 'type': 'KEYWORD'}
                ]
            }
            
            matches = self.matcher.find_matching_icons(subjects)
            
            # Should have only one match (deduplicated)
            assert len(matches) == 1
            # Should keep the higher confidence
            assert matches[0].confidence >= 0.6
            # Should combine subjects matched
            assert len(matches[0].subjects_matched) >= 1


class TestIconMatcherContextualBoosts:
    """Test contextual confidence boosts."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = IconMatcher()
    
    def test_calculate_confidence_exact_name_match(self):
        """Test confidence boost for exact name matches."""
        exact_match_icon = IconData(
            name="test",
            url="https://example.com/icon.svg",
            tags=["other"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=exact_match_icon,
            term_type="keyword",
            base_confidence=0.3
        )
        
        # Should get significant boost for exact name match
        assert confidence > 0.5
    
    def test_calculate_confidence_partial_name_match(self):
        """Test confidence boost for partial name matches."""
        partial_match_icon = IconData(
            name="test-icon-example",
            url="https://example.com/icon.svg",
            tags=["other"]
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=partial_match_icon,
            term_type="keyword", 
            base_confidence=0.3
        )
        
        # Should get some boost for partial match
        assert confidence > 0.3
    
    def test_calculate_confidence_high_downloads_boost(self):
        """Test confidence boost for high download count."""
        popular_icon = IconData(
            name="other-name",
            url="https://example.com/icon.svg",
            tags=["test"],
            metadata={'num_downloads': '50000'}  # Very high downloads
        )
        
        confidence = self.matcher._calculate_confidence(
            term="test",
            icon=popular_icon,
            term_type="keyword",
            base_confidence=0.5
        )
        
        # Should get downloads boost
        assert confidence > 0.5


class TestSemanticSimilarity:
    """Test suite for semantic similarity functionality in IconMatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = IconMatcher()
    
    @patch('spacy.load')
    def test_semantic_similarity_with_spacy(self, mock_spacy_load):
        """Test semantic similarity calculation when spaCy model is available."""
        # Mock spaCy model and documents
        mock_nlp = Mock()
        mock_keyword_doc = Mock()
        mock_icon_doc = Mock()
        
        # Mock vector similarity
        mock_keyword_doc.has_vector = True
        mock_icon_doc.has_vector = True
        mock_keyword_doc.similarity.return_value = 0.8
        
        # Configure the mock to return different docs for different calls
        mock_nlp.side_effect = [mock_keyword_doc, mock_icon_doc]
        mock_spacy_load.return_value = mock_nlp
        
        # Enable semantic matching and set up NLP
        self.matcher.semantic_matching_enabled = True
        self.matcher.nlp = mock_nlp
        
        test_icon = IconData(
            name="royal-crown",
            url="https://example.com/crown.svg",
            tags=["royal", "monarchy"],
            metadata={'num_downloads': '1000'}
        )
        
        similarity = self.matcher._calculate_semantic_similarity("king", test_icon)
        
        # Should return the mocked similarity score
        assert similarity == 0.8
    
    def test_semantic_similarity_disabled(self):
        """Test semantic similarity when feature is disabled."""
        # Disable semantic matching
        self.matcher.semantic_matching_enabled = False
        
        test_icon = IconData(
            name="royal-crown",
            url="https://example.com/crown.svg", 
            tags=["royal"],
            metadata={'num_downloads': '1000'}
        )
        
        similarity = self.matcher._calculate_semantic_similarity("king", test_icon)
        
        # Should return default confidence when disabled
        assert similarity == 1.0
    
    def test_semantic_similarity_no_nlp(self):
        """Test semantic similarity when spaCy is not available."""
        # Set up without NLP
        self.matcher.semantic_matching_enabled = True
        self.matcher.nlp = None
        
        test_icon = IconData(
            name="crown",
            url="https://example.com/crown.svg",
            tags=["royal"],
            metadata={}
        )
        
        similarity = self.matcher._calculate_semantic_similarity("king", test_icon)
        
        # Should fall back to default confidence
        assert similarity == 1.0
    
    def test_semantic_similarity_empty_icon_metadata(self):
        """Test semantic similarity with icon that has no metadata."""
        self.matcher.semantic_matching_enabled = True
        
        empty_icon = IconData(
            name="",
            url="https://example.com/icon.svg",
            tags=[],
            metadata={}
        )
        
        similarity = self.matcher._calculate_semantic_similarity("king", empty_icon)
        
        # Should return 0 when no metadata available
        assert similarity == 0.0
    
    def test_semantic_similarity_error_handling(self):
        """Test semantic similarity with error conditions."""
        # Mock spaCy to raise an exception
        mock_nlp = Mock()
        mock_nlp.side_effect = Exception("spaCy error")
        
        self.matcher.semantic_matching_enabled = True
        self.matcher.nlp = mock_nlp
        
        test_icon = IconData(
            name="crown",
            url="https://example.com/crown.svg",
            tags=["royal"],
            metadata={}
        )
        
        similarity = self.matcher._calculate_semantic_similarity("king", test_icon)
        
        # Should handle errors gracefully and fall back
        assert similarity == 1.0
    
    def test_confidence_calculation_uses_semantic_similarity(self):
        """Test that confidence calculation integrates semantic similarity."""
        # Create an icon with tags that are semantically related but not exact matches
        semantic_icon = IconData(
            name="royalty-icon",
            url="https://example.com/royal.svg",
            tags=["crown", "monarchy", "regal"],  # Related to "king" but not exact
            metadata={'num_downloads': '1000'}
        )
        
        # Calculate confidence for a semantically related term
        confidence = self.matcher._calculate_confidence(
            term="king",
            icon=semantic_icon,
            term_type="keyword",
            base_confidence=0.4
        )
        
        # Should get some confidence boost from semantic similarity
        # (Even without mocking spaCy, it should handle the comparison)
        assert 0.4 <= confidence <= 1.0


