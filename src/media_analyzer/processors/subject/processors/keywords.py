"""
Keyword extraction processor using RAKE algorithm.
"""
from typing import Dict, Any, List, Tuple
import re
from collections import defaultdict
from string import punctuation


class KeywordProcessor:
    """Implements keyword extraction using the RAKE algorithm."""
    
    def __init__(self, min_chars: int = 4, min_words: int = 1, max_words: int = 5):
        """Initialize the keyword processor."""
        self.min_chars = min_chars
        self.min_words = min_words
        self.max_words = max_words
        self.stopwords = set([
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "were", "will", "with"
        ])
        
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract keywords using RAKE.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing:
                - results: List of extracted keywords with scores
                - metadata: Processing metadata
        """
        # Split text into phrases
        phrases = self._extract_phrases(text)
        
        # Calculate word scores
        word_scores = self._calculate_word_scores(phrases)
        
        # Calculate phrase scores
        phrase_scores = self._calculate_phrase_scores(phrases, word_scores)
        
        # Convert to result format
        results = []
        for phrase, score in phrase_scores:
            results.append({
                "name": phrase,
                "score": score,
                "metadata": {
                    "word_count": len(phrase.split())
                }
            })
            
        return {
            "results": results,
            "metadata": {
                "total_phrases": len(phrases),
                "min_chars": self.min_chars,
                "min_words": self.min_words,
                "max_words": self.max_words
            }
        }
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract candidate phrases from text."""
        # Convert to lowercase and clean text
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Split into phrases
        words = text.split()
        phrases = []
        current_phrase = []
        
        for word in words:
            if word in self.stopwords or len(word) < self.min_chars:
                if current_phrase:
                    phrase = ' '.join(current_phrase)
                    if self.min_words <= len(current_phrase) <= self.max_words:
                        phrases.append(phrase)
                    current_phrase = []
            else:
                current_phrase.append(word)
                
        return phrases
    
    def _calculate_word_scores(self, phrases: List[str]) -> Dict[str, float]:
        """Calculate scores for individual words."""
        word_freq = defaultdict(float)
        word_degree = defaultdict(float)
        
        for phrase in phrases:
            words = phrase.split()
            degree = len(words) - 1
            for word in words:
                word_freq[word] += 1
                word_degree[word] += degree
                
        word_scores = {}
        for word in word_freq:
            word_scores[word] = word_degree[word] / word_freq[word]
            
        return word_scores
    
    def _calculate_phrase_scores(self, 
                               phrases: List[str], 
                               word_scores: Dict[str, float]) -> List[Tuple[str, float]]:
        """Calculate scores for phrases."""
        phrase_scores = []
        
        for phrase in phrases:
            words = phrase.split()
            score = sum(word_scores[word] for word in words)
            phrase_scores.append((phrase, score))
            
        # Sort by score in descending order
        return sorted(phrase_scores, key=lambda x: x[1], reverse=True)
