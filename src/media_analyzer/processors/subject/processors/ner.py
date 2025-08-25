"""Named entity recognition processor for subject identification."""

from typing import Dict, Any
import spacy
from spacy.language import Language
import logging

logger = logging.getLogger(__name__)


from .base import BaseProcessor

class EntityProcessor(BaseProcessor):
    """Named entity recognition processor using spaCy."""

    def __init__(self):
        """Initialize the NER processor with spaCy model."""
        # Load model with reduced pipeline for better performance
        self.nlp = spacy.load("en_core_web_sm", 
                             disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
        # Only keep NER pipeline
        self.nlp.select_pipes(enable=["ner"])
        
        self.min_length = 1  # Minimum words in entity
        self.known_companies = {
            "microsoft", "apple", "google", "meta", "amazon",
            "tesla", "openai", "nvidia", "intel", "ibm"
        }
        self.known_people = {
            "satya nadella", "tim cook", "elon musk", "sam altman",
            "bill gates", "steve jobs", "sundar pichai"
        }

    def process(self, text: str) -> Dict[str, float]:
        """Process text to extract named entities with confidence scores.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            Dict[str, float]: Dictionary mapping entity names to confidence scores
        """
        try:
            if not text:
                logger.warning("Empty text provided for entity extraction")
                return {}
                
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract entities with confidence scores
            entities = {}
            for ent in doc.ents:
                name = ent.text.strip()
                if len(name.split()) >= self.min_length:
                    # Base confidence score
                    confidence = 0.8
                    
                    # Boost known entities
                    name_lower = name.lower()
                    if name_lower in self.known_companies:
                        confidence = 1.0
                    elif name_lower in self.known_people:
                        confidence = 1.0
                    elif ent.label_ in ["ORG", "PERSON", "GPE"]:
                        confidence = 0.9
                    
                    entities[name] = min(1.0, confidence)
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract entities: {str(e)}")
            return {}
