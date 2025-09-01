"""Main podcast episode analyzer."""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, List

from media_analyzer.models.podcast import PodcastEpisode, StreamingAnalysisResult, AnalysisOptions
from media_analyzer.processors.podcast.platform_connector import PodcastPlatformConnector
from media_analyzer.processors.podcast.rss_connector import RSSFeedConnector
from media_analyzer.processors.podcast.transcription_service import WhisperStreamingService
from media_analyzer.processors.subject.identifier import SubjectIdentifier
from media_analyzer.core.exceptions import ValidationError, AudioProcessingError

logger = logging.getLogger(__name__)


class PodcastAnalyzer:
    """Main orchestrator for podcast episode analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize podcast analyzer.
        
        Args:
            config: Optional configuration dictionary with service settings
        """
        self.config = config or {}
        
        # Initialize connectors
        self.connectors: Dict[str, PodcastPlatformConnector] = {
            'rss': RSSFeedConnector(self.config.get('rss', {}))
        }
        
        # Initialize transcription service
        transcription_config = self.config.get('transcription', {})
        self.transcription_service = WhisperStreamingService(transcription_config)
        
        # Initialize subject identifier
        subject_config = self.config.get('subject_identification', {})
        max_workers = subject_config.get('max_workers', 3)
        timeout_ms = subject_config.get('timeout_ms', 800)
        self.subject_identifier = SubjectIdentifier(max_workers=max_workers, timeout_ms=timeout_ms)
    
    async def analyze_episode(self, url: str, options: Optional[AnalysisOptions] = None) -> StreamingAnalysisResult:
        """Analyze a single podcast episode from URL.
        
        Args:
            url: Podcast episode URL
            options: Analysis configuration options
            
        Returns:
            StreamingAnalysisResult with analysis data
        """
        if options is None:
            options = AnalysisOptions()
        
        try:
            start_time = time.time()
            logger.info(f"Starting podcast analysis for: {url}")
            
            # Find appropriate connector
            connector = self._get_connector_for_url(url)
            if not connector:
                raise ValidationError(f"No connector found for URL: {url}")
            
            # Get episode metadata
            logger.info(f"Extracting metadata with {connector.platform_name} connector...")
            episode = await connector.get_episode_metadata(url, options)
            
            # Log episode duration and processing limit
            max_duration_seconds = options.max_duration_minutes * 60
            if episode.duration_seconds and episode.duration_seconds > max_duration_seconds:
                logger.info(f"Episode duration ({episode.duration_seconds//60}min) exceeds processing limit ({options.max_duration_minutes}min), will process first {options.max_duration_minutes}min only")
            
            # Get audio stream URL
            logger.info("Getting audio stream URL...")
            audio_url = await connector.get_audio_stream_url(episode)
            
            # Transcribe audio
            logger.info("Starting transcription...")
            transcription_options = {
                'language': options.language,
                'segment_length': options.segment_length_seconds,
                'max_duration_seconds': options.max_duration_minutes * 60  # Limit transcription duration
            }
            transcription = await self.transcription_service.transcribe_stream(audio_url, transcription_options)
            
            # Extract subjects if requested
            subjects = []
            if options.subject_extraction and transcription.text:
                logger.info("Extracting subjects...")
                try:
                    subject_result = self.subject_identifier.identify_subjects(transcription.text)
                    # Filter subjects by confidence threshold
                    subjects = [
                        subject for subject in subject_result.subjects 
                        if subject.confidence >= options.confidence_threshold
                    ]
                    logger.info(f"Extracted {len(subjects)} subjects above confidence threshold {options.confidence_threshold}")
                except Exception as e:
                    logger.warning(f"Subject extraction failed: {e}")
                    subjects = []
            
            # TODO: Icon matching would be integrated here once that component is available
            matched_icons = []
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Prepare processing metadata
            processing_metadata = {
                'connector_used': connector.platform_name,
                'transcription_service': 'whisper',
                'subject_extraction_enabled': options.subject_extraction,
                'icon_matching_enabled': options.icon_matching,
                'processing_options': options.__dict__.copy(),
                'processing_time': processing_time
            }
            
            result = StreamingAnalysisResult(
                episode=episode,
                transcription=transcription,
                subjects=subjects,
                matched_icons=matched_icons,
                processing_metadata=processing_metadata,
                success=True
            )
            
            logger.info(f"Successfully analyzed episode: {episode.title}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze episode {url}: {str(e)}")
            
            # Return failed result with error info
            return StreamingAnalysisResult(
                episode=PodcastEpisode(
                    platform="unknown",
                    episode_id="error",
                    url=url,
                    title="Analysis Failed",
                    description=f"Error: {str(e)}",
                    duration_seconds=0,
                    publication_date=None,  # type: ignore[arg-type]
                    show_name="Error"
                ),
                transcription=None,  # type: ignore[arg-type]
                subjects=[],
                matched_icons=[],
                processing_metadata={'error': str(e)},
                success=False,
                error_message=str(e)
            )
    
    async def analyze_playlist(self, playlist_url: str, options: Optional[AnalysisOptions] = None) -> List[StreamingAnalysisResult]:
        """Analyze multiple episodes from a playlist.
        
        Args:
            playlist_url: URL to podcast playlist or RSS feed
            options: Analysis configuration options
            
        Returns:
            List of StreamingAnalysisResult for each episode
            
        Note:
            Currently only RSS feeds support multiple episodes.
            Individual episode analysis is recommended for better control.
        """
        if options is None:
            options = AnalysisOptions()
        
        # For now, RSS feeds are treated as single episodes (most recent)
        # This could be extended to process multiple episodes from the feed
        logger.info(f"Analyzing playlist/feed: {playlist_url}")
        
        try:
            result = await self.analyze_episode(playlist_url, options)
            return [result]
        except Exception as e:
            logger.error(f"Failed to analyze playlist {playlist_url}: {str(e)}")
            return []
    
    async def get_episode_metadata(self, url: str) -> PodcastEpisode:
        """Extract metadata without full analysis.
        
        Args:
            url: Podcast episode URL
            
        Returns:
            PodcastEpisode with metadata only
        """
        connector = self._get_connector_for_url(url)
        if not connector:
            raise ValidationError(f"No connector found for URL: {url}")
        
        return await connector.get_episode_metadata(url)
    
    def _get_connector_for_url(self, url: str) -> Optional[PodcastPlatformConnector]:
        """Find the appropriate connector for a given URL.
        
        Args:
            url: URL to find connector for
            
        Returns:
            PodcastPlatformConnector that can handle the URL, or None
        """
        for connector in self.connectors.values():
            try:
                if connector.validate_url(url):
                    return connector
            except Exception as e:
                logger.debug(f"Connector {connector.platform_name} validation failed: {e}")
        
        return None
    
    def add_connector(self, name: str, connector: PodcastPlatformConnector):
        """Add a new platform connector.
        
        Args:
            name: Name/identifier for the connector
            connector: PodcastPlatformConnector instance
        """
        self.connectors[name] = connector
        logger.info(f"Added connector: {name}")
    
    async def cleanup(self):
        """Cleanup resources used by the analyzer."""
        logger.info("Cleaning up podcast analyzer resources...")
        
        # Cleanup transcription service
        if hasattr(self.transcription_service, 'cleanup'):
            await self.transcription_service.cleanup()
        
        # Cleanup connectors
        for connector in self.connectors.values():
            if hasattr(connector, 'cleanup') and callable(getattr(connector, 'cleanup')):
                await connector.cleanup()  # type: ignore[attr-defined]
        
        logger.info("Cleanup complete")
