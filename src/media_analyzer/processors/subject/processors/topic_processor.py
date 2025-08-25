"""Topic extraction processor using frequency-based scoring."""

import re
import math
from collections import Counter
from typing import Any, Dict, List, Set, Tuple

from media_analyzer.utils.stopwords import STOPWORDS
from media_analyzer.utils import logger


from .base import BaseProcessor

class TopicProcessor(BaseProcessor):
    """Extract key topics from text using phrase frequency-based scoring."""

    def __init__(self):
        """Initialize topic processor with default parameters."""
        self.min_length = 5  # Minimum text length in words
        self.max_topics = 5   # Maximum topics to return
        self.max_ngram = 3    # Maximum words in a phrase
        self.min_score = 0.1  # Minimum score threshold
        
    def process(self, text: str) -> Dict[str, float]:
        """Extract topics from text.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: Mapping of topics to confidence scores
            
        Raises:
            ValueError: If text is empty or too short
        """
        # Input validation
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        # Extract topics
        return self._extract_topics(text)

    def extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text.
        
        Args:
            text (str): Input text to extract phrases from
            
        Returns:
            List[str]: List of extracted phrases
        """
        # Common technical phrases to preserve
        common_phrases = {
            'artificial intelligence', 'machine learning', 'deep learning',
            'cloud computing', 'neural network', 'data science',
            'computer vision', 'natural language processing'
        }
        
        # First look for common phrases
        phrases = set()
        text_lower = text.lower()
        for phrase in common_phrases:
            if phrase in text_lower:
                phrases.add(phrase)
        
        # Normalize and tokenize remaining text
        text = re.sub(r'[^\w\s]', ' ', text_lower)
        words = [w for w in text.split() if w not in STOPWORDS and len(w) > 2]
        
        # Build phrases of different lengths
        for i in range(len(words)):
            # Single words
            if len(words[i]) >= 4:
                phrases.add(words[i])
            # Multi-word phrases
            for j in range(2, min(self.max_ngram + 1, len(words) - i + 1)):
                phrase = ' '.join(words[i:i+j])
                # Skip if it's a subsequence of an already found common phrase
                if not any(phrase in p for p in phrases if len(p) > len(phrase)):
                    phrases.add(phrase)
        
        return list(phrases)

    def score_phrase(self, phrase: str, count: int, total_words: int, max_freq: int) -> float:
        """Score a phrase based on frequency and length.
        
        Args:
            phrase (str): The phrase to score
            count (int): Number of times the phrase appears
            total_words (int): Total number of words in text
            max_freq (int): Maximum frequency of any phrase
            
        Returns:
            float: Score between 0 and 1
        """
        # Base TF (term frequency) score
        tf = count / max_freq
        
        # IDF with smoothing to avoid division by zero
        idf = 1 + math.log((total_words + 1) / (count + 1))
        
        # Length bonus - higher scores for multi-word phrases
        word_count = len(phrase.split())
        length_bonus = 1.0 if word_count == 1 else 1.2 * word_count / self.max_ngram
        
        # Importance bonus for known important words
        importance_words = {
            "technology", "science", "research", "development",
            "intelligence", "learning", "computing", "system"
        }
        importance_bonus = 1.2 if any(word in phrase for word in importance_words) else 1.0
        
        # Combine scores with different weights
        score = tf * idf * length_bonus * importance_bonus
        return min(score, 1.0)  # Cap at 1.0

    def _extract_topics(self, text: str) -> Dict[str, float]:
        """Extract topics from text with scores."""
        # Validate input
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        # Extract initial phrases
        phrases = self.extract_phrases(text)
        
        # Count phrase frequencies
        freq = Counter(phrases)
        if not freq:
            return {}
            
        # Calculate scores
        max_freq = max(freq.values())
        topics = {}
        
        for phrase, count in freq.most_common(self.max_topics):
            # Base score from frequency
            score = 0.5 + (0.5 * count / max_freq)
            
            # Bonus for phrase length
            length_bonus = min(0.3, len(phrase.split()) * 0.1)
            
            # Combine scores
            final_score = min(1.0, score + length_bonus)
            
            if final_score >= self.min_score:
                topics[phrase] = final_score
                
        return topics
                
        return topics

    def process(self, text: str) -> Dict[str, Any]:
        """Process text to extract topics."""
        self._validate_input(text)
        
        # Get raw topics with scores
        raw_topics = self._extract_topics(text)
        
        return {
            "results": raw_topics,
            "metadata": self._get_metadata()
        }
