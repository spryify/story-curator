"""Text processing module for summarization and analysis."""

from typing import Dict, Optional

import spacy
from nltk.tokenize import sent_tokenize
from media_analyzer.core.exceptions import SummarizationError


class TextProcessor:
    """Handles text processing operations like summarization."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        
    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Summarize the given text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary in characters
            
        Returns:
            Summarized text
            
        Raises:
            TypeError: If text is None
            ValueError: If max_length is invalid
        """
        if not isinstance(text, str):
            raise TypeError("Invalid input text")
            
        if not text.strip():
            return ""
            
        if max_length is not None:
            if not isinstance(max_length, int) or max_length <= 0:
                raise ValueError("max_length must be positive")
        
        # For now, implement a simple summarization
        # In a real implementation, this would use a proper summarization algorithm
        words = text.split()
        if max_length:
            # Take first N words that fit within max_length
            summary = ""
            for word in words:
                if len(summary) + len(word) + 1 <= max_length:
                    summary += (" " + word if summary else word)
                else:
                    break
            return summary
        elif len(words) > 50:  # Arbitrary threshold for demo
            return " ".join(words[:50]) + "..."
        else:
            return text
        self.nlp = spacy.load("en_core_web_sm")

    def summarize(self, text: str | None, max_length: int = 100) -> str:
        """Summarize the given text to specified maximum length.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary in characters
            
        Returns:
            Summarized text string
            
        Raises:
            TypeError: If text is not a string
            ValueError: If max_length is not positive
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")
            
        if max_length <= 0:
            raise ValueError("max_length must be positive")
            
        # Handle empty or whitespace-only text
        if not text.strip():
            return ""
            
        sentences = text.split('. ')
        summary = sentences[0]
        
        for sentence in sentences[1:]:
            # Account for the period and space we'll add
            if len(summary) + len(sentence) + 2 <= max_length:
                summary += '. ' + sentence
            else:
                break
                
        # Ensure final summary respects max length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
                
        return summary
