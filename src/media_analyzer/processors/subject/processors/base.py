"""Base class for text processors."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProcessor(ABC):
    """Abstract base class for all text processors."""
    
    @abstractmethod
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract information.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary containing:
                - results: List of extracted information
                - metadata: Processing metadata
                
        Raises:
            ProcessingError: If processing fails
        """
        pass
    
    def _validate_input(self, text: str) -> None:
        """
        Validate input text.
        
        Args:
            text: Input text to validate
            
        Raises:
            ValueError: If text is invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Input must be a non-empty string")
            
    def _get_metadata(self) -> Dict[str, Any]:
        """Get basic metadata about the processor."""
        return {
            "processor_type": self.__class__.__name__,
            "version": "1.0.0"
        }
