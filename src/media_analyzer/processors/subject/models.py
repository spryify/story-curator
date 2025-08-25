"""
Subject identification models module.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class SubjectType(Enum):
    TOPIC = "topic"         # Abstract topics from LDA
    ENTITY = "entity"       # Named entities
    KEYWORD = "keyword"     # Extracted keywords


@dataclass
class Category:
    """Category model for grouping related subjects."""
    name: str
    description: str
    parent: Optional["Category"] = None


@dataclass
class Context:
    """Context information for subject identification."""
    domain: str
    language: str
    confidence: float


@dataclass
class Subject:
    """Subject model representing an identified topic or entity."""
    name: str
    subject_type: SubjectType
    confidence: float
    category: Optional[Category] = None
    context: Optional[Context] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubjectAnalysisResult:
    """Results from subject analysis including subjects and metadata."""
    subjects: List[Subject]
    categories: List[Category]
    metadata: Dict[str, Any]
