"""
Topic modeling processor using LDA.
"""
from typing import Dict, Any
import gensim
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from gensim.parsing.preprocessing import preprocess_string, strip_punctuation
from gensim.parsing.preprocessing import strip_numeric, strip_multiple_whitespaces


class TopicProcessor:
    """Implements topic modeling using LDA."""
    
    def __init__(self, num_topics: int = 5):
        """Initialize the topic processor."""
        self.num_topics = num_topics
        self.dictionary = None
        self.lda_model = None
        
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract topics using LDA.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing:
                - results: List of extracted topics with scores
                - metadata: Processing metadata
        """
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Create or update dictionary
        if not self.dictionary:
            self.dictionary = corpora.Dictionary([processed_text])
        
        # Convert to bag of words
        bow = self.dictionary.doc2bow(processed_text)
        
        # Create or update LDA model
        if not self.lda_model:
            self.lda_model = LdaModel(
                corpus=[bow],
                id2word=self.dictionary,
                num_topics=self.num_topics,
                passes=10
            )
        
        # Get topics
        topics = self.lda_model.get_document_topics(bow)
        
        # Convert to result format
        results = []
        for topic_id, score in topics:
            topic_terms = self.lda_model.show_topic(topic_id)
            name = " ".join(term for term, _ in topic_terms[:3])
            results.append({
                "name": name,
                "score": float(score),
                "metadata": {
                    "topic_id": topic_id,
                    "terms": topic_terms
                }
            })
            
        return {
            "results": results,
            "metadata": {
                "num_topics": self.num_topics,
                "dictionary_size": len(self.dictionary)
            }
        }
    
    def _preprocess_text(self, text: str) -> list:
        """Preprocess text for topic modeling."""
        filters = [
            strip_punctuation,
            strip_numeric,
            strip_multiple_whitespaces
        ]
        return preprocess_string(text, filters)
