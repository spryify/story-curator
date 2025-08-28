"""Main pipeline for converting audio to icon recommendations."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.exceptions import (
    AudioIconValidationError, 
    AudioIconProcessingError,
    SubjectIdentificationError
)
from ..models.results import AudioIconResult, IconMatch
from ..processors.icon_matcher import IconMatcher
from ..processors.result_ranker import ResultRanker

# Import existing components
from media_analyzer.processors.audio.audio_processor import AudioProcessor
from media_analyzer.processors.subject.subject_identifier import SubjectIdentifier
from media_analyzer.models.subject.identification import SubjectAnalysisResult

logger = logging.getLogger(__name__)


class AudioIconPipeline:
    """Main pipeline for converting audio to icon recommendations."""
    
    def __init__(self):
        """Initialize the pipeline with required processors."""
        self.audio_processor = AudioProcessor()
        self.subject_identifier = SubjectIdentifier()
        self.icon_matcher = IconMatcher()
        self.result_ranker = ResultRanker()
    
    def process(
        self, 
        audio_file: str, 
        max_icons: int = 10,
        confidence_threshold: float = 0.3
    ) -> AudioIconResult:
        """Process audio file through the complete pipeline.
        
        Args:
            audio_file: Path to audio file to process
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            
        Returns:
            AudioIconResult with transcription, subjects, and icon matches
            
        Raises:
            AudioIconValidationError: If audio file is invalid
            AudioIconProcessingError: If processing fails
        """
        start_time = time.time()
        
        try:
            # Validate input file
            audio_path = Path(audio_file)
            if not audio_path.exists():
                raise AudioIconValidationError(f"Audio file not found: {audio_file}")
                
            logger.info(f"Starting audio-to-icon pipeline for: {audio_file}")
            
            # Step 1: Extract text from audio
            logger.info("Step 1: Extracting text from audio...")
            audio_result = self.audio_processor.extract_text(audio_path)
            
            if not audio_result or not audio_result.text:
                raise AudioIconProcessingError("Audio processing failed or produced no text")
            
            transcription = audio_result.text
            transcription_confidence = audio_result.confidence
            
            logger.info(f"Transcription complete (confidence: {transcription_confidence:.2f})")
            logger.debug(f"Transcribed text: {transcription[:100]}...")
            
            # Step 2: Identify subjects from transcription
            logger.info("Step 2: Identifying subjects...")
            try:
                subject_result = self.subject_identifier.identify_subjects(transcription)
                
                if not subject_result:
                    logger.warning("Subject identification produced no results")
                    subjects = {}
                else:
                    # Convert SubjectAnalysisResult to dict format for compatibility
                    subjects = self._convert_subject_result_to_dict(subject_result)
                
                logger.info(f"Subject identification complete. Found {len(subjects)} subject types")
                logger.debug(f"Subjects: {subjects}")
                
            except Exception as e:
                logger.error(f"Subject identification failed: {e}")
                # Continue with empty subjects rather than failing completely
                subjects = {}
            
            # Step 3: Match subjects to icons
            logger.info("Step 3: Matching subjects to icons...")
            icon_matches = self.icon_matcher.find_matching_icons(
                subjects, 
                limit=max_icons * 2  # Get more matches for better ranking
            )
            
            logger.info(f"Found {len(icon_matches)} potential icon matches")
            
            # Step 4: Rank and filter results
            logger.info("Step 4: Ranking and filtering results...")
            ranked_matches = self.result_ranker.rank_results(
                icon_matches, 
                subjects, 
                limit=max_icons
            )
            
            # Apply confidence threshold
            filtered_matches = [
                match for match in ranked_matches 
                if match.confidence >= confidence_threshold
            ]
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Pipeline complete in {processing_time:.2f}s. "
                f"Returning {len(filtered_matches)} icon matches"
            )
            
            # Create result
            result = AudioIconResult(
                success=True,
                transcription=transcription,
                transcription_confidence=transcription_confidence,
                subjects=subjects,
                icon_matches=filtered_matches,
                processing_time=processing_time,
                metadata={
                    'audio_file': str(audio_path),
                    'max_icons_requested': max_icons,
                    'confidence_threshold': confidence_threshold,
                    'total_matches_found': len(icon_matches),
                    'matches_after_ranking': len(ranked_matches),
                    'matches_after_filtering': len(filtered_matches),
                    'pipeline_version': '1.0'
                }
            )
            
            return result
            
        except (AudioIconValidationError, AudioIconProcessingError):
            # Re-raise validation and audio processing errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in audio-to-icon pipeline: {e}")
            processing_time = time.time() - start_time
            
            # Return error result
            return AudioIconResult(
                success=False,
                error=f"Pipeline failed: {e}",
                transcription="",
                transcription_confidence=0.0,
                subjects={},
                icon_matches=[],
                processing_time=processing_time,
                metadata={
                    'audio_file': audio_file,
                    'error_type': type(e).__name__,
                    'pipeline_version': '1.0'
                }
            )
    
    def validate_audio_file(self, audio_file: str) -> bool:
        """Validate that the audio file can be processed.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            path = self.audio_processor.validate_file(audio_file)
            return path is not None and path.exists()
        except Exception as e:
            logger.error(f"Audio file validation failed: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.audio_processor.SUPPORTED_FORMATS)
    
    def _convert_subject_result_to_dict(self, subject_result: SubjectAnalysisResult) -> Dict[str, Any]:
        """Convert SubjectAnalysisResult to dict format for compatibility.
        
        Args:
            subject_result: SubjectAnalysisResult object
            
        Returns:
            Dictionary representation of subjects
        """
        subjects_dict = {
            'keywords': [],
            'topics': [],
            'entities': [],
            'categories': []
        }
        
        # Group subjects by type
        for subject in subject_result.subjects:
            subject_info = {
                'name': subject.name,
                'confidence': subject.confidence
            }
            
            if hasattr(subject, 'subject_type') and subject.subject_type:
                subject_type = str(subject.subject_type).lower()
                if subject_type == 'keyword':
                    subjects_dict['keywords'].append(subject_info)
                elif subject_type == 'topic':
                    subjects_dict['topics'].append(subject_info)
                elif subject_type == 'entity':
                    subjects_dict['entities'].append(subject_info)
                else:
                    subjects_dict['keywords'].append(subject_info)  # Default to keywords
            else:
                subjects_dict['keywords'].append(subject_info)  # Default to keywords
        
        # Add categories
        for category in subject_result.categories:
            subjects_dict['categories'].append(str(category.name) if hasattr(category, 'name') else str(category))
        
        return subjects_dict
