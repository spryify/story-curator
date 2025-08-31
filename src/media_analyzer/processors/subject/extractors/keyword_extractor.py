"""
Keyword-based subject identification processor.
"""
import re
from typing import Dict, Set, List, Tuple, Any
import string
from collections import Counter


class KeywordExtractor:
    """Identifies subjects based on keyword matching."""
    
    def __init__(self):
        """Initialize processor."""
        # Common stopwords to filter out
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'over',
            'after', 'is', 'am', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'shall', 'should', 'may', 'might', 'must', 'can', 'could',
            'a', 'an', 'this', 'that', 'these', 'those', 'his', 'hers',
            'its', 'their', 'our', 'we', 'they', 'them', 'he', 'she',
            'it', 'i', 'you', 'who', 'which', 'what', 'when', 'where',
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'than', 'however', 'therefore',
            'consequently'
        }
        
        # Important compound words to detect
        self.compound_phrases = {
            'artificial intelligence': 0.95,
            'machine learning': 0.95,
            'deep learning': 0.95,
            'natural language processing': 0.95,
            'computer vision': 0.95,
            'neural networks': 0.9,
            'cloud computing': 0.9,
        }
            
    def process(self, text: str, context = None) -> Dict[str, Any]:
        """Process text and return keyword matches.
        
        Args:
            text: Text to analyze
            context: Optional context info
            
        Returns:
            Dict containing results and metadata
        """
        text = text.lower()
        results = {}
        
        # First check for compound phrases
        for phrase, base_score in self.compound_phrases.items():
            if phrase in text:
                results[phrase] = base_score
                # Remove the phrase from text to avoid double-counting
                text = text.replace(phrase, '')
        
        # Tokenize remaining text
        words = text.split()
        
        # Count word frequencies
        word_counts = Counter(words)
        total_words = len(words)
        
        # Calculate scores based on frequency and repetition
        for word, count in word_counts.items():
            if len(word) > 2 and word not in self.stop_words:  # Filter stopwords and short words
                # Base score from frequency
                freq_score = count / total_words
                # Boost score for repetition
                repetition_boost = min(0.4, (count - 1) * 0.1)  # Up to 0.4 boost for repetition
                # Combine scores with a base minimum
                score = min(0.95, 0.3 + freq_score + repetition_boost)
                results[word] = score
                
        return {
            "results": results,
            "metadata": {
                "total_words": total_words,
                "unique_keywords": len(results),
                "processor_type": "KeywordExtractor",
                "version": "1.0"
            }
        }
