"""Topic-based subject identification."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from collections import Counter
import math

@dataclass
class TopicResult:
    """Result from topic processing."""
    name: str
    confidence: float
    metadata: Dict[str, Any]

class TopicProcessor:
    """Identifies subjects based on topic modeling."""
    
    # Common stopwords to filter out
    STOPWORDS = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
        'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which',
        'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
        'him', 'know', 'take', 'people', 'into', 'year', 'your', 'some',
        'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look',
        'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after',
        'use', 'two', 'how', 'our', 'well', 'way', 'even', 'new', 'want',
        'because', 'any', 'these', 'give', 'day', 'most', 'us'
    }

    def __init__(self, min_topic_freq: int = 2):
        """Initialize topic processor.
        
        Args:
            min_topic_freq: Minimum frequency for a topic
        """
        self.min_topic_freq = min_topic_freq
        
    def process(self, text: str, context = None) -> List[TopicResult]:
        """Process text and identify topics.
        
        Args:
            text: Text to analyze
            context: Optional context info
            
        Returns:
            List of TopicResult with identified topics
        """
        # Split into words and normalize
        words = text.lower().split()
        
        # Remove stopwords and short words
        words = [w for w in words if w not in self.STOPWORDS and len(w) > 2]
        
        # Get word frequencies
        word_freq = Counter(words)
        
        # Calculate TF-IDF-like scores
        max_freq = max(word_freq.values())
        word_scores = {}
        
        for word, freq in word_freq.items():
            if freq >= self.min_topic_freq:
                # TF score normalized by max frequency
                tf = freq / max_freq
                
                # IDF-like score based on word length and frequency
                idf = math.log(1 + len(word)) * math.log(1 + freq)
                
                word_scores[word] = tf * idf
        
        # Convert to results
        results = []
        for word, score in sorted(word_scores.items(), key=lambda x: x[1], reverse=True):
            # Normalize score to confidence between 0 and 1
            confidence = min(score / max(word_scores.values()), 1.0)
            
            # Adjust confidence based on context
            if context and hasattr(context, 'domain'):
                confidence = self._adjust_confidence_for_domain(
                    confidence, word, context.domain
                )
            
            results.append(TopicResult(
                name=word,
                confidence=confidence,
                metadata={
                    "type": "topic",
                    "frequency": word_freq[word],
                    "score": score
                }
            ))
            
        return results[:10]  # Return top 10 topics
    
    def _adjust_confidence_for_domain(self, confidence: float, word: str, domain: str) -> float:
        """Adjust confidence based on domain context."""
        # Domain-specific boosts
        tech_terms = {
            'algorithm', 'data', 'model', 'network', 'system',
            'cloud', 'code', 'software', 'application', 'api',
            'learning', 'intelligence', 'neural', 'vision'
        }
        
        bio_terms = {
            'gene', 'protein', 'cell', 'molecular', 'genome',
            'dna', 'rna', 'sequence', 'enzyme', 'biology'
        }
        
        boost = 1.0
        if domain == "technology" and word in tech_terms:
            boost = 1.2
        elif domain == "biotechnology" and word in bio_terms:
            boost = 1.2
            
        return min(confidence * boost, 1.0)
