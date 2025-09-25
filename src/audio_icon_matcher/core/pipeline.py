"""Main pipeline for converting audio to icon recommendations."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ..core.exceptions import (
    AudioIconValidationError, 
    AudioIconProcessingError
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
from media_analyzer.models.podcast import AnalysisOptions

logger = logging.getLogger(__name__)


class AudioIconPipeline:
    """Main pipeline for converting audio to icon recommendations."""
    
    def __init__(self):
        """Initialize the pipeline with required processors."""
        self.audio_processor = AudioProcessor()
        self.subject_identifier = SubjectIdentifier()
        self.icon_matcher = IconMatcher()  # Enhanced icon matcher with semantic similarity
        self.result_ranker = ResultRanker()
        
        # Initialize podcast analyzer for streaming content
        self.podcast_analyzer = PodcastAnalyzer()
    
    def _match_subjects_to_icons(
        self, 
        subjects: Dict[str, Any], 
        max_icons: int
    ) -> List[IconMatch]:
        """Match subjects to icons and rank results.
        
        Args:
            subjects: Subject identification results
            max_icons: Maximum number of icons to return
            
        Returns:
            Ranked list of icon matches
        """
        # Step 3: Match subjects to icons
        logger.info("Step 3: Matching subjects to icons...")
        
        icon_matches = self.icon_matcher.find_matching_icons(
            subjects, 
            limit=max_icons * 2  # Get more matches for better ranking
        )
        
        logger.info("Found %d potential icon matches", len(icon_matches))
        
        # Step 4: Rank and filter results
        logger.info("Step 4: Ranking and filtering results...")
        ranked_matches = self.result_ranker.rank_results(
            icon_matches, 
            subjects, 
            limit=max_icons
        )
        
        return ranked_matches
    
    def _filter_by_confidence(
        self, 
        matches: List[IconMatch], 
        confidence_threshold: float
    ) -> List[IconMatch]:
        """Filter matches by confidence threshold.
        
        Args:
            matches: List of icon matches to filter
            confidence_threshold: Minimum confidence required
            
        Returns:
            Filtered list of matches
        """
        return [
            match for match in matches 
            if match.confidence >= confidence_threshold
        ]
    
    def _create_success_result(
        self,
        transcription: str,
        transcription_confidence: float,
        subjects: Dict[str, Any],
        filtered_matches: List[IconMatch],
        processing_time: float,
        metadata: Dict[str, Any]
    ) -> AudioIconResult:
        """Create a successful AudioIconResult.
        
        Args:
            transcription: Transcribed text
            transcription_confidence: Confidence of transcription
            subjects: Identified subjects
            filtered_matches: Final filtered icon matches
            processing_time: Total processing time
            metadata: Additional metadata
            
        Returns:
            AudioIconResult for success case
        """
        return AudioIconResult(
            success=True,
            transcription=transcription,
            transcription_confidence=transcription_confidence,
            subjects=subjects,
            icon_matches=filtered_matches,
            processing_time=processing_time,
            metadata=metadata
        )
    
    def _create_error_result(
        self,
        error_message: str,
        processing_time: float,
        metadata: Dict[str, Any]
    ) -> AudioIconResult:
        """Create an error AudioIconResult.
        
        Args:
            error_message: Error description
            processing_time: Time taken before error
            metadata: Additional metadata
            
        Returns:
            AudioIconResult for error case
        """
        return AudioIconResult(
            success=False,
            error=error_message,
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=processing_time,
            metadata=metadata
        )

    def process(
        self, 
        audio_source: str, 
        max_icons: int = 10,
        confidence_threshold: float = 0.3,
        episode_index: int = 0,
        episode_title: Optional[str] = None,
        max_duration_minutes: int = 30
    ) -> AudioIconResult:
        """Process audio source through the complete pipeline.
        
        Args:
            audio_source: Path to audio file or podcast episode URL
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            episode_index: Episode index from RSS feed (0 = most recent)
            episode_title: Find episode by title (partial match, case-insensitive)
            max_duration_minutes: Maximum audio duration to process in minutes (default: 30)
            
        Returns:
            AudioIconResult with transcription, subjects, and icon matches
            
        Raises:
            AudioIconValidationError: If audio source is invalid
            AudioIconProcessingError: If processing fails
        """
        # Determine if source is a URL or local file
        if self._is_url(audio_source):
            # For URL processing, handle cleanup within the same event loop
            async def process_with_cleanup():
                try:
                    result = await self._process_podcast_url(
                        audio_source, max_icons, confidence_threshold, episode_index, episode_title, max_duration_minutes
                    )
                    return result
                finally:
                    # Clean up in the same event loop context
                    await self.cleanup()
            
            # Check if we're already in an event loop (e.g., in async tests)
            try:
                asyncio.get_running_loop()
                # If we're here, there's already a running loop
                # We cannot use asyncio.run(), so we need to raise an error
                # suggesting to use the async version
                raise AudioIconProcessingError(
                    "Cannot process podcast URL in an async context. "
                    "Use 'await pipeline.process_async()' instead."
                )
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(process_with_cleanup())
        else:
            return self._process_local_file(
                audio_source, max_icons, confidence_threshold, max_duration_minutes
            )
    
    async def process_async(
        self, 
        audio_source: str, 
        max_icons: int = 10,
        confidence_threshold: float = 0.3,
        episode_index: int = 0,
        episode_title: Optional[str] = None,
        max_duration_minutes: int = 30
    ) -> AudioIconResult:
        """Async version of process method for use in async contexts.
        
        Args:
            audio_source: Path to audio file or podcast episode URL
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            episode_index: Episode index from RSS feed (0 = most recent)
            episode_title: Find episode by title (partial match, case-insensitive)
            max_duration_minutes: Maximum audio duration to process in minutes (default: 30)
            
        Returns:
            AudioIconResult with transcription, subjects, and icon matches
            
        Raises:
            AudioIconValidationError: If audio source is invalid
            AudioIconProcessingError: If processing fails
        """
        # Determine if source is a URL or local file
        if self._is_url(audio_source):
            try:
                result = await self._process_podcast_url(
                    audio_source, max_icons, confidence_threshold, episode_index, episode_title, max_duration_minutes
                )
                return result
            finally:
                # Clean up in the same event loop context
                await self.cleanup()
        else:
            return self._process_local_file(
                audio_source, max_icons, confidence_threshold, max_duration_minutes
            )
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        return source.startswith(('http://', 'https://'))
    
    async def _process_podcast_url(
        self, 
        url: str, 
        max_icons: int, 
        confidence_threshold: float,
        episode_index: int = 0,
        episode_title: Optional[str] = None,
        max_duration_minutes: int = 30
    ) -> AudioIconResult:
        """Process podcast episode from URL.
        
        Args:
            url: Podcast episode URL
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            episode_index: Episode index from RSS feed (0 = most recent)
            episode_title: Find episode by title (partial match, case-insensitive)
            
        Returns:
            AudioIconResult with podcast analysis results
        """
        start_time = time.time()
        
        try:
            logger.info("Starting podcast analysis for: %s", url)
            
            # Configure podcast analysis options
            options = AnalysisOptions(
                subject_extraction=True,
                confidence_threshold=0.3,  # Use lower threshold for subject extraction
                max_duration_minutes=max_duration_minutes,  # Use configurable duration limit
                episode_index=episode_index,      # Pass episode selection to options
                episode_title=episode_title       # Pass episode title to options
            )
            
            # Analyze podcast episode (URL will be used with episode selection options)
            podcast_result = await self.podcast_analyzer.analyze_episode(url, options)
            
            if not podcast_result.success:
                raise AudioIconProcessingError(f"Podcast analysis failed: {podcast_result.error_message}")
            
            # Extract transcription and subjects from podcast result
            transcription = podcast_result.transcription.text if podcast_result.transcription else ""
            transcription_confidence = podcast_result.transcription.confidence if podcast_result.transcription else 0.0
            
            # Convert subjects to dict format for icon matching (unified method)
            subjects = self._convert_subjects_to_rich_dict(podcast_result.subjects)
            
            logger.info("Podcast analysis complete. Transcription length: %d", len(transcription))
            logger.info("Found %d subject types from podcast", len(subjects))
            
            # Use common icon matching and ranking logic
            ranked_matches = self._match_subjects_to_icons(subjects, max_icons)
            filtered_matches = self._filter_by_confidence(ranked_matches, confidence_threshold)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Podcast pipeline complete in %.2fs. Returning %d icon matches",
                processing_time, len(filtered_matches)
            )
            
            # Create result with podcast metadata
            metadata = {
                'source_type': 'podcast',
                'source_url': url,
                'episode_title': podcast_result.episode.title if podcast_result.episode else None,
                'show_name': podcast_result.episode.show_name if podcast_result.episode else None,
                'max_icons_requested': max_icons,
                'confidence_threshold': confidence_threshold,
                'total_matches_found': len(ranked_matches),
                'matches_after_filtering': len(filtered_matches),
                'pipeline_version': '1.1'
            }
            
            return self._create_success_result(
                transcription, transcription_confidence, subjects,
                filtered_matches, processing_time, metadata
            )
            
        except (AudioIconValidationError, AudioIconProcessingError) as e:
            logger.error("Specific error in podcast pipeline: %s", e)
            processing_time = time.time() - start_time
            
            # Return error result
            error_metadata = {
                'source_type': 'podcast',
                'source_url': url,
                'error_type': type(e).__name__,
                'pipeline_version': '1.1'
            }
            
            return self._create_error_result(
                f"Podcast pipeline failed: {e}",
                processing_time,
                error_metadata
            )
    
    def _process_local_file(
        self, 
        audio_file: str, 
        max_icons: int, 
        confidence_threshold: float,
        max_duration_minutes: int = 30
    ) -> AudioIconResult:
        """Process local audio file through the complete pipeline.
        
        Args:
            audio_file: Path to audio file to process
            max_icons: Maximum number of icons to return
            confidence_threshold: Minimum confidence for icon matches
            max_duration_minutes: Maximum audio duration to process in minutes (default: 30)
            
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
                
            logger.info("Starting audio-to-icon pipeline for: %s", audio_file)
            
            # Step 1: Extract text from audio
            logger.info("Step 1: Extracting text from audio...")
            
            # Prepare audio processing options with duration limit
            audio_options = {
                'max_duration_minutes': max_duration_minutes
            }
            
            audio_result = self.audio_processor.extract_text(audio_path, audio_options)
            
            if not audio_result or not audio_result.text:
                raise AudioIconProcessingError("Audio processing failed or produced no text")
            
            transcription = audio_result.text
            transcription_confidence = audio_result.confidence
            
            logger.info("Transcription complete (confidence: %.2f)", transcription_confidence)
            logger.debug("Transcribed text: %s...", transcription[:100])
            
            # Step 2: Identify subjects from transcription
            logger.info("Step 2: Identifying subjects...")
            try:
                subject_result = self.subject_identifier.identify_subjects(transcription, episode_title=None)
                
                if not subject_result or not subject_result.subjects:
                    logger.warning("Subject identification produced no results")
                    subjects = {}
                else:
                    # Convert SubjectAnalysisResult to rich dict format (unified method)
                    subjects = self._convert_subjects_to_rich_dict(subject_result)
                
                logger.info("Subject identification complete. Found %d subject types", len(subjects))
                logger.debug("Subjects: %s", subjects)
                
            except (AttributeError, ValueError) as e:
                logger.error("Subject identification failed: %s", e)
                # Continue with empty subjects rather than failing completely
                subjects = {}
            
            # Use common icon matching and ranking logic (no episode title for local files)
            ranked_matches = self._match_subjects_to_icons(subjects, max_icons)
            filtered_matches = self._filter_by_confidence(ranked_matches, confidence_threshold)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Local file pipeline complete in %.2fs. Returning %d icon matches",
                processing_time, len(filtered_matches)
            )
            
            # Create result metadata
            metadata = {
                'source_type': 'local_file',
                'audio_file': str(audio_path),
                'max_icons_requested': max_icons,
                'confidence_threshold': confidence_threshold,
                'total_matches_found': len(ranked_matches),
                'matches_after_filtering': len(filtered_matches),
                'pipeline_version': '1.1'
            }
            
            return self._create_success_result(
                transcription, transcription_confidence, subjects,
                filtered_matches, processing_time, metadata
            )
            
        except (AudioIconValidationError, AudioIconProcessingError):
            # Intentionally re-raise specific validation and processing errors
            # These should be handled by the caller, not converted to generic errors
            raise  # noqa: TRY201
        except (OSError, IOError) as e:
            logger.error("File system error in local file pipeline: %s", e)
            processing_time = time.time() - start_time
            
            # Return error result
            error_metadata = {
                'source_type': 'local_file',
                'audio_file': audio_file,
                'error_type': type(e).__name__,
                'pipeline_version': '1.1'
            }
            
            return self._create_error_result(
                f"Local file pipeline failed: {e}",
                processing_time,
                error_metadata
            )
        except (RuntimeError, TypeError, AttributeError) as e:
            logger.error("Unexpected error in local file pipeline: %s", e)
            processing_time = time.time() - start_time
            
            # Return error result for unexpected errors
            error_metadata = {
                'source_type': 'local_file',
                'audio_file': audio_file,
                'error_type': type(e).__name__,
                'pipeline_version': '1.1'
            }
            
            return self._create_error_result(
                f"Local file pipeline failed: {e}",
                processing_time,
                error_metadata
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
        except (FileNotFoundError, ValueError, OSError, RuntimeError, TypeError) as e:
            logger.error("Audio file validation failed: %s", e)
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.audio_processor.SUPPORTED_FORMATS)
    
    def _convert_subjects_to_rich_dict(self, subjects_source: Union[SubjectAnalysisResult, List]) -> Dict[str, Any]:
        """Convert subjects to rich dict format with confidence and metadata.
        
        This unified method handles both SubjectAnalysisResult (from local files) 
        and List[Subject] (from podcast analysis) to produce consistent rich metadata.
        
        Args:
            subjects_source: SubjectAnalysisResult object or List of Subject objects
            
        Returns:
            Dictionary representation with rich metadata
        """
        subjects_dict = {
            'keywords': [],
            'topics': [],
            'entities': [],
            'categories': []
        }
        
        # Handle different input types
        if isinstance(subjects_source, list):
            # Podcast analysis case: List[Subject]
            subjects_list = subjects_source
            categories_list = []
        else:
            # Local file case: SubjectAnalysisResult
            subjects_list = subjects_source.subjects
            categories_list = subjects_source.categories
        
        # Group subjects by type with rich metadata
        for subject in subjects_list:
            # Clean up the type field to just show the enum value
            subject_type_clean = 'KEYWORD'  # Default
            if hasattr(subject, 'subject_type') and subject.subject_type:
                if hasattr(subject.subject_type, 'value'):
                    subject_type_clean = subject.subject_type.value.upper()
                else:
                    subject_type_clean = str(subject.subject_type).upper()
            
            subject_info = {
                'name': subject.name,
                'confidence': subject.confidence,
                'type': subject_type_clean,
                'context': {}  # Default empty context
            }
            
            # Add context if available
            if hasattr(subject, 'context') and subject.context:
                subject_info['context'] = {
                    'domain': getattr(subject.context, 'domain', None),
                    'language': getattr(subject.context, 'language', 'en')
                }
            
            # Route to appropriate category based on subject type
            subject_type_str = subject_type_clean.lower()
            if 'keyword' in subject_type_str:
                subjects_dict['keywords'].append(subject_info)
            elif 'topic' in subject_type_str:
                subjects_dict['topics'].append(subject_info)
            elif 'entity' in subject_type_str:
                subjects_dict['entities'].append(subject_info)
            else:
                # Default unknown types to keywords
                subjects_dict['keywords'].append(subject_info)
        
        # Add categories with metadata (if available)
        for category in categories_list:
            category_info = {
                'name': str(category.name) if hasattr(category, 'name') else str(category),
                'id': getattr(category, 'id', None)
            }
            subjects_dict['categories'].append(category_info)
        
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
            # Note: We access the internal method as it's the only way to validate URLs
            # This could be improved by adding a public validate_url method to PodcastAnalyzer
            connector = self.podcast_analyzer._get_connector_for_url(url)  # noqa: SLF001
            return connector is not None
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Podcast URL validation failed: %s", e)
            return False
    
    async def cleanup(self):
        """Cleanup resources used by the pipeline."""
        try:
            if hasattr(self.podcast_analyzer, 'cleanup'):
                await self.podcast_analyzer.cleanup()
        except (AttributeError, RuntimeError) as e:
            logger.warning("Error during cleanup: %s", e)

    def __del__(self):
        """Cleanup when pipeline is destroyed."""
        try:
            # Only attempt cleanup if there's an event loop available
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule cleanup as a task
                    asyncio.create_task(self.cleanup())
                else:
                    # If loop is not running, create new loop to run cleanup
                    asyncio.run(self.cleanup())
            except RuntimeError:
                # No event loop available - this is common during interpreter shutdown
                pass
        except (RuntimeError, AttributeError):
            # Ignore cleanup errors during destruction to avoid issues during shutdown
            pass
