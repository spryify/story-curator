"""Keyword-based subject identification."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re

@dataclass
class KeywordResult:
    """Result from keyword processing."""
    name: str
    confidence: float
    metadata: Dict[str, Any]

class KeywordProcessor:
    """Identifies subjects based on keyword matching."""
    
    TECH_KEYWORDS = {
        "artificial intelligence": 0.95,
        "machine learning": 0.95,
        "deep learning": 0.95,
        "natural language processing": 0.95,
        "computer vision": 0.95,
        "neural networks": 0.9,
        "data science": 0.9,
        "big data": 0.9,
        "cloud computing": 0.9,
        "internet of things": 0.9,
        "blockchain": 0.9,
        "cybersecurity": 0.9,
        "virtual reality": 0.9,
        "augmented reality": 0.9,
        "robotics": 0.9,
        "automation": 0.85,
        "machine vision": 0.85,
        "edge computing": 0.85,
        "quantum computing": 0.95,
        "5g": 0.85,
        "data analytics": 0.85,
        "devops": 0.85,
        "microservices": 0.85,
        "containerization": 0.85,
        "api": 0.8,
        "web development": 0.8,
        "mobile development": 0.8,
        "database": 0.8,
        "software engineering": 0.8,
        "testing": 0.75,
        "agile": 0.75,
        "scrum": 0.75
    }

    BIO_KEYWORDS = {
        "crispr": 0.95,
        "genome": 0.95,
        "dna sequencing": 0.95,
        "gene editing": 0.95,
        "biotechnology": 0.95,
        "molecular biology": 0.95,
        "cell culture": 0.9,
        "protein synthesis": 0.9,
        "genetics": 0.9,
        "enzymes": 0.85
    }
    
    def __init__(self, custom_keywords: Optional[Dict[str, float]] = None):
        """Initialize with optional custom keywords."""
        self.keywords = {**self.TECH_KEYWORDS, **self.BIO_KEYWORDS}
        if custom_keywords:
            self.keywords.update(custom_keywords)
            
    def process(self, text: str, context = None) -> List[KeywordResult]:
        """Process text and return keyword matches.
        
        Args:
            text: Text to analyze
            context: Optional context info (unused in basic implementation)
            
        Returns:
            List of KeywordResult with matched keywords
        """
        results = []
        text = text.lower()
        
        # Use context domain if available
        domain_keywords = {}
        if context and hasattr(context, 'domain'):
            if context.domain == 'technology':
                domain_keywords = self.TECH_KEYWORDS
            elif context.domain == 'biotechnology':
                domain_keywords = self.BIO_KEYWORDS
        
        # If no specific domain, use all keywords
        keywords_to_check = domain_keywords or self.keywords
        
        for keyword, base_confidence in keywords_to_check.items():
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.finditer(pattern, text)
            
            for match in matches:
                # Adjust confidence based on match position and frequency
                position_factor = 1.0 - (match.start() / len(text) * 0.2)  # Earlier mentions weighted higher
                confidence = base_confidence * position_factor
                
                results.append(KeywordResult(
                    name=keyword,
                    confidence=min(confidence, 1.0),
                    metadata={
                        "position": match.start(),
                        "type": "keyword"
                    }
                ))
                
        return results
