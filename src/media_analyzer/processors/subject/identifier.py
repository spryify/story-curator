"""
Core subject identification module.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any

from .models import Subject, Category, Context, SubjectAnalysisResult, SubjectType
from .processors.lda import TopicProcessor
from .processors.ner import EntityProcessor
from .processors.keywords import KeywordProcessor

logger = logging.getLogger(__name__)


class SubjectIdentifier:
    """
    Main subject identification class implementing the hybrid approach from ADR-008.
    """

    def __init__(self):
        """Initialize processors and load models."""
        self.topic_processor = TopicProcessor()
        self.entity_processor = EntityProcessor()
        self.keyword_processor = KeywordProcessor()

    def identify_subjects(self, text: str, context: Optional[Context] = None) -> SubjectAnalysisResult:
        """
        Identify subjects in the given text using multiple processing methods.
        
        Args:
            text: Input text to analyze
            context: Optional context information to guide analysis
            
        Returns:
            SubjectAnalysisResult containing identified subjects and metadata
            
        Raises:
            ValueError: If text is empty or invalid
            ProcessingError: If subject identification fails
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        try:
            # Process text using multiple methods in parallel
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self.topic_processor.process, text): SubjectType.TOPIC,
                    executor.submit(self.entity_processor.process, text): SubjectType.ENTITY,
                    executor.submit(self.keyword_processor.process, text): SubjectType.KEYWORD
                }

                subjects: List[Subject] = []
                metadata: Dict[str, Any] = {}

                # Collect results as they complete
                for future in as_completed(futures):
                    subject_type = futures[future]
                    try:
                        result = future.result()
                        subjects.extend(self._convert_to_subjects(result, subject_type))
                        metadata[f"{subject_type.value}_metadata"] = result.get("metadata", {})
                    except Exception as e:
                        logger.error(f"Error processing {subject_type}: {str(e)}")
                        metadata[f"{subject_type.value}_error"] = str(e)

            # Score and rank subjects
            scored_subjects = self._score_subjects(subjects, context)
            
            # Group into categories
            categories = self._categorize_subjects(scored_subjects)
            
            return SubjectAnalysisResult(
                subjects=scored_subjects,
                categories=categories,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Subject identification failed: {str(e)}")
            raise ProcessingError(f"Failed to identify subjects: {str(e)}") from e

    def _convert_to_subjects(self, 
                           processor_results: Dict[str, Any], 
                           subject_type: SubjectType) -> List[Subject]:
        """Convert processor-specific results to Subject objects."""
        subjects = []
        for result in processor_results.get("results", []):
            subject = Subject(
                name=result["name"],
                subject_type=subject_type,
                confidence=result.get("score", 0.0),
                metadata=result.get("metadata", {})
            )
            subjects.append(subject)
        return subjects

    def _score_subjects(self, 
                       subjects: List[Subject], 
                       context: Optional[Context]) -> List[Subject]:
        """Score and rank subjects based on multiple factors."""
        # Add context-based scoring here
        if context:
            for subject in subjects:
                subject.context = context
                if context.domain in subject.name.lower():
                    subject.confidence *= 1.2  # Boost domain-relevant subjects
        
        # Sort by confidence
        return sorted(subjects, key=lambda x: x.confidence, reverse=True)

    def _categorize_subjects(self, subjects: List[Subject]) -> List[Category]:
        """Group subjects into categories."""
        # Implement hierarchical clustering or category assignment
        # For now, return basic categories
        categories = {subject.subject_type.value for subject in subjects}
        return [Category(name=cat, description=f"Subjects of type {cat}") 
                for cat in categories]


class ProcessingError(Exception):
    """Raised when subject processing fails."""
    pass
