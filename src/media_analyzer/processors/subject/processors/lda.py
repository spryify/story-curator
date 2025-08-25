"""Topic processor that extracts key topics and phrases from text."""
import logging
import math
import re
from typing import Dict, List
from collections import Counter

logger = logging.getLogger(__name__)

STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has',
    'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was',
    'were', 'will', 'with', 'but', 'they', 'have', 'had', 'what', 'when',
    'where', 'who', 'which', 'why', 'how', 'all', 'any', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'than', 'too', 'very',
    'can', 'will', 'just', 'should', 'now'
}

logger = logging.getLogger(__name__)

# Common English stopwords to filter
STOPWORDS = set(['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 
                 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 
                 'that', 'the', 'to', 'was', 'were', 'will', 'with'])


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
        self.min_length = 10  # Minimum text length in words
        self.max_topics = 5   # Maximum topics to return
        self.max_ngram = 3    # Maximum words in a phrase

    def extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text.
        
        Args:
            text (str): Input text to extract phrases from
            
        Returns:
            List[str]: List of extracted phrases
        """
        # Normalize and tokenize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = [w for w in text.split() if w not in STOPWORDS and len(w) > 2]
        
        # Build phrases of different lengths
        phrases = []
        for i in range(len(words)):
            for j in range(1, min(self.max_ngram + 1, len(words) - i + 1)):
                phrase = ' '.join(words[i:i+j])
                if len(phrase.split()) > 1:  # Only keep multi-word phrases
                    phrases.append(phrase)
        return phrases

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
        # TF-IDF style scoring
        tf = count / max_freq  # Term frequency normalized
        idf = 1 + math.log(total_words / (count + 1))  # Inverse doc frequency
        length_bonus = len(phrase.split()) / self.max_ngram  # Favor longer phrases
        return min(tf * idf * length_bonus, 1.0)  # Cap at 1.0

    def process(self, text: str) -> Dict[str, float]:
        """Process text to extract topics with confidence scores.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: Dictionary mapping topics to confidence scores
        """
        # Validate input
        if not isinstance(text, str):
            logger.error("Input must be a string")
            return {}

        if not text or len(text.split()) < self.min_length:
            logger.warning("Text too short for topic extraction")
            return {}

        try:
            # Extract and count phrases
            phrases = self.extract_phrases(text)
            if not phrases:
                logger.warning("No valid phrases found in text")
                return {}
            
            # Calculate scores
            counts = Counter(phrases)
            if not counts:
                return {}
            
            total_words = len(text.split())
            max_freq = max(counts.values())
            
            # Score phrases
            scores = {}
            for phrase, count in counts.most_common(self.max_topics * 2):
                score = self.score_phrase(phrase, count, total_words, max_freq)
                if score > 0.1:  # Filter low-confidence topics
                    scores[phrase] = score
            
            # Return top topics
            return dict(sorted(
                scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:self.max_topics])

        except Exception as e:
            logger.error(f"Failed to extract topics: {str(e)}")
            return {}
        try:
            # Input validation
            if not text or len(text.split()) < self.min_length:
                logger.warning("Text too short for meaningful topic modeling")
                return {}

            # Preprocess text
            processed_docs = self.preprocess(text)
            if not processed_docs:
                return {}

            # Create/update dictionary
            self.dictionary = corpora.Dictionary(processed_docs)
            corpus = [self.dictionary.doc2bow(doc) for doc in processed_docs]

            # Train model
            self.lda_model = models.LdaModel(
                corpus,
                num_topics=self.num_topics,
                id2word=self.dictionary,
                random_state=42
            )

            # Get topics with scores
            topics = {}
            for idx, topic in self.lda_model.print_topics():
                for term, score in self.lda_model.get_topic_terms(idx):
                    term = self.dictionary[term]
                    if score > 0.1:  # Only keep significant terms
                        topics[term] = float(score)

            return topics

        except Exception as e:
            logger.error(f"Topic processing failed: {str(e)}")
            return {}
        try:
            # Input validation
            if not text or len(text.split()) < self.min_length:
                self.logger.warning("Text too short for meaningful topic modeling")
                return {}

            # Preprocess text
            processed_docs = self.preprocess(text)
            if not processed_docs:
                return {}

            # Create/update dictionary
            self.dictionary = corpora.Dictionary(processed_docs)
            corpus = [self.dictionary.doc2bow(doc) for doc in processed_docs]

            # Train model
            self.lda_model = models.LdaModel(
                corpus,
                num_topics=self.num_topics,
                id2word=self.dictionary,
                random_state=42
            )

            # Get topics with scores
            topics = {}
            for idx, topic in self.lda_model.print_topics():
                for term, score in self.lda_model.get_topic_terms(idx):
                    term = self.dictionary[term]
                    if score > 0.1:  # Only keep significant terms
                        topics[term] = float(score)

            return topics

        except Exception as e:
            self.logger.error(f"Topic processing failed: {str(e)}")
            return {}
        # Check for minimum text length
        words = text.split()
            if len(text.split()) < self.min_length:
                logger.warning("Text too short for meaningful topic modeling")
                return {}        try:
            # Tokenize and preprocess
            processed_text = [word.lower() for word in words]
            
            # Create or update dictionary
            texts = [processed_text]
            if not self.dictionary:
                self.dictionary = corpora.Dictionary(texts)
            
            # Convert text to bag of words
            corpus = [self.dictionary.doc2bow(text) for text in texts]
            
            # Train LDA model
            self.lda_model = models.LdaModel(
                corpus=corpus,
                id2word=self.dictionary,
                num_topics=self.num_topics,
                random_state=42,
                iterations=50
            )

            # Get topics with words and probabilities
            results = []
            for topic_id in range(self.num_topics):
                topic_words = self.lda_model.show_topic(topic_id)
                # Create readable topic name from top 3 words
                topic_name = " ".join(word for word, prob in topic_words[:3])
                results.append({
                    "name": topic_name,
                    "score": sum(prob for _, prob in topic_words),
                    "metadata": {
                        "topic_id": topic_id,
                        "terms": topic_words
                    }
                })

            return {
                "results": results,
                "metadata": {
                    "num_topics": self.num_topics,
                    "dictionary_size": len(self.dictionary),
                    "num_words": len(words)
                }
            }

        except Exception as e:
            # Return empty results on error
            return {
                "results": [],
                "metadata": {
                    "error": str(e),
                    "num_words": len(words)
                }
            }
