"""Topic extraction processor using frequency-based scoring."""

import re
import math
from collections import Counter
from typing import Dict, List

from media_analyzer.utils.stopwords import STOPWORDS
from media_analyzer.utils import logger


class TopicProcessor:
    """Extract key topics from text using phrase frequency-based scoring."""

    def __init__(self):
        """Initialize topic processor with default parameters."""
        self.min_length = 5  # Minimum text length in words
        self.max_topics = 5   # Maximum topics to return
        self.max_ngram = 3    # Maximum words in a phrase
        self.min_score = 0.1  # Minimum score threshold

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

    def process(self, text: str) -> Dict[str, float]:
        """Process text to extract topics with confidence scores.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: Dictionary mapping topics to confidence scores
            
        Raises:
            ValueError: If input text is empty
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided for topic extraction")

        try:
            # Clean and normalize input text
            text = text.strip()
            if not isinstance(text, str) or not text:
                logger.warning("Invalid or empty input text")
                return {}
                
            # Get word count
            words = text.split()
            word_count = len(words)
            
            # For very short texts, lower the minimum length requirement
            min_length = min(self.min_length, max(3, word_count // 2))
            
            if word_count < min_length:
                logger.warning(f"Text too short ({word_count} words)")
                return {}

            # Extract and count phrases
            phrases = self.extract_phrases(text)
            if not phrases:
                logger.warning("No valid phrases found in text")
                return {}
            
            # Calculate scores
            counts = Counter(phrases)
            total_words = len(words)
            max_freq = max(counts.values())
            
            # Score all phrases
            scores = {}
            for phrase, count in counts.most_common(self.max_topics * 3):
                score = self.score_phrase(phrase, count, total_words, max_freq)
                if score > self.min_score:
                    scores[phrase] = score
            
            if not scores:
                # If no phrases scored above threshold, take the best one
                phrase, count = counts.most_common(1)[0]
                score = self.score_phrase(phrase, count, total_words, max_freq)
                scores[phrase] = score
            
            # Return top topics
            return dict(sorted(
                scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:self.max_topics])

        except Exception as e:
            logger.error(f"Failed to extract topics: {str(e)}")
            raise  # Re-raise to test error handling
