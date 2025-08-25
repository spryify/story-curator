"""Text processing module for summarization and analysis."""

from typing import Dict, Optional
from media_analyzer.core.exceptions import SummarizationError


class TextProcessor:
    """Handles text processing operations like summarization."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""
            
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Basic normalization
        text = text.strip()
        
        return text

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Summarize text to specified maximum length.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in characters
            
        Returns:
            Summarized text
            
        Raises:
            TypeError: If text is not a string
            ValueError: If max_length is not positive
        """
        if text is None:
            raise TypeError("text must be a string")
            
        if not isinstance(text, str):
            raise TypeError("text must be a string")
            
        # Handle max_length validation
        if max_length is not None:
            if not isinstance(max_length, int):
                raise TypeError("max_length must be an integer")
            if max_length <= 0:
                raise ValueError("max_length must be positive")
                
        # Handle empty text
        if not text.strip():
            return ""

        # Clean input
        text = text.strip()
        if not text:
            return ""

        words = text.split()
        if not max_length:
            max_length = 500 if len(words) > 50 else len(text)

        # Take first N words that fit within max_length
        summary = []
        current_length = 0
        ellipsis_length = 3  # Length of "..."
        
        for word in words:
            word_length = len(word) + (1 if summary else 0)
            # Save space for ellipsis if we will need it
            available_length = max_length - (ellipsis_length if len(words) > len(summary) + 1 else 0)
            
            if current_length + word_length <= available_length:
                summary.append(word)
                current_length += word_length
            else:
                break

        result = " ".join(summary)
        return result + ("..." if len(words) > len(summary) else "")
