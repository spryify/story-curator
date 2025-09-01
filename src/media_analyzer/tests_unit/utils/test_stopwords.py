"""Unit tests for stopwords module."""

import pytest

from media_analyzer.utils.stopwords import STOPWORDS


class TestStopwords:
    """Test stopwords functionality."""
    
    def test_stopwords_exists(self):
        """Test that STOPWORDS is defined and is a set."""
        assert STOPWORDS is not None
        assert isinstance(STOPWORDS, set)
    
    def test_stopwords_not_empty(self):
        """Test that STOPWORDS contains words."""
        assert len(STOPWORDS) > 0
    
    def test_common_stopwords_present(self):
        """Test that common English stopwords are present."""
        common_stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have',
            'what', 'when', 'where', 'who', 'which', 'why', 'i', 'you'
        }
        
        for word in common_stopwords:
            assert word in STOPWORDS, f"Common stopword '{word}' not found in STOPWORDS"
    
    def test_stopwords_are_lowercase(self):
        """Test that all stopwords are lowercase."""
        for word in STOPWORDS:
            assert word.islower(), f"Stopword '{word}' is not lowercase"
    
    def test_stopwords_are_strings(self):
        """Test that all stopwords are strings."""
        for word in STOPWORDS:
            assert isinstance(word, str), f"Stopword '{word}' is not a string"
    
    def test_no_empty_strings(self):
        """Test that there are no empty strings in stopwords."""
        for word in STOPWORDS:
            assert len(word) > 0, "Found empty string in STOPWORDS"
    
    def test_no_whitespace_in_words(self):
        """Test that stopwords don't contain whitespace."""
        for word in STOPWORDS:
            assert ' ' not in word, f"Stopword '{word}' contains space"
            assert '\t' not in word, f"Stopword '{word}' contains tab"
            assert '\n' not in word, f"Stopword '{word}' contains newline"
    
    def test_stopwords_reasonable_size(self):
        """Test that stopwords set has a reasonable size."""
        # Should have a reasonable number of stopwords (not too few, not too many)
        assert 30 <= len(STOPWORDS) <= 200, f"STOPWORDS has {len(STOPWORDS)} words, expected 30-200"
    
    def test_specific_pronouns_present(self):
        """Test that common pronouns are included."""
        pronouns = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        present_pronouns = pronouns.intersection(STOPWORDS)
        assert len(present_pronouns) > 0, "No common pronouns found in STOPWORDS"
    
    def test_specific_articles_present(self):
        """Test that articles are included."""
        articles = {'a', 'an', 'the'}
        for article in articles:
            assert article in STOPWORDS, f"Article '{article}' not found in STOPWORDS"
    
    def test_specific_prepositions_present(self):
        """Test that common prepositions are included."""
        prepositions = {'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of'}
        present_prepositions = prepositions.intersection(STOPWORDS)
        assert len(present_prepositions) >= 5, f"Too few prepositions found in STOPWORDS: {present_prepositions}"
    
    def test_specific_conjunctions_present(self):
        """Test that common conjunctions are included."""
        conjunctions = {'and', 'or', 'but', 'if', 'then', 'else'}
        present_conjunctions = conjunctions.intersection(STOPWORDS)
        assert len(present_conjunctions) >= 3, f"Too few conjunctions found in STOPWORDS: {present_conjunctions}"
    
    def test_modal_verbs_present(self):
        """Test that modal verbs are included."""
        modals = {'can', 'could', 'should', 'would', 'may', 'might', 'must', 'shall'}
        present_modals = modals.intersection(STOPWORDS)
        assert len(present_modals) >= 4, f"Too few modal verbs found in STOPWORDS: {present_modals}"
    
    def test_stopwords_immutable(self):
        """Test that STOPWORDS is a set (which is mutable, but we test it doesn't change accidentally)."""
        # Make a copy to compare against
        original_stopwords = STOPWORDS.copy()
        original_length = len(STOPWORDS)
        
        # Verify it's the same after accessing it
        assert STOPWORDS == original_stopwords
        assert len(STOPWORDS) == original_length
    
    def test_membership_operations(self):
        """Test that membership operations work correctly."""
        # Test positive cases
        assert 'the' in STOPWORDS
        assert 'and' in STOPWORDS
        assert 'is' in STOPWORDS
        
        # Test negative cases (words that shouldn't be stopwords)
        assert 'python' not in STOPWORDS
        assert 'computer' not in STOPWORDS
        assert 'testing' not in STOPWORDS
