"""
Subject identification models module.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum


class SubjectType(Enum):
    """Types of subjects that can be identified."""
    TOPIC = "topic"         # Abstract topics from LDA
    ENTITY = "entity"       # Named entities
    KEYWORD = "keyword"     # Extracted keywords


@dataclass(frozen=True)
class Category:
    """A subject category."""
    id: str
    name: str

    def __hash__(self):
        """Make Category hashable."""
        return hash((self.id, self.name))


@dataclass
class Context:
    """Context information for subject identification."""
    domain: str
    language: str
    confidence: float


@dataclass(frozen=True)
class Subject:
    """An identified subject."""
    name: str
    subject_type: SubjectType
    confidence: float
    context: Optional[Context] = None

    def __hash__(self):
        """Make Subject hashable."""
        # Context is mutable so we exclude it from the hash
        return hash((self.name, self.subject_type))


@dataclass
class ProcessingMetrics:
    """Metrics from subject identification."""
    processing_time_ms: float
    keyword_count: int
    text_length: int
    error_count: int = 0


@dataclass
class SubjectMetadata:
    """Metadata about identified subjects."""
    categories: Set[Category]
    confidence: float
    processing_time_ms: float
    metrics: Optional[ProcessingMetrics] = None


@dataclass
class SubjectAnalysisResult:
    """Result of subject identification analysis."""
    subjects: Set[Subject] = field(default_factory=set)
    categories: Set[Category] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
