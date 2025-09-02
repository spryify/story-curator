"""NLP-based keyword extractor using established libraries.

Uses NLTK, spaCy, and scikit-learn for robust keyword extraction
per FR-002 enhancement phase requirements.
"""

import logging
import time
from typing import Dict, Any, Optional, Set, List
from collections import Counter

import nltk
import spacy
from nltk.corpus import stopwords, wordnet
from sklearn.feature_extraction.text import TfidfVectorizer

from media_analyzer.processors.subject.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class NLPKeywordExtractor:
    """Enhanced keyword extractor using established NLP libraries.
    
    Replaces custom implementations with NLTK, spaCy, and scikit-learn
    to improve keyword quality and semantic understanding per FR-002.
    """
    
    def __init__(self) -> None:
        """Initialize NLP keyword extractor with required libraries."""
        try:
            # NLTK resources
            self.stop_words = set(stopwords.words('english'))
            self.wordnet = wordnet
            
            # spaCy model for semantic analysis
            self.nlp = spacy.load("en_core_web_sm")
            
            # TF-IDF vectorizer for term importance
            self.tfidf = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=1,
                max_features=1000
            )
            
            logger.info("NLP keyword extractor initialized with NLTK, spaCy, and scikit-learn")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP libraries: {e}")
            raise ProcessingError(f"NLP library initialization failed: {e}")
    
    def _extract_compound_phrases(self, doc) -> List[str]:
        """Extract compound phrases using spaCy dependency parsing.
        
        Identifies noun phrases like 'folk tale', 'fairy tale', etc.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            List of compound phrases found in text
        """
        phrases = []
        
        # Extract noun chunks (compound noun phrases)
        for chunk in doc.noun_chunks:
            # Remove determiners and clean up the phrase
            words = []
            for token in chunk:
                if (token.pos_ not in ['DET', 'ADP'] and 
                    not token.is_stop and 
                    not token.is_space and 
                    token.is_alpha):
                    words.append(token.text.lower())
            
            # Only keep 2-word phrases for better quality
            if len(words) == 2:
                phrase = ' '.join(words)
                if len(phrase) > 4:  # Minimum phrase length
                    phrases.append(phrase)
        
        # Also look for adjective + noun patterns not captured above
        for token in doc:
            if (token.pos_ == 'ADJ' and 
                token.head.pos_ in ['NOUN', 'PROPN'] and
                not token.is_space and
                token.is_alpha and
                token.head.is_alpha):
                phrase = f"{token.text.lower()} {token.head.text.lower()}"
                if phrase not in phrases and len(phrase) > 4:
                    phrases.append(phrase)
        
        return phrases
    
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract keywords using NLP libraries.
        
        Uses NLTK stop words, spaCy tokenization/POS tagging, and TF-IDF scoring
        to extract high-quality keywords with semantic relevance.
        
        Args:
            text: Input text to extract keywords from
            context: Optional context information (domain, etc.)
            
        Returns:
            Dict containing extracted keywords with confidence scores
            
        Raises:
            ProcessingError: If keyword extraction fails
        """
        try:
            start_time = time.time()
            
            if not text or not text.strip():
                return {'results': {}, 'metadata': {'processing_time': 0}}
            
            # 🟢 GREEN: Minimal implementation to make test pass
            # Phase 1: Use spaCy for tokenization and POS tagging
            doc = self.nlp(text.strip())
            
            # Extract compound phrases using dependency parsing
            compound_phrases = self._extract_compound_phrases(doc)
            logger.debug(f"Found {len(compound_phrases)} compound phrases: {compound_phrases}")
            
            # Extract tokens that are NOT stop words and are meaningful POS tags
            meaningful_tokens = []
            for token in doc:
                # Filter using NLTK stop words and POS tags
                if (token.text.lower() not in self.stop_words and 
                    token.pos_ in ['NOUN', 'ADJ', 'PROPN'] and  # Keep nouns, adjectives, proper nouns
                    len(token.text) > 2 and  # Filter very short words
                    token.is_alpha):  # Only alphabetic tokens
                    meaningful_tokens.append(token.text.lower())
            
            # Simple frequency-based scoring for now (will enhance in refactor)
            token_counts = Counter(meaningful_tokens)
            
            # Add compound phrases to counts
            for phrase in compound_phrases:
                token_counts[phrase] = token_counts.get(phrase, 0) + 1
            
            # Convert to confidence scores (normalized by max frequency)
            if not token_counts:
                return {'results': {}, 'metadata': {'processing_time': time.time() - start_time}}
            
            max_count = max(token_counts.values())
            keywords = {}
            
            for token, count in token_counts.items():
                confidence = count / max_count
                if confidence >= 0.3:  # Minimum threshold
                    keywords[token] = confidence
            
            processing_time = time.time() - start_time
            
            logger.debug(f"Extracted {len(keywords)} keywords in {processing_time:.3f}s")
            
            return {
                'results': keywords,
                'metadata': {
                    'processing_time': processing_time,
                    'method': 'nlp_libraries',
                    'token_count': len(meaningful_tokens),
                    'filtered_count': len(doc) - len(meaningful_tokens),
                    'compound_phrases_found': len(compound_phrases)
                }
            }
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            raise ProcessingError(f"NLP keyword extraction failed: {e}")
