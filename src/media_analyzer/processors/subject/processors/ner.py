"""
Named Entity Recognition processor using spaCy.
"""
from typing import Dict, Any
import spacy
from spacy.language import Language


class EntityProcessor:
    """Implements named entity recognition using spaCy."""
    
    def __init__(self, model: str = "en_core_web_sm"):
        """Initialize the entity processor."""
        self.nlp: Language = spacy.load(model)
        
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract named entities.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing:
                - results: List of extracted entities with scores
                - metadata: Processing metadata
        """
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract entities
        results = []
        for ent in doc.ents:
            results.append({
                "name": ent.text,
                "score": 1.0,  # spaCy doesn't provide confidence scores
                "metadata": {
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
            })
            
        return {
            "results": results,
            "metadata": {
                "model": self.nlp.meta["name"],
                "version": self.nlp.meta["version"]
            }
        }
