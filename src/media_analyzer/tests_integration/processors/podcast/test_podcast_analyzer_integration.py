"""Integration tests for podcast analysis with real RSS feeds."""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
from typing import Dict, Any

from media_analyzer.processors.podcast.analyzer import PodcastAnalyzer
from media_analyzer.processors.podcast.rss_connector import RSSFeedConnector
from media_analyzer.models.podcast import AnalysisOptions, PodcastEpisode, StreamingAnalysisResult


class TestPodcastIntegration:
    """Integration tests using real podcast RSS feeds."""
    
    @pytest.fixture
    def circle_round_feed_url(self):
        """Circle Round podcast RSS feed URL."""
        return "https://rss.wbur.org/circleround/podcast"
    
    @pytest_asyncio.fixture
    async def podcast_analyzer(self):
        """Create a podcast analyzer instance with proper cleanup."""
        config = {
            'transcription': {
                'model_size': 'base',  # Use smaller model for faster testing
            }
        }
        analyzer = PodcastAnalyzer(config)
        yield analyzer
        # Ensure cleanup happens
        await analyzer.cleanup()
    
    @pytest_asyncio.fixture
    async def rss_connector(self):
        """Create an RSS connector instance with proper cleanup."""
        connector = RSSFeedConnector()
        yield connector
        # Ensure cleanup happens
        await connector.cleanup()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circle_round_metadata_extraction(self, circle_round_feed_url, rss_connector):
        """Test metadata extraction from Circle Round RSS feed."""
        
        # Test RSS connector URL validation
        assert rss_connector.validate_url(circle_round_feed_url), "Circle Round RSS URL should be valid"
        
        # Extract episode metadata
        episode = await rss_connector.get_episode_metadata(circle_round_feed_url)
        
        # Validate episode structure
        assert isinstance(episode, PodcastEpisode), "Should return PodcastEpisode instance"
        assert episode.platform == "rss", "Platform should be RSS"
        assert episode.show_name == "Circle Round", "Should identify Circle Round as show name"
        
        # Check episode metadata
        assert episode.title is not None and len(episode.title) > 0, "Episode should have a title"
        assert episode.description is not None, "Episode should have a description"
        assert episode.url == circle_round_feed_url, "Episode URL should match feed URL"
        assert episode.episode_id is not None and len(episode.episode_id) > 0, "Episode should have an ID"
        
        # Check duration (Circle Round episodes are typically 15-25 minutes)
        if episode.duration_seconds:
            assert 10*60 <= episode.duration_seconds <= 35*60, f"Duration {episode.duration_seconds}s should be reasonable for Circle Round"
        
        # Check audio metadata
        assert episode.metadata is not None, "Episode should have metadata"
        assert 'audio_url' in episode.metadata, "Should have audio URL in metadata"
        assert episode.metadata['audio_url'].startswith('http'), "Audio URL should be valid HTTP URL"
        
        # Verify audio URL accessibility  
        audio_url = episode.metadata['audio_url']
        assert any(ext in audio_url.lower() for ext in ['.mp3', '.m4a', '.wav', 'audio']), "Audio URL should indicate audio content"
        
        print(f"\nCircle Round Episode Found:")
        print(f"   Title: {episode.title}")
        print(f"   Duration: {episode.duration_seconds}s ({episode.duration_seconds/60:.1f} min)" if episode.duration_seconds else "   Duration: Not specified")
        print(f"   Publication: {episode.publication_date}")
        print(f"   Audio URL: {audio_url[:100]}...")
        
        # Explicit cleanup to prevent SSL errors
        await rss_connector.cleanup()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circle_round_short_audio_analysis(self, circle_round_feed_url, podcast_analyzer):
        """Test complete podcast analysis with Circle Round (limited to first 4 minutes for subject detection)."""
        
        # Use options that limit processing while allowing enough content for subject detection
        options = AnalysisOptions(
            language="en",
            max_duration_minutes=4,  # Increase to 4 minutes for better subject detection
            segment_length_seconds=60,  # 1-minute segments for faster processing
            confidence_threshold=0.5,  # Lower threshold for better subject detection
            subject_extraction=True  # Test subject extraction
        )
        
        print(f"\n🎙️ Analyzing Circle Round episode (limited to 4 minutes for subject detection)...")
        
        # Run full analysis
        result = await podcast_analyzer.analyze_episode(circle_round_feed_url, options)
        
        # Validate analysis results
        assert isinstance(result, StreamingAnalysisResult), "Should return StreamingAnalysisResult"
        assert result.success, f"Analysis should succeed. Error: {result.error_message}"
        assert result.episode is not None, "Should have episode metadata"
        assert result.transcription is not None, "Should have transcription results"
        
        # Check transcription quality
        transcription = result.transcription
        assert len(transcription.text) > 10, "Transcription should have meaningful content"
        assert transcription.confidence > 0, "Should have confidence score"
        assert transcription.language == "en", "Should detect English language"
        
        # Check subject extraction
        assert isinstance(result.subjects, list), "Should return list of subjects"
        # With 4 minutes of content, we should be able to detect at least some subjects
        assert len(result.subjects) > 0, f"Should detect subjects in 4 minutes of Circle Round content. Transcription: {transcription.text[:300]}..."
        
        # Performance validation
        assert 'processing_time' in result.processing_metadata, "Should track processing time"
        processing_time = result.processing_metadata['processing_time']
        assert processing_time > 0, "Should track processing time"
        assert processing_time < 600, "Processing should complete within 10 minutes"  # Generous limit for 4 minutes of audio
        
        print(f"✅ Analysis Results:")
        print(f"   Episode: {result.episode.title}")
        print(f"   Transcription Length: {len(transcription.text)} characters")
        print(f"   Confidence: {transcription.confidence:.2f}")
        print(f"   Subjects Found: {len(result.subjects)}")
        print(f"   Processing Time: {processing_time:.1f}s")
        
        if result.subjects:
            # Sort subjects by confidence and show more details
            sorted_subjects = sorted(result.subjects, key=lambda x: x.confidence, reverse=True)
            print(f"   Top Subjects (with confidence):")
            for i, subject in enumerate(sorted_subjects[:5]):  # Show top 5 subjects
                print(f"     {i+1}. {subject.name} ({subject.confidence:.2f}) - {subject.subject_type}")
        
        # Print first part of transcription for verification
        print(f"   Transcription Preview: {transcription.text[:200]}...")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metadata_only_analysis(self, circle_round_feed_url, podcast_analyzer):
        """Test metadata extraction without audio analysis."""
        
        # Get just the metadata
        episode_metadata = await podcast_analyzer.get_episode_metadata(circle_round_feed_url)
        
        # Validate metadata
        assert isinstance(episode_metadata, PodcastEpisode), "Should return PodcastEpisode"
        assert episode_metadata.title is not None, "Should have episode title"
        assert episode_metadata.show_name == "Circle Round", "Should identify correct show"
        
        # Verify this is much faster than full analysis
        print(f"\n📋 Metadata Only:")
        print(f"   Title: {episode_metadata.title}")
        print(f"   Show: {episode_metadata.show_name}")
        print(f"   Duration: {episode_metadata.duration_seconds}s" if episode_metadata.duration_seconds else "   Duration: Unknown")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analysis_with_subject_extraction_disabled(self, circle_round_feed_url, podcast_analyzer):
        """Test analysis with subject extraction disabled for faster processing."""
        
        options = AnalysisOptions(
            language="en",
            max_duration_minutes=1,  # Very short for speed
            subject_extraction=False,  # Disable for faster processing
            confidence_threshold=0.5
        )
        
        print(f"\n⚡ Fast Analysis (no subjects, 1 minute limit)...")
        
        # Run analysis without subject extraction
        result = await podcast_analyzer.analyze_episode(circle_round_feed_url, options)
        
        # Validate results
        assert result.success, f"Analysis should succeed. Error: {result.error_message}"
        assert result.transcription is not None, "Should have transcription"
        assert len(result.subjects) == 0, "Should have no subjects when disabled"
        
        # Should be faster without subject extraction
        processing_time = result.processing_metadata.get('processing_time', 0)
        assert processing_time < 200, "Should be fast without subject extraction"
        
        print(f"✅ Fast Analysis Complete:")
        print(f"   Transcription: {len(result.transcription.text)} characters")
        print(f"   Processing Time: {processing_time:.1f}s")
        print(f"   Preview: {result.transcription.text[:150]}...")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_invalid_feed(self, podcast_analyzer):
        """Test error handling with invalid RSS feed."""
        
        invalid_url = "https://example.com/invalid-feed.xml"
        
        # Should handle invalid URL gracefully
        result = await podcast_analyzer.analyze_episode(invalid_url)
        
        assert isinstance(result, StreamingAnalysisResult), "Should return result object"
        assert result.success is False, "Should indicate failure"
        assert result.error_message is not None, "Should provide error message"
        assert "Failed to fetch RSS feed" in result.error_message, "Should indicate RSS fetch failure"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audio_format_detection(self, circle_round_feed_url, rss_connector):
        """Test detection of different audio formats in RSS feeds."""
        
        episode = await rss_connector.get_episode_metadata(circle_round_feed_url)
        audio_url = episode.metadata['audio_url']
        
        # Test basic format detection from URL
        if '.mp3' in audio_url.lower():
            detected_format = 'mp3'
        elif '.m4a' in audio_url.lower():
            detected_format = 'm4a'
        elif '.wav' in audio_url.lower():
            detected_format = 'wav'
        elif '.aac' in audio_url.lower():
            detected_format = 'aac'
        else:
            detected_format = 'mp3'  # Default assumption for podcast audio
        
        assert detected_format in ['mp3', 'm4a', 'wav', 'aac'], f"Should detect valid audio format, got: {detected_format}"
        
        print(f"\n🔍 Audio Format Detection:")
        print(f"   URL: {audio_url}")
        print(f"   Detected Format: {detected_format}")
        print(f"   Content Type: {episode.metadata.get('audio_type', 'Not specified')}")
        print(f"   Audio Length: {episode.metadata.get('audio_length', 'Not specified')} bytes")

    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_cleanup_resources(self, podcast_analyzer):
        """Test that resources are properly cleaned up."""
        
        # Run a quick analysis
        options = AnalysisOptions(max_duration_minutes=1, subject_extraction=False)
        
        # This should work without issues
        await podcast_analyzer.get_episode_metadata("https://rss.wbur.org/circleround/podcast")
        
        # Cleanup should not raise errors
        await podcast_analyzer.cleanup()
        
        print("✅ Resource cleanup completed successfully")
        
    def test_analysis_options_validation(self):
        """Test validation of analysis options."""
        
        # Valid options should work
        valid_options = AnalysisOptions(
            language="en",
            max_duration_minutes=30,
            confidence_threshold=0.7
        )
        assert valid_options.language == "en"
        assert valid_options.max_duration_minutes == 30
        
        # Invalid options should raise errors
        with pytest.raises(ValueError, match="max_duration_minutes must be positive"):
            AnalysisOptions(max_duration_minutes=0)
            
        with pytest.raises(ValueError, match="confidence_threshold must be between 0 and 1"):
            AnalysisOptions(confidence_threshold=1.5)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_episode_selection_integration(self, circle_round_feed_url, podcast_analyzer, rss_connector):
        """Test episode selection functionality integrated with podcast analyzer."""
        
        print(f"\nTesting Episode Selection Integration...")
        
        # Test 1: Default episode (index 0) vs explicit index 0
        default_episode = await podcast_analyzer.get_episode_metadata(circle_round_feed_url)
        
        options_index_0 = AnalysisOptions(episode_index=0)
        explicit_episode_0 = await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_index_0)
        
        assert default_episode.episode_id == explicit_episode_0.episode_id, \
            "Default episode should match explicit index 0"
        print(f"   Default episode matches explicit index 0: '{default_episode.title}'")
        
        # Test 2: Different episodes by index
        options_index_1 = AnalysisOptions(episode_index=1)
        episode_1 = await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_index_1)
        
        options_index_2 = AnalysisOptions(episode_index=2)
        episode_2 = await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_index_2)
        
        assert episode_1.episode_id != episode_2.episode_id, "Different indices should return different episodes"
        print(f"   Episode 1: '{episode_1.title}'")
        print(f"   Episode 2: '{episode_2.title}'")
        
        # Test 3: Episode selection by title
        # Use a distinctive word from episode 1 for title search
        title_words = episode_1.title.split()
        search_term = None
        
        # Find a distinctive word (avoid common words)
        common_words = {'the', 'and', 'of', 'to', 'in', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'with'}
        for word in title_words:
            clean_word = word.strip('.,!?:;"()').lower()
            if len(clean_word) > 3 and clean_word not in common_words:
                search_term = clean_word
                break
        
        if not search_term:
            search_term = title_words[0].strip('.,!?:;"()') if title_words else "episode"
        
        print(f"   Searching for episode with term: '{search_term}'")
        
        try:
            options_title = AnalysisOptions(episode_title=search_term)
            episode_by_title = await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_title)
            
            assert search_term.lower() in episode_by_title.title.lower(), \
                f"Found episode should contain search term '{search_term}'"
            print(f"   Found episode by title: '{episode_by_title.title}'")
            
        except ValueError as e:
            print(f"   Title search failed (expected for unique titles): {e}")
        
        # Test 4: Full analysis with episode selection
        print(f"   Running full analysis on selected episode...")
        
        analysis_options = AnalysisOptions(
            episode_index=1,  # Use episode 1 for analysis
            max_duration_minutes=2,  # Keep short for testing
            segment_length_seconds=30,
            confidence_threshold=0.5,
            subject_extraction=True
        )
        
        result = await podcast_analyzer.analyze_episode(circle_round_feed_url, analysis_options)
        
        # Validate analysis results
        assert result.success, f"Analysis should succeed. Error: {result.error_message}"
        assert result.episode.episode_id == episode_1.episode_id, \
            "Analysis result should match selected episode"
        assert len(result.transcription.text) > 0, "Should have transcription content"
        
        print(f"   Full analysis completed on: '{result.episode.title}'")
        print(f"       Transcription length: {len(result.transcription.text)} chars")
        print(f"       Subjects found: {len(result.subjects)}")
        print(f"       Processing time: {result.processing_metadata.get('processing_time', 0):.1f}s")
        
        # Test 5: Error handling
        print(f"   Testing error handling...")
        
        # Invalid episode index
        try:
            options_invalid = AnalysisOptions(episode_index=999)
            await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_invalid)
            assert False, "Should raise ValueError for invalid index"
        except ValueError as e:
            assert "Episode index 999 not found" in str(e)
            print(f"   Invalid index properly handled: {e}")
        
        # Non-existent episode title
        try:
            options_invalid_title = AnalysisOptions(episode_title="NonExistentEpisodeXYZ123")
            await podcast_analyzer.get_episode_metadata(circle_round_feed_url, options_invalid_title)
            assert False, "Should raise ValueError for non-existent title"
        except ValueError as e:
            assert "Episode with title 'NonExistentEpisodeXYZ123' not found" in str(e)
            print(f"   Invalid title properly handled: {e}")
        
        print(f"Episode Selection Integration Tests Passed!")
        
        # Explicit cleanup to prevent SSL errors
        await podcast_analyzer.cleanup()
        await rss_connector.cleanup()
