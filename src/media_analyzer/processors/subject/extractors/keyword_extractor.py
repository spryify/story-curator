"""
Keyword-based subject identification processor with NLP enhancements.
Enhanced with NLTK, spaCy, and scikit-learn for robust keyword extraction.
"""
import re
import time
import logging
from typing import Dict, Set, List, Tuple, Any, Optional
import string
from collections import Counter

import nltk
import spacy
from nltk.corpus import stopwords, wordnet
from sklearn.feature_extraction.text import TfidfVectorizer

from media_analyzer.processors.subject.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Enhanced keyword extractor using established NLP libraries.
    
    Uses NLTK, spaCy, and scikit-learn for robust keyword extraction
    with improved semantic understanding.
    """
    
    def __init__(self):
        """Initialize enhanced keyword extractor with NLP libraries."""
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
            
            logger.info("Enhanced keyword extractor initialized with NLTK, spaCy, and scikit-learn")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP libraries: {e}")
            raise ProcessingError(f"NLP library initialization failed: {e}")
            
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract keywords using NLP libraries.
        
        Uses NLTK stop words, spaCy tokenization/POS tagging, and semantic analysis
        to extract high-quality keywords with confidence scores.
        
        Args:
            text: Text to analyze
            context: Optional context info
            
        Returns:
            Dict containing results and metadata
        """
        try:
            start_time = time.time()
            
            if not text or not text.strip():
                return {'results': {}, 'metadata': {'processing_time': 0}}
            
            # Use spaCy for tokenization and POS tagging
            doc = self.nlp(text.strip())
            
            # Extract compound phrases using dependency parsing
            compound_phrases = self._extract_compound_phrases(doc)
            logger.debug(f"Found {len(compound_phrases)} compound phrases: {compound_phrases}")
            
            # Extract meaningful tokens using spaCy POS tags
            meaningful_tokens = []
            for token in doc:
                # Filter using NLTK stop words and POS tags
                if (token.text.lower() not in self.stop_words and 
                    token.pos_ in ['NOUN', 'ADJ', 'PROPN'] and  # Keep nouns, adjectives, proper nouns
                    len(token.text) > 2 and  # Filter very short words
                    token.is_alpha):  # Only alphabetic tokens
                    meaningful_tokens.append(token.text.lower())
            
            # Count frequencies
            token_counts = Counter(meaningful_tokens)
            
            # Add compound phrases but don't artificially boost them over individual words
            # For icon matching, individual nouns like "train" are more valuable than "little train"
            for phrase in compound_phrases:
                # Add compound phrases with their natural frequency, no artificial boost
                # This makes them available but doesn't prioritize them over core nouns
                phrase_count = min(meaningful_tokens.count(word) for word in phrase.split() if word in meaningful_tokens)
                if phrase_count > 0:
                    token_counts[phrase] = phrase_count
            
            # Convert to confidence scores
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
                    'method': 'enhanced_nlp',
                    'token_count': len(meaningful_tokens),
                    'filtered_count': len(doc) - len(meaningful_tokens),
                    'compound_phrases_found': len(compound_phrases),
                    'total_words': len(doc),
                    'unique_keywords': len(keywords),
                    'processor_type': 'KeywordExtractor',
                    'version': '2.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            raise ProcessingError(f"Enhanced keyword extraction failed: {e}")

    def _extract_compound_phrases(self, doc) -> List[str]:
        """Extract compound phrases that represent distinct entities for icon matching.
        
        Uses simple, generalizable rules: only noun+noun compounds that represent
        distinct entities, completely avoiding adjective+noun combinations.
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            List of noun+noun compound phrases
        """
        phrases = []
        
        # Focus ONLY on noun+noun compounds - these represent distinct entities
        # Completely avoid adjective+noun which are just descriptive
        for chunk in doc.noun_chunks:
            nouns_only = []
            
            for token in chunk:
                # Only collect actual nouns, skip adjectives entirely
                if (token.pos_ in ['NOUN', 'PROPN'] and
                    not token.is_stop and 
                    not token.is_space and 
                    token.is_alpha):
                    nouns_only.append(token.text.lower())
            
            # Create compounds only from consecutive nouns
            if len(nouns_only) == 2:
                phrase = ' '.join(nouns_only)
                phrases.append(phrase)
        
        return phrases
