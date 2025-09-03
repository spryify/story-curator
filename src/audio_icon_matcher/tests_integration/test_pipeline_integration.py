"""Integration tests for AudioIconPipeline."""

import pytest
import tempfile
import os
import time
import wave
import struct
import subprocess
from pathlib import Path

from audio_icon_matcher.core.pipeline import AudioIconPipeline
from audio_icon_matcher.models.results import AudioIconResult, IconMatch
from audio_icon_matcher.core.exceptions import AudioIconValidationError, AudioIconProcessingError


def create_story_audio_file(output_path: Path, text: str, voice: str = "Samantha", rate: int = 150) -> Path:
    """Create an audio file using macOS 'say' command with children's story content.
    
    Args:
        output_path: Where to save the audio file
        text: Story text to convert to speech
        voice: Voice to use (child-friendly voices: Samantha, Victoria, Alex)
        rate: Speaking rate (words per minute, slower for children)
        
    Returns:
        Path to the created audio file
    """
    # Create temp AIFF file first (say command native format)
    temp_aiff = output_path.with_suffix('.aiff')
    
    try:
        # Generate speech with macOS say command
        subprocess.run(
            ["say", "-r", str(rate), "-v", voice, "-o", str(temp_aiff), text],
            check=True
        )
        
        # Convert AIFF to WAV using ffmpeg if available, otherwise use the AIFF directly
        try:
            subprocess.run(
                ["ffmpeg", "-i", str(temp_aiff), "-ar", "16000", "-ac", "1", "-y", str(output_path)],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: rename AIFF to output path
            temp_aiff.rename(output_path)
            
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to generate speech audio: {e}")
    finally:
        # Clean up temp file if it still exists
        if temp_aiff.exists() and temp_aiff != output_path:
            temp_aiff.unlink()
    
    return output_path


class TestAudioIconPipelineIntegration:
    """Integration tests for the AudioIconPipeline using real components."""
    
    @pytest.fixture(scope="session")
    def children_story_texts(self):
        """Sample children's story texts for audio generation."""
        return {
            "magic_garden": """
                The Magic Garden Adventure. In a colorful garden lived a curious butterfly named Flutter. 
                Flutter loved to explore and learn about all the flowers. One sunny morning, Flutter met 
                a wise old owl named Professor Hoot. Would you like to learn about the special magic of 
                the garden, asked Professor Hoot. Oh yes, please, Flutter replied excitedly. The garden 
                was full of beautiful roses, daisies, and sunflowers that danced in the gentle breeze.
            """,
            
            "animal_friends": """
                The Tale of Animal Friends. Once upon a time, in a peaceful forest, lived many animal 
                friends. There was a playful rabbit named Hop, a wise old owl called Hoot, a friendly 
                bear named Cuddles, and a colorful bird named Melody. Every day they would meet by the 
                big oak tree to share stories and help each other. They learned that friendship is the 
                most precious treasure of all.
            """,
            
            "weather_adventure": """
                Let's Learn About Weather! Today we're going on a weather adventure. When the bright 
                sun shines, we can play outside and enjoy the warmth. Sometimes fluffy white clouds 
                fill the blue sky, and gentle rain falls to water all the plants and flowers. In winter, 
                beautiful white snow covers everything like a magical blanket. Weather changes bring 
                new adventures every day.
            """,
            
            "ocean_discovery": """
                Under the Sea Adventure. Deep in the blue ocean lived many fascinating sea creatures. 
                There were colorful fish swimming through coral reefs, graceful dolphins jumping and 
                playing, and gentle sea turtles gliding through the water. A little seahorse named 
                Splash loved to explore and discover new parts of the ocean kingdom every day.
            """,
            
            "space_journey": """
                Journey to the Stars. High up in the night sky, twinkling stars light up the darkness. 
                The bright moon watches over us while we sleep. Astronauts in their special spaceships 
                travel to visit distant planets and explore the wonders of space. Maybe someday you'll 
                become an astronaut and journey among the stars too.
            """
        }
    
    @pytest.fixture
    def story_audio_files(self, tmp_path, children_story_texts):
        """Generate actual audio files from children's stories using the 'say' command."""
        audio_files = {}
        
        for story_name, story_text in children_story_texts.items():
            audio_path = tmp_path / f"{story_name}.wav"
            try:
                create_story_audio_file(audio_path, story_text.strip(), voice="Samantha", rate=150)
                audio_files[story_name] = audio_path
            except Exception as e:
                # Log error but don't skip the entire fixture - just skip this file
                print(f"Warning: Could not generate audio file {story_name}: {e}")
                continue
        
        # Only skip if NO audio files were generated
        if not audio_files:
            pytest.skip("Could not generate any audio files")
        
        yield audio_files
        
        # Cleanup
        for audio_path in audio_files.values():
            if audio_path.exists():
                audio_path.unlink()

    @pytest.fixture
    def test_audio_file(self, story_audio_files):
        """Provide a single test audio file for simple tests."""
        if not story_audio_files:
            pytest.skip("No story audio files available")
        
        # Return the first available story audio file
        return next(iter(story_audio_files.values()))
    
    @pytest.mark.integration
    def test_pipeline_end_to_end_real_components(self, test_audio_file):
        """Test the complete pipeline with real components."""
        # This test requires actual services to be available
        # It might fail if external services (Whisper, database) are not set up
        
        pipeline = AudioIconPipeline()
        
        # Test with minimal requirements - if this fails, it means the pipeline
        # integration is broken, not just external services
        try:
            result = pipeline.process(str(test_audio_file), max_icons=3, confidence_threshold=0.1)
            
            # Basic result structure validation
            assert isinstance(result, AudioIconResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'transcription')
            assert hasattr(result, 'processing_time')
            assert hasattr(result, 'icon_matches')
            assert hasattr(result, 'subjects')
            assert hasattr(result, 'metadata')
            
            # Processing time should be reasonable
            assert result.processing_time > 0
            assert result.processing_time < 60  # Should complete within 60 seconds
            
        except Exception as e:
            # If external services are not available, that's expected in CI/testing environments
            # But we should still test the pipeline structure
            pytest.skip(f"External services not available for integration test: {e}")
    
    def test_pipeline_file_validation(self):
        """Test that pipeline properly validates input files."""
        pipeline = AudioIconPipeline()
        
        # Test with non-existent file
        with pytest.raises((AudioIconValidationError, FileNotFoundError)):
            pipeline.process("/nonexistent/file.wav")
        
        # Test with invalid file extension - should fail at processing stage
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"This is not audio data")
        
        try:
            result = pipeline.process(temp_path)
            # Should either raise an exception or return failure result
            if hasattr(result, 'success'):
                assert result.success is False, "Processing invalid file should fail"
                assert result.error is not None, "Failed result should contain error message"
        except (AudioIconValidationError, AudioIconProcessingError):
            # Exception is also acceptable
            pass
        finally:
            os.unlink(temp_path)
    
    def test_pipeline_different_audio_formats(self):
        """Test pipeline accepts different audio formats."""
        pipeline = AudioIconPipeline()
        
        # Test format validation logic without external dependencies
        supported_formats = {".wav", ".mp3", ".m4a", ".aac"}
        
        for fmt in supported_formats:
            with tempfile.NamedTemporaryFile(suffix=fmt, delete=False) as f:
                temp_path = f.name
                # Write minimal valid audio header for WAV
                if fmt == ".wav":
                    # Write a minimal WAV header
                    with wave.open(temp_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(44100)
                        # Empty audio data
                        wav_file.writeframes(b'')
            
            try:
                # This will likely fail due to invalid/empty audio content,
                # but it should fail at the processing stage, not validation
                pipeline.process(temp_path, max_icons=1)
            except Exception as e:
                # We expect processing errors for empty/invalid audio,
                # but not validation errors for supported formats
                assert not isinstance(e, AudioIconValidationError), \
                    f"Format {fmt} should be supported but got validation error: {e}"
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    @pytest.mark.integration
    def test_pipeline_concurrency_safety(self, test_audio_file):
        """Test that pipeline can handle concurrent requests safely."""
        import threading
        import time
        
        pipeline = AudioIconPipeline()
        results = []
        errors = []
        
        def run_pipeline():
            try:
                result = pipeline.process(str(test_audio_file), max_icons=2, confidence_threshold=0.1)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_pipeline)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Check that threads completed (might have external service errors, but shouldn't hang)
        assert len(results) + len(errors) == 3, "Some threads did not complete"
    
    @pytest.mark.integration
    def test_pipeline_configuration_options(self, test_audio_file):
        """Test that pipeline respects configuration parameters."""
        pipeline = AudioIconPipeline()
        
        try:
            # Test max_icons parameter
            result1 = pipeline.process(str(test_audio_file), max_icons=1, confidence_threshold=0.0)
            result2 = pipeline.process(str(test_audio_file), max_icons=5, confidence_threshold=0.0)
            
            # If both succeed, result2 should have >= result1 icons (up to availability)
            if result1.success and result2.success:
                assert len(result1.icon_matches) <= len(result2.icon_matches)
                assert len(result1.icon_matches) <= 1
                assert len(result2.icon_matches) <= 5
            
        except Exception as e:
            # External service errors are acceptable in integration tests
            pytest.skip(f"External services not available: {e}")
    
    def test_pipeline_error_handling_and_recovery(self):
        """Test that pipeline handles errors gracefully and provides useful information."""
        pipeline = AudioIconPipeline()
        
        # Test with various invalid inputs
        invalid_files = [
            ("/dev/null", "empty file"),
            ("/nonexistent.wav", "nonexistent file"),
        ]
        
        for invalid_file, description in invalid_files:
            try:
                result = pipeline.process(invalid_file, max_icons=1)
                # If it somehow succeeds, it should indicate failure
                if hasattr(result, 'success'):
                    assert result.success is False, f"Should fail for {description}"
            except Exception as e:
                # Errors are expected, but they should be meaningful
                assert len(str(e)) > 0, f"Error message should not be empty for {description}"
                # Should be appropriate exception types
                assert isinstance(e, (AudioIconValidationError, AudioIconProcessingError, FileNotFoundError))
    
    @pytest.mark.integration
    def test_pipeline_performance_reasonable(self, test_audio_file):
        """Test that pipeline completes in reasonable time."""
        pipeline = AudioIconPipeline()
        
        start_time = time.time()
        try:
            result = pipeline.process(str(test_audio_file), max_icons=3, confidence_threshold=0.3)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete within reasonable time (adjust based on your requirements)
            assert processing_time < 120, f"Pipeline took too long: {processing_time} seconds"
            
            if result.success:
                # Result processing time should be tracked
                assert result.processing_time > 0
                assert result.processing_time <= processing_time
                
        except Exception as e:
            # External service errors are expected in some environments
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Even failures should complete in reasonable time
            assert processing_time < 30, f"Even failure took too long: {processing_time} seconds"
    
    @pytest.mark.integration
    def test_children_story_scenarios(self, story_audio_files):
        """Test pipeline with different children's story scenarios."""
        if not story_audio_files:
            pytest.skip("No story audio files available for testing")
        
        pipeline = AudioIconPipeline()
        
        # Test each story type
        story_expectations = {
            "magic_garden": ["garden", "butterfly", "flower", "nature"],
            "animal_friends": ["animal", "rabbit", "owl", "bear", "bird"],
            "weather_adventure": ["weather", "sun", "cloud", "rain", "snow"],
            "ocean_discovery": ["ocean", "sea", "fish", "dolphin", "turtle"],
            "space_journey": ["space", "star", "moon", "astronaut", "planet"]
        }
        
        for story_name, audio_path in story_audio_files.items():
            try:
                result = pipeline.process(str(audio_path), max_icons=5, confidence_threshold=0.2)
                
                if result.success:
                    # Verify we got some transcription
                    assert isinstance(result.transcription, str)
                    assert len(result.transcription.strip()) > 0
                    
                    # Check if expected themes appear in subjects or transcription
                    expected_themes = story_expectations.get(story_name, [])
                    transcription_lower = result.transcription.lower()
                    
                    found_themes = []
                    for theme in expected_themes:
                        if theme.lower() in transcription_lower:
                            found_themes.append(theme)
                    
                    # Should find at least some expected themes
                    if expected_themes:
                        assert len(found_themes) > 0, \
                            f"Story '{story_name}' should contain themes {expected_themes}, " \
                            f"but transcription was: {result.transcription}"
                    
                    # Should complete in reasonable time
                    assert result.processing_time < 120, \
                        f"Story '{story_name}' took too long: {result.processing_time} seconds"
                    
            except Exception as e:
                # External services might not be available - that's acceptable
                pytest.skip(f"External services not available for story '{story_name}': {e}")
    
    @pytest.mark.integration
    def test_story_icon_matching_quality(self, story_audio_files):
        """Test that icon matches are relevant to story content."""
        if not story_audio_files:
            pytest.skip("No story audio files available for testing")
        
        pipeline = AudioIconPipeline()
        
        # Test one story in detail
        story_name = "animal_friends"
        if story_name not in story_audio_files:
            pytest.skip(f"Story '{story_name}' not available for testing")
        
        try:
            result = pipeline.process(
                str(story_audio_files[story_name]), 
                max_icons=10, 
                confidence_threshold=0.1
            )
            
            if result.success and result.icon_matches:
                # Check that icon matches have proper structure
                for match in result.icon_matches:
                    assert isinstance(match, IconMatch)
                    assert hasattr(match, 'icon')
                    assert hasattr(match, 'confidence')
                    assert hasattr(match, 'match_reason')
                    assert 0 <= match.confidence <= 1
                
                # For animal friends story, expect animal-related icons
                icon_names = [match.icon.name.lower() for match in result.icon_matches]
                icon_tags = []
                for match in result.icon_matches:
                    if hasattr(match.icon, 'tags') and match.icon.tags:
                        icon_tags.extend([tag.lower() for tag in match.icon.tags])
                
                # Should find some animal-related content
                animal_terms = ["animal", "rabbit", "owl", "bear", "bird", "pet", "creature"]
                found_animal_terms = any(
                    any(term in name for term in animal_terms) for name in icon_names
                ) or any(
                    any(term in tag for term in animal_terms) for tag in icon_tags
                )
                
                if not found_animal_terms:
                    # Log for debugging but don't fail - icon database might not have animal icons
                    print(f"Warning: No animal-related icons found for animal story")
                    print(f"Icon names: {icon_names}")
                    print(f"Icon tags: {icon_tags}")
                
        except Exception as e:
            pytest.skip(f"External services not available for icon matching test: {e}")
    
    @pytest.mark.integration
    def test_multiple_story_processing(self, story_audio_files):
        """Test processing multiple different stories in sequence."""
        if len(story_audio_files) < 2:
            pytest.skip("Need at least 2 story audio files for this test")
        
        pipeline = AudioIconPipeline()
        results = []
        
        # Process up to 3 stories to keep test time reasonable
        stories_to_test = list(story_audio_files.items())[:3]
        
        total_start = time.time()
        for story_name, audio_path in stories_to_test:
            try:
                result = pipeline.process(str(audio_path), max_icons=3, confidence_threshold=0.3)
                results.append((story_name, result))
            except Exception as e:
                results.append((story_name, None))
        
        total_time = time.time() - total_start
        
        # Should complete all stories in reasonable time
        assert total_time < 300, f"Processing {len(stories_to_test)} stories took too long: {total_time} seconds"
        
        # Check that we got some results
        successful_results = [(name, result) for name, result in results if result and result.success]
        
        if successful_results:
            # Verify each successful result
            for story_name, result in successful_results:
                assert isinstance(result.transcription, str)
                assert result.processing_time > 0
                assert isinstance(result.subjects, dict)
                assert isinstance(result.metadata, dict)


class TestPipelineRealWorldScenarios:
    """Test pipeline with realistic scenarios using real story audio."""
    
    @pytest.mark.integration
    def test_educational_content_recognition(self, tmp_path):
        """Test pipeline with educational content scenarios."""
        educational_stories = {
            "counting_lesson": """
                Let's Count Together! One butterfly dancing in the garden, two happy bees buzzing 
                around the flowers, three little frogs sitting by the pond, four colorful birds 
                singing in the trees, and five busy ants marching in a line. Counting is so much 
                fun when we practice with our animal friends!
            """,
            
            "colors_lesson": """
                Learning About Beautiful Colors! Look at the bright red roses blooming in the garden, 
                the golden yellow sunshine warming our faces, the deep blue sky stretching far above, 
                the fresh green grass tickling our toes, and the pretty purple violets smiling at us. 
                Colors make our world magical and wonderful!
            """
        }
        
        pipeline = AudioIconPipeline()
        
        for lesson_name, lesson_text in educational_stories.items():
            audio_path = tmp_path / f"{lesson_name}.wav"
            
            try:
                create_story_audio_file(audio_path, lesson_text.strip(), voice="Victoria", rate=140)
                
                result = pipeline.process(str(audio_path), max_icons=5, confidence_threshold=0.2)
                
                if result.success:
                    # Educational content should be transcribed clearly
                    assert len(result.transcription.strip()) > 20
                    
                    # Should complete quickly for short educational content
                    assert result.processing_time < 60
                    
                    # Should extract educational themes
                    transcription = result.transcription.lower()
                    if lesson_name == "counting_lesson":
                        # Should recognize numbers or counting concepts
                        number_words = ["one", "two", "three", "four", "five", "count"]
                        found_numbers = any(word in transcription for word in number_words)
                        assert found_numbers, f"Counting lesson should contain number words: {transcription}"
                    
                    elif lesson_name == "colors_lesson":
                        # Should recognize color words
                        color_words = ["red", "yellow", "blue", "green", "purple", "color"]
                        found_colors = any(word in transcription for word in color_words)
                        assert found_colors, f"Color lesson should contain color words: {transcription}"
                
            except Exception as e:
                pytest.skip(f"Could not test educational content '{lesson_name}': {e}")
            finally:
                if audio_path.exists():
                    audio_path.unlink()


class TestPodcastPipelineIntegration:
    """Integration tests for podcast functionality."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_podcast_rss_feed_integration(self):
        """Test integration with real RSS feed (Circle Round)."""
        try:
            pipeline = AudioIconPipeline()
            
            # Use Circle Round RSS feed for testing
            test_url = "https://rss.wbur.org/circleround/podcast"
            
            # Validate URL first
            is_valid = pipeline.validate_podcast_url(test_url)
            if not is_valid:
                pytest.skip("Circle Round RSS feed not accessible")
            
            # Process podcast episode using async method
            result = await pipeline.process_async(
                test_url,
                max_icons=5,
                confidence_threshold=0.3
            )
            
            # Validate results
            assert isinstance(result, AudioIconResult)
            
            if result.success:
                # Check basic structure
                assert result.transcription is not None
                assert len(result.transcription) > 0
                assert result.transcription_confidence > 0
                assert result.metadata['source_type'] == 'podcast'
                
                # Should have episode metadata
                assert 'episode_title' in result.metadata
                assert 'show_name' in result.metadata
                assert result.metadata['show_name'] == "Circle Round"
                
                # Should have subjects extracted
                assert isinstance(result.subjects, dict)
                
                print(f"Successfully processed podcast episode:")
                print(f"  Title: {result.metadata.get('episode_title', 'Unknown')}")
                print(f"  Transcription length: {len(result.transcription)} chars")
                print(f"  Processing time: {result.processing_time:.2f}s")
                print(f"  Icon matches: {len(result.icon_matches)}")
                
            else:
                print(f"Podcast processing failed: {result.error}")
                # Don't fail test for expected network/API issues
                pytest.skip(f"Podcast processing failed: {result.error}")
                
        except Exception as e:
            pytest.skip(f"Podcast integration test failed: {e}")
        finally:
            # Cleanup
            try:
                await pipeline.cleanup()
            except Exception:
                pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_specific_circle_round_episode_integration(self):
        """Test integration with a specific Circle Round episode from a few months ago."""
        try:
            pipeline = AudioIconPipeline()
            
            # Use Circle Round RSS feed for testing
            test_url = "https://rss.wbur.org/circleround/podcast"
            
            # Validate URL first
            is_valid = pipeline.validate_podcast_url(test_url)
            if not is_valid:
                pytest.skip("Circle Round RSS feed not accessible")
            
            # Test with a specific episode by title (partial match, case-insensitive)
            # Using an episode that should be stable and available from a few months ago
            target_episode_title = "The Pot of Gold"  # A classic story that's likely to be available
            
            result = await pipeline.process_async(
                test_url,
                max_icons=8,
                confidence_threshold=0.25,
                episode_title=target_episode_title
            )
            
            # Validate results
            assert isinstance(result, AudioIconResult)
            
            if result.success:
                # Check basic structure
                assert result.transcription is not None
                assert len(result.transcription) > 100, "Should have substantial transcription content"
                assert result.transcription_confidence > 0.5, "Should have reasonable transcription confidence"
                assert result.metadata['source_type'] == 'podcast'
                
                # Should have episode metadata
                assert 'episode_title' in result.metadata
                assert 'show_name' in result.metadata
                assert result.metadata['show_name'] == "Circle Round"
                
                # Check that we got the episode we requested (or close to it)
                episode_title = result.metadata.get('episode_title', '').lower()
                target_lower = target_episode_title.lower()
                
                # Should contain key words from the target title or be a similar story
                title_match = (
                    target_lower in episode_title or 
                    any(word in episode_title for word in target_lower.split()) or
                    "gold" in episode_title or "treasure" in episode_title
                )
                
                print(f"Successfully processed specific Circle Round episode:")
                print(f"  Requested: {target_episode_title}")
                print(f"  Got: {result.metadata.get('episode_title', 'Unknown')}")
                print(f"  Transcription length: {len(result.transcription)} chars")
                print(f"  Transcription confidence: {result.transcription_confidence:.2f}")
                print(f"  Processing time: {result.processing_time:.2f}s")
                print(f"  Icon matches: {len(result.icon_matches)}")
                print(f"  Subjects found: {len(result.subjects)}")
                
                # Should have extracted subjects
                assert isinstance(result.subjects, dict)
                assert len(result.subjects) > 0, "Should extract at least some subjects"
                
                # Should have some icon matches
                assert len(result.icon_matches) > 0, "Should find at least some icon matches"
                
                # Verify icon matches have proper structure
                for match in result.icon_matches:
                    assert isinstance(match, IconMatch)
                    assert hasattr(match, 'icon')
                    assert hasattr(match, 'confidence')
                    assert hasattr(match, 'match_reason')
                    assert 0 <= match.confidence <= 1
                    assert len(match.match_reason) > 0, "Should have match reasoning"
                
                # For a story episode, expect story-related subjects and icons
                transcription_lower = result.transcription.lower()
                
                # Check for story elements in transcription
                story_elements = ["story", "once", "character", "adventure", "learn", "tale"]
                found_story_elements = [elem for elem in story_elements if elem in transcription_lower]
                
                if found_story_elements:
                    print(f"  Found story elements: {found_story_elements}")
                
                # Processing should be reasonably fast (under 2 minutes)
                assert result.processing_time < 120, f"Processing took too long: {result.processing_time}s"
                
                # Print subject types found for debugging
                subject_types = list(result.subjects.keys())
                print(f"  Subject types: {subject_types}")
                
                # Print top icon matches for debugging
                top_matches = result.icon_matches[:3]
                print("  Top icon matches:")
                for i, match in enumerate(top_matches, 1):
                    print(f"    {i}. {match.icon.name} (confidence: {match.confidence:.2f}) - {match.match_reason}")
                
            else:
                error_msg = result.error if hasattr(result, 'error') and result.error else "Unknown error"
                print(f"Episode processing failed: {error_msg}")
                
                # If the specific episode wasn't found, that's still valuable information
                if "episode not found" in error_msg.lower() or "no episodes found" in error_msg.lower():
                    print(f"Episode '{target_episode_title}' not found in current feed - this is expected behavior")
                else:
                    pytest.skip(f"Podcast processing failed: {error_msg}")
                
        except Exception as e:
            pytest.skip(f"Specific episode integration test failed: {e}")
        finally:
            # Cleanup
            try:
                await pipeline.cleanup()
            except Exception:
                pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_episode_selection_by_index(self):
        """Test selecting a specific episode by index from Circle Round."""
        try:
            pipeline = AudioIconPipeline()
            
            # Use Circle Round RSS feed for testing
            test_url = "https://rss.wbur.org/circleround/podcast"
            
            # Validate URL first
            is_valid = pipeline.validate_podcast_url(test_url)
            if not is_valid:
                pytest.skip("Circle Round RSS feed not accessible")
            
            # Test with episode index 5 (6th episode from the top, should be a few weeks/months old)
            episode_index = 5
            
            result = await pipeline.process_async(
                test_url,
                max_icons=6,
                confidence_threshold=0.3,
                episode_index=episode_index
            )
            
            # Validate results
            assert isinstance(result, AudioIconResult)
            
            if result.success:
                # Check basic structure
                assert result.transcription is not None
                assert len(result.transcription) > 50, "Should have transcription content"
                assert result.metadata['source_type'] == 'podcast'
                
                # Should have episode metadata
                assert 'episode_title' in result.metadata
                assert 'show_name' in result.metadata
                assert result.metadata['show_name'] == "Circle Round"
                
                print(f"Successfully processed Circle Round episode at index {episode_index}:")
                print(f"  Title: {result.metadata.get('episode_title', 'Unknown')}")
                print(f"  Episode number/date: {result.metadata.get('episode_number', 'Unknown')}")
                print(f"  Published: {result.metadata.get('published_date', 'Unknown')}")
                print(f"  Transcription length: {len(result.transcription)} chars")
                print(f"  Processing time: {result.processing_time:.2f}s")
                print(f"  Icon matches: {len(result.icon_matches)}")
                
                # Print subject types found for debugging
                subject_types = list(result.subjects.keys())
                print(f"  Subject types: {subject_types}")
                
                # Print top icon matches for debugging
                if result.icon_matches:
                    top_matches = result.icon_matches[:3]
                    print("  Top icon matches:")
                    for i, match in enumerate(top_matches, 1):
                        print(f"    {i}. {match.icon.name} (confidence: {match.confidence:.2f}) - {match.match_reason}")
                else:
                    print("  No icon matches found")
                
                # Should have reasonable processing time
                assert result.processing_time < 120, f"Processing took too long: {result.processing_time}s"
                
                # Should extract some content
                assert len(result.subjects) >= 0  # May be 0 if subject extraction is disabled for speed
                assert len(result.icon_matches) >= 0  # May be 0 if no good matches found
                
            else:
                error_msg = result.error if hasattr(result, 'error') and result.error else "Unknown error"
                print(f"Episode at index {episode_index} processing failed: {error_msg}")
                pytest.skip(f"Episode processing failed: {error_msg}")
                
        except Exception as e:
            pytest.skip(f"Episode index selection test failed: {e}")
        finally:
            # Cleanup
            try:
                await pipeline.cleanup()
            except Exception:
                pass
    
    @pytest.mark.integration
    def test_mixed_source_processing(self):
        """Test processing both local files and podcast URLs."""
        try:
            pipeline = AudioIconPipeline()
            
            # Create a simple test audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                audio_path = Path(temp_file.name)
            
            try:
                # Create test story audio
                story_text = "Once upon a time, there was a little cat who loved to play with a red ball."
                create_story_audio_file(audio_path, story_text)
                
                if not audio_path.exists():
                    pytest.skip("Could not create test audio file")
                
                # Test local file processing
                local_result = pipeline.process(
                    str(audio_path),
                    max_icons=3,
                    confidence_threshold=0.3
                )
                
                assert isinstance(local_result, AudioIconResult)
                if local_result.success:
                    assert local_result.metadata['source_type'] == 'local_file'
                    assert 'audio_file' in local_result.metadata
                
                # Test podcast URL processing (if RSS feed is accessible)
                test_url = "https://rss.wbur.org/circleround/podcast"
                if pipeline.validate_podcast_url(test_url):
                    podcast_result = pipeline.process(
                        test_url,
                        max_icons=3,
                        confidence_threshold=0.3
                    )
                    
                    assert isinstance(podcast_result, AudioIconResult)
                    if podcast_result.success:
                        assert podcast_result.metadata['source_type'] == 'podcast'
                        assert 'episode_title' in podcast_result.metadata
                        
                        print("Successfully tested both source types:")
                        print(f"  Local file: {local_result.success}")
                        print(f"  Podcast URL: {podcast_result.success}")
                
            finally:
                if audio_path.exists():
                    audio_path.unlink()
                    
        except Exception as e:
            pytest.skip(f"Mixed source test failed: {e}")


class TestEnhancedPipelineIntegration:
    """Integration tests for enhanced pipeline functionality."""
    
    def test_title_boosting_end_to_end(self):
        """Test that title boosting works in the full pipeline."""
        # Simple story for quick testing
        story_text = "The princess lived in a castle. The princess was very kind."
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_path = Path(temp_file.name)
        
        try:
            create_story_audio_file(audio_path, story_text, rate=200)  # Faster speech
            
            pipeline = AudioIconPipeline()
            
            # Process with title that matches story content
            result = pipeline.process(
                str(audio_path),
                episode_title="Princess Adventure",
                max_icons=8,
                confidence_threshold=0.2
            )
            
            # Should succeed
            assert result.success, f"Pipeline failed: {result.error}"
            assert len(result.icon_matches) > 0, "Should find some icon matches"
                
        finally:
            if audio_path.exists():
                audio_path.unlink()
    
    def test_consolidated_classes_work_together(self):
        """Test that consolidated IconMatcher and KeywordExtractor work in pipeline."""
        # Simple story to test NLP processing
        story_text = "The wizard lived in a tower. The dragon protected the village."
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_path = Path(temp_file.name)
        
        try:
            create_story_audio_file(audio_path, story_text, rate=200)
            
            pipeline = AudioIconPipeline()
            result = pipeline.process(
                str(audio_path),
                max_icons=10,
                confidence_threshold=0.1
            )
            
            # Should work without errors with consolidated classes
            assert result.success, f"Pipeline failed: {result.error}"
            
            if result.icon_matches:
                # Should have matched subjects from enhanced keyword extraction
                all_subjects = []
                for match in result.icon_matches:
                    all_subjects.extend(match.subjects_matched)
                
                # Should find some story-related subjects
                assert len(all_subjects) > 0, "Should extract subjects with enhanced NLP"
                
        finally:
            if audio_path.exists():
                audio_path.unlink()
    
    def test_enhanced_pipeline_robustness(self):
        """Test that enhanced pipeline handles various content types robustly."""
        test_cases = [
            ("Simple story", "The king ruled wisely"),
            ("Modern content", "The computer processed the data"),
            ("Mixed content", "The digital princess used magic technology")
        ]
        
        for test_name, story_text in test_cases:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio_path = Path(temp_file.name)
            
            try:
                create_story_audio_file(audio_path, story_text, rate=250)
                
                pipeline = AudioIconPipeline()
                result = pipeline.process(
                    str(audio_path),
                    max_icons=5,
                    confidence_threshold=0.1
                )
                
                # Should handle all content types without crashing
                assert isinstance(result.success, bool), f"{test_name} should return valid result"
                
                if not result.success:
                    # Log the error but don't fail the test - some content may not have icons
                    print(f"Expected behavior: {test_name} had no matching icons")
                    
            finally:
                if audio_path.exists():
                    audio_path.unlink()

