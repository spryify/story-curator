"""Main pipeline for converting audio to icon recommendations."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

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
from media_analyzer.processors.subject.identifier import SubjectIdentifier
from media_analyzer.models.subject.identification import SubjectAnalysisResult

# Import podcast components
from media_analyzer.processors.podcast.analyzer import PodcastAnalyzer
from media_analyzer.models.podcast import AnalysisOptions, StreamingAnalysisResult

logger = logging.getLogger(__name__)


class AudioIconPipeline:
    """Main pipeline for converting audio to icon recommendations."""
    
    def __init__(self):
        """Initialize the pipeline with required processors."""
        self.audio_processor = AudioProcessor()
        self.subject_identifier = SubjectIdentifier()
        self.icon_matcher = IconMatcher()
        self.result_ranker = ResultRanker()
        
        # Initialize podcast analyzer for streaming content
        self.podcast_analyzer = PodcastAnalyzer()
    
    def process(
        self, 
        audio_source: str, 
        max_icons: int = 10,
        confidence_threshold: float = 0.3
    ) -> AudioIconResult:
        """Process audio source through the complete pipeline.
        
        Args:
            audio_source: Path to audio file or podcast episode URL
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            
        Returns:
            AudioIconResult with transcription, subjects, and icon matches
            
        Raises:
            AudioIconValidationError: If audio source is invalid
            AudioIconProcessingError: If processing fails
        """
        # Determine if source is a URL or local file
        if self._is_url(audio_source):
            return asyncio.run(self._process_podcast_url(
                audio_source, max_icons, confidence_threshold
            ))
        else:
            return self._process_local_file(
                audio_source, max_icons, confidence_threshold
            )
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        return source.startswith(('http://', 'https://'))
    
    async def _process_podcast_url(
        self, 
        url: str, 
        max_icons: int, 
        confidence_threshold: float
    ) -> AudioIconResult:
        """Process podcast episode from URL.
        
        Args:
            url: Podcast episode URL
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            
        Returns:
            AudioIconResult with podcast analysis results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting podcast analysis for: {url}")
            
            # Configure podcast analysis options
            options = AnalysisOptions(
                subject_extraction=True,
                confidence_threshold=0.3,  # Use lower threshold for subject extraction
                max_duration_minutes=4     # Limit to 4 minutes for faster processing
            )
            
            # Analyze podcast episode
            podcast_result = await self.podcast_analyzer.analyze_episode(url, options)
            
            if not podcast_result.success:
                raise AudioIconProcessingError(f"Podcast analysis failed: {podcast_result.error_message}")
            
            # Extract transcription and subjects from podcast result
            transcription = podcast_result.transcription.text if podcast_result.transcription else ""
            transcription_confidence = podcast_result.transcription.confidence if podcast_result.transcription else 0.0
            
            # Convert subjects to dict format for icon matching
            subjects = self._convert_podcast_subjects_to_dict(podcast_result.subjects)
            
            logger.info(f"Podcast analysis complete. Transcription length: {len(transcription)}")
            logger.info(f"Found {len(subjects)} subject types from podcast")
            
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
                f"Podcast pipeline complete in {processing_time:.2f}s. "
                f"Returning {len(filtered_matches)} icon matches"
            )
            
            # Create result with podcast metadata
            result = AudioIconResult(
                success=True,
                transcription=transcription,
                transcription_confidence=transcription_confidence,
                subjects=subjects,
                icon_matches=filtered_matches,
                processing_time=processing_time,
                metadata={
                    'source_type': 'podcast',
                    'source_url': url,
                    'episode_title': podcast_result.episode.title if podcast_result.episode else None,
                    'show_name': podcast_result.episode.show_name if podcast_result.episode else None,
                    'max_icons_requested': max_icons,
                    'confidence_threshold': confidence_threshold,
                    'total_matches_found': len(icon_matches),
                    'matches_after_ranking': len(ranked_matches),
                    'matches_after_filtering': len(filtered_matches),
                    'pipeline_version': '1.1'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in podcast pipeline: {e}")
            processing_time = time.time() - start_time
            
            # Return error result
            return AudioIconResult(
                success=False,
                error=f"Podcast pipeline failed: {e}",
                transcription="",
                transcription_confidence=0.0,
                subjects={},
                icon_matches=[],
                processing_time=processing_time,
                metadata={
                    'source_type': 'podcast',
                    'source_url': url,
                    'error_type': type(e).__name__,
                    'pipeline_version': '1.1'
                }
            )
    
    def _process_local_file(
        self, 
        audio_file: str, 
        max_icons: int, 
        confidence_threshold: float
    ) -> AudioIconResult:
        """Process local audio file through the complete pipeline.
        
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
                
                if not subject_result or not subject_result.subjects:
                    logger.warning("Subject identification produced no results")
                    subjects = {}
                else:
                    # Convert SubjectAnalysisResult to rich dict format (same as podcast processing)
                    subjects = self._convert_subject_result_to_rich_dict(subject_result)
                
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
                f"Local file pipeline complete in {processing_time:.2f}s. "
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
                    'source_type': 'local_file',
                    'audio_file': str(audio_path),
                    'max_icons_requested': max_icons,
                    'confidence_threshold': confidence_threshold,
                    'total_matches_found': len(icon_matches),
                    'matches_after_ranking': len(ranked_matches),
                    'matches_after_filtering': len(filtered_matches),
                    'pipeline_version': '1.1'
                }
            )
            
            return result
            
        except (AudioIconValidationError, AudioIconProcessingError):
            # Re-raise validation and audio processing errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in local file pipeline: {e}")
            processing_time = time.time() - start_time
            
            # Return error result
            return AudioIconResult(
                success=False,
                error=f"Local file pipeline failed: {e}",
                transcription="",
                transcription_confidence=0.0,
                subjects={},
                icon_matches=[],
                processing_time=processing_time,
                metadata={
                    'source_type': 'local_file',
                    'audio_file': audio_file,
                    'error_type': type(e).__name__,
                    'pipeline_version': '1.1'
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
    
    def _convert_subject_result_to_rich_dict(self, subject_result: SubjectAnalysisResult) -> Dict[str, Any]:
        """Convert SubjectAnalysisResult to rich dict format with confidence and metadata.
        
        This provides the same rich format as podcast processing, with confidence scores
        and type information for better icon matching.
        
        Args:
            subject_result: SubjectAnalysisResult object
            
        Returns:
            Dictionary representation with rich metadata
        """
        subjects_dict = {
            'keywords': [],
            'topics': [],
            'entities': [],
            'categories': []
        }
        
        # Group subjects by type with rich metadata
        for subject in subject_result.subjects:
            # Clean up the type field to just show the enum value
            subject_type_clean = subject.subject_type.value if hasattr(subject, 'subject_type') and subject.subject_type else 'keyword'
            
            subject_info = {
                'name': subject.name,
                'confidence': subject.confidence,
                'type': subject_type_clean.upper()
            }
            
            # Add context if available
            if hasattr(subject, 'context') and subject.context:
                subject_info['context'] = {
                    'domain': getattr(subject.context, 'domain', None),
                    'language': getattr(subject.context, 'language', 'en')
                }
            
            # Route to appropriate category based on subject type
            if hasattr(subject, 'subject_type') and subject.subject_type:
                subject_type_str = str(subject.subject_type).lower()
                
                # Handle enum values that may include the class name
                if 'keyword' in subject_type_str:
                    subjects_dict['keywords'].append(subject_info)
                elif 'topic' in subject_type_str:
                    subjects_dict['topics'].append(subject_info)
                elif 'entity' in subject_type_str:
                    subjects_dict['entities'].append(subject_info)
                else:
                    # Default unknown types to keywords
                    subjects_dict['keywords'].append(subject_info)
            else:
                # Default to keywords if no type specified
                subjects_dict['keywords'].append(subject_info)
        
        # Add categories with metadata
        for category in subject_result.categories:
            category_info = {
                'name': str(category.name) if hasattr(category, 'name') else str(category),
                'id': getattr(category, 'id', None)
            }
            subjects_dict['categories'].append(category_info)
        
        return subjects_dict
    
    def _convert_podcast_subjects_to_dict(self, subjects: List) -> Dict[str, Any]:
        """Convert podcast subjects list to dict format for compatibility.
        
        Args:
            subjects: List of Subject objects from podcast analysis
            
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
        for subject in subjects:
            subject_info = {
                'name': subject.name,
                'confidence': subject.confidence
            }
            
            if hasattr(subject, 'subject_type') and subject.subject_type:
                # Handle enum values properly
                if hasattr(subject.subject_type, 'value'):
                    subject_type = subject.subject_type.value.lower()
                else:
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
        
        return subjects_dict

    def validate_podcast_url(self, url: str) -> bool:
        """Validate that the podcast URL can be processed.
        
        Args:
            url: Podcast episode URL
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not self._is_url(url):
            return False
            
        try:
            # Use the podcast analyzer to validate the URL
            connector = self.podcast_analyzer._get_connector_for_url(url)
            return connector is not None
        except Exception as e:
            logger.error(f"Podcast URL validation failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources used by the pipeline."""
        try:
            if hasattr(self.podcast_analyzer, 'cleanup'):
                await self.podcast_analyzer.cleanup()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup when pipeline is destroyed."""
        try:
            # Run cleanup in event loop if available
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.cleanup())
            else:
                asyncio.run(self.cleanup())
        except Exception:
            # Ignore cleanup errors during destruction
            pass
