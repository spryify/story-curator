"""Entity-based subject identification."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import spacy
from spacy.language import Language
from spacy.tokens import Doc

@dataclass
class EntityResult:
    """Result from entity processing."""
    name: str
    confidence: float
    metadata: Dict[str, Any]

class EntityProcessor:
    """Identifies subjects based on named entity recognition."""
    
    def __init__(self, model: str = "en_core_web_sm"):
        """Initialize with spaCy model."""
        try:
            self.nlp = spacy.load(model)
        except OSError:
            # Download if not available
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load(model)
            
        # Add custom components
        self.nlp.add_pipe("tech_entity_ruler", config={
            "patterns": self._get_tech_patterns()
        })
            
    def process(self, text: str, context = None) -> List[EntityResult]:
        """Process text and return entity matches.
        
        Args:
            text: Text to analyze
            context: Optional context info
            
        Returns:
            List of EntityResult with identified entities
        """
        doc = self.nlp(text)
        results = []
        
        # Track seen entities to avoid duplicates
        seen = set()
        
        for ent in doc.ents:
            if ent.text.lower() not in seen and len(ent.text) > 1:
                # Calculate confidence based on entity type and label
                confidence = self._calculate_confidence(ent)
                
                # Adjust confidence based on context if available
                if context and hasattr(context, 'domain'):
                    confidence = self._adjust_confidence_for_domain(
                        confidence, ent, context.domain
                    )
                
                results.append(EntityResult(
                    name=ent.text,
                    confidence=confidence,
                    metadata={
                        "type": "entity",
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    }
                ))
                seen.add(ent.text.lower())
                
        return results
    
    def _calculate_confidence(self, ent: Doc) -> float:
        """Calculate confidence score for an entity."""
        # Base confidence by entity type
        base_confidence = {
            "PRODUCT": 0.9,
            "ORG": 0.85,
            "TECH": 0.95,
            "GPE": 0.8,
            "PERSON": 0.75,
            "WORK_OF_ART": 0.7
        }.get(ent.label_, 0.6)
        
        # Adjust for entity length (longer entities tend to be more specific)
        length_factor = min(len(ent.text.split()) / 5, 1.0)
        
        return min(base_confidence * (1 + length_factor * 0.2), 1.0)
    
    def _adjust_confidence_for_domain(self, confidence: float, ent: Doc, domain: str) -> float:
        """Adjust confidence based on domain context."""
        if domain == "technology":
            if ent.label_ == "TECH":
                confidence *= 1.2
            elif ent.label_ == "PRODUCT":
                confidence *= 1.1
        elif domain == "biotechnology":
            if ent.label_ == "SCIENCE":
                confidence *= 1.2
                
        return min(confidence, 1.0)
    
    def _get_tech_patterns(self) -> List[Dict]:
        """Get patterns for tech entity ruler."""
        return [
            {"label": "TECH", "pattern": [{"LOWER": "artificial"}, {"LOWER": "intelligence"}]},
            {"label": "TECH", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
            {"label": "TECH", "pattern": [{"LOWER": "deep"}, {"LOWER": "learning"}]},
            {"label": "TECH", "pattern": [{"LOWER": "neural"}, {"LOWER": "networks"}]},
            {"label": "TECH", "pattern": [{"LOWER": "computer"}, {"LOWER": "vision"}]},
            {"label": "TECH", "pattern": [{"LOWER": "natural"}, {"LOWER": "language"}, {"LOWER": "processing"}]},
            {"label": "TECH", "pattern": [{"LOWER": "nlp"}]},
            {"label": "TECH", "pattern": [{"LOWER": "ai"}]},
            {"label": "TECH", "pattern": [{"LOWER": "ml"}]}
        ]
