"""Named entity recognition processor for subject identification."""

from typing import Dict, Any, Set, Tuple
import spacy
from spacy.language import Language
import logging

logger = logging.getLogger(__name__)


from .base import BaseExtractor

class EntityExtractor(BaseExtractor):
    """Named entity recognition extractor using spaCy."""

    def __init__(self):
        """Initialize the NER processor with spaCy model."""
        # Load model with reduced pipeline for better performance
        self.nlp = spacy.load("en_core_web_sm", 
                             disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
        # Only keep NER pipeline
        self.nlp.select_pipes(enable=["ner"])
        
        self.min_length = 1  # Minimum words in entity
        
        # Define scoring for different entity types
        self.entity_scores = {
            'ORG': 0.9,    # Organizations
            'PERSON': 0.9,  # People
            'PRODUCT': 0.8, # Products
            'GPE': 0.8,    # Countries, cities, etc.
            'WORK_OF_ART': 0.7,  # Titles of books, songs, etc.
            'EVENT': 0.7,   # Named events
            'LAW': 0.7,     # Named laws and documents
            'FAC': 0.6,     # Facilities
            'LOC': 0.6,     # Non-GPE locations
            'NORP': 0.6,    # Nationalities, religious/political groups
        }

    def process(self, text: str) -> Dict[str, Any]:
        """Process text to extract entities."""
        self._validate_input(text)
        
        # Get raw entities with scores
        raw_entities = self._extract_entities(text)
        
        # Convert to dictionary format
        results = {k: s for k, s in raw_entities}
        
        return {
            "results": results,
            "metadata": self._get_metadata()
        }
    
    def _extract_entities(self, text: str) -> Set[Tuple[str, float]]:
        """Extract named entities from text with scores."""
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract entities with scores
        entities = set()
        seen_texts = set()
        
        for ent in doc.ents:
            if ent.text not in seen_texts:
                # Score based on entity type and length
                base_score = self.entity_scores.get(ent.label_, 0.5)
                length_bonus = min(0.2, len(ent.text.split()) * 0.1)  # Bonus for multi-word entities
                score = min(1.0, base_score + length_bonus)
                
                entities.add((ent.text, score))
                seen_texts.add(ent.text)
                
        return entities
