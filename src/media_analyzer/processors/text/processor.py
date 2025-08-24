"""Text processing module for summarization and analysis."""

from typing import Dict, Optional

import spacy
from nltk.tokenize import sent_tokenize
from media_analyzer.core.exceptions import SummarizationError


class TextProcessor:
    """Handles text processing and summarization."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the text processor with optional configuration."""
        self.config = config or {}
        self.nlp = spacy.load("en_core_web_sm")

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Generate a summary of the input text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Summarized text
            
        Raises:
            SummarizationError: If summarization fails
        """
        try:
            # Tokenize into sentences
            sentences = sent_tokenize(text)
            
            if not sentences:
                return ""
                
            # If text is already short, return as is
            if len(sentences) <= 3:
                return text
                
            # Process with spaCy
            doc = self.nlp(text)
            
            # Score sentences based on importance
            scores = {}
            for sent in doc.sents:
                # Score based on position and key phrase presence
                position_score = 1.0 if sent.text in [sentences[0], sentences[-1]] else 0.0
                
                # Score based on presence of key entities and noun phrases
                content_score = len([ent for ent in sent.ents]) + len([np for np in sent.noun_chunks])
                
                # Combine scores
                scores[sent.text] = position_score + content_score
            
            # Sort sentences by score
            ranked_sentences = sorted(
                [(sent, scores.get(sent, 0.0)) for sent in sentences],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Select top sentences
            num_sentences = max(3, len(sentences) // 3)  # At least 3 sentences or 1/3 of original
            summary_sentences = [sent for sent, _ in ranked_sentences[:num_sentences]]
            
            # Restore original order
            summary_sentences.sort(key=lambda x: sentences.index(x))
            
            summary = " ".join(summary_sentences)
            
            # Apply max length if specified
            if max_length:
                words = summary.split()
                if len(words) > max_length:
                    summary = " ".join(words[:max_length]) + "..."
            
            return summary
            
        except Exception as e:
            raise SummarizationError(f"Failed to generate summary: {e}")
