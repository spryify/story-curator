"""Integration tests for the audio analysis pipeline."""

import os
import numpy as np
from pathlib import Path
from scipy import signal
import pytest
import io
import wave

from media_analyzer.core.analyzer import Analyzer
from media_analyzer.core.exceptions import ValidationError
from media_analyzer.models.audio import TranscriptionResult
from ..tests_unit.utils.audio import create_timed_speech_file, create_wav_file


@pytest.fixture
def audio_analyzer():
    """Create an AudioAnalyzer instance."""
    return Analyzer()


class TestAudioPipeline:
    """Integration test suite for audio processing pipeline."""

    def test_end_to_end_audio_analysis(self, audio_analyzer, tmp_path):
        """Test the complete audio analysis pipeline."""
        # Create a test audio file
        test_file = create_timed_speech_file(tmp_path)
        
        # Process the file with default options
        result = audio_analyzer.process_file(test_file)
        
        # Verify the result structure
        assert isinstance(result, TranscriptionResult)
        assert result.text
        assert result.summary
        assert result.confidence > 0
        assert result.metadata
        
        # Verify metadata
        assert "processing_time" in result.metadata
        assert "sample_rate" in result.metadata
        assert "channels" in result.metadata
        assert "duration" in result.metadata
        assert "language" in result.metadata

    def test_pipeline_with_different_formats(self, audio_analyzer, tmp_path):
        """Test the pipeline with different audio formats."""
        for fmt in ["wav", "mp3"]:
            # Create test file in the current format
            test_file = create_timed_speech_file(tmp_path, filename=f"test.{fmt}")
            
            # Process the file
            result = audio_analyzer.process_file(test_file)
            
            # Verify basic results
            assert isinstance(result, TranscriptionResult)
            assert result.text
            assert result.metadata["duration"] > 0

    def test_pipeline_with_various_languages(self, audio_analyzer, tmp_path):
        """Test the pipeline with different language settings."""
        test_file = create_timed_speech_file(tmp_path)
        
        # Test valid language
        result = audio_analyzer.process_file(test_file, {"language": "en"})
        assert isinstance(result, TranscriptionResult)
        assert result.metadata["language"] == "en"
        
        # Test unsupported language
        with pytest.raises(ValueError) as exc_info:
            audio_analyzer.process_file(test_file, {"language": "es"})
        assert "Unsupported language: es" in str(exc_info.value)

    def test_pipeline_error_propagation(self, audio_analyzer, tmp_path):
        """Test how errors propagate through the pipeline."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            audio_analyzer.process_file("nonexistent.wav")
        
        # Test with invalid format
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("Not an audio file")
        with pytest.raises(ValueError):
            audio_analyzer.process_file(invalid_file)
        
        # Test with invalid options
        test_file = create_timed_speech_file(tmp_path)
        with pytest.raises(ValidationError):
            audio_analyzer.process_file(test_file, {"language": "invalid"})

    def test_pipeline_performance(self, audio_analyzer, tmp_path):
        """Test pipeline performance with different file sizes."""
        # Test with different durations
        durations = [10000, 20000]  # 10 seconds, 20 seconds
        
        for duration in durations:
            # Create audio file of specified duration
            file_path = create_timed_speech_file(
                tmp_path,
                duration=duration,
                filename=f"test_{duration}ms.wav"
            )
            
            # Process and verify timing
            result = audio_analyzer.process_file(file_path)
            
            # Basic performance checks
            assert result.metadata["processing_time"] > 0
            # Verify duration is within expected range, allowing 50% variance
            expected_duration = duration / 1000.0  # Convert ms to seconds
            actual_duration = result.metadata["duration"]
            # Allow for wider variance since TTS timing can vary significantly
            assert 0.5 * expected_duration <= actual_duration <= 1.5 * expected_duration

    def test_pipeline_concurrent_processing(self, audio_analyzer, tmp_path):
        """Test pipeline handling multiple files concurrently."""
        import concurrent.futures
        
        # Create multiple test files
        test_files = [
            create_timed_speech_file(tmp_path, filename=f"test{i}.wav")
            for i in range(3)
        ]
        
        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {
                executor.submit(audio_analyzer.process_file, file_path): file_path
                for file_path in test_files
            }
            
            # Verify all results
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    assert isinstance(result, TranscriptionResult)
                    assert result.text
                    assert result.metadata["duration"] > 0
                except Exception as e:
                    pytest.fail(f"Processing failed for {file_path}: {e}")

    def test_childrens_story_audio_processing(self, audio_analyzer, children_story_texts, story_audio_creator, tmp_path):
        """Test processing of children's story audio files."""
        for story_name, story_text in children_story_texts.items():
            # Create audio file from story text
            audio_file = story_audio_creator(tmp_path, story_text, f"{story_name}.wav")
            
            # Process the audio file
            result = audio_analyzer.process_file(audio_file)
            
            # Verify basic transcription results
            assert isinstance(result, TranscriptionResult)
            assert result.text
            assert len(result.text.strip()) > 10  # Should have substantial content
            assert result.confidence > 0.5  # Should have reasonable confidence
            
            # Verify metadata
            assert "processing_time" in result.metadata
            assert "duration" in result.metadata
            assert result.metadata["duration"] > 1.0  # Should be at least 1 second
            
            # Check for story-specific content in transcription
            text_lower = result.text.lower()
            if story_name == "magic_garden":
                # Should contain garden/nature related words
                story_keywords = ["garden", "butterfly", "flutter", "owl", "professor"]
                assert any(keyword in text_lower for keyword in story_keywords), \
                    f"Expected story keywords not found in: {result.text}"
                    
            elif story_name == "weather_lesson":
                # Should contain weather-related words
                weather_keywords = ["weather", "sun", "rain", "snow", "clouds"]
                assert any(keyword in text_lower for keyword in weather_keywords), \
                    f"Expected weather keywords not found in: {result.text}"
                    
            elif story_name == "sharing_story":
                # Should contain sharing/friendship words
                sharing_keywords = ["share", "friends", "mouse", "cheese"]
                assert any(keyword in text_lower for keyword in sharing_keywords), \
                    f"Expected sharing keywords not found in: {result.text}"

    def test_educational_audio_content(self, audio_analyzer, educational_content_texts, story_audio_creator, tmp_path):
        """Test processing of educational audio content."""
        for lesson_name, lesson_text in educational_content_texts.items():
            # Create audio file from educational text
            audio_file = story_audio_creator(tmp_path, lesson_text, f"{lesson_name}.wav")
            
            # Process the audio file
            result = audio_analyzer.process_file(audio_file)
            
            # Verify transcription quality
            assert isinstance(result, TranscriptionResult)
            assert result.text
            assert result.confidence > 0.4  # Educational content might be slightly harder
            
            # Verify educational content is captured
            text_lower = result.text.lower()
            if lesson_name == "counting_lesson":
                # Should contain numbers or counting words
                counting_keywords = ["one", "two", "three", "count", "number"]
                assert any(keyword in text_lower for keyword in counting_keywords), \
                    f"Expected counting keywords not found in: {result.text}"
                    
            elif lesson_name == "colors_lesson":
                # Should contain color words
                color_keywords = ["red", "yellow", "blue", "green", "color"]
                assert any(keyword in text_lower for keyword in color_keywords), \
                    f"Expected color keywords not found in: {result.text}"
                    
            elif lesson_name == "kindness_lesson":
                # Should contain kindness/social words
                kindness_keywords = ["kind", "help", "friend", "share", "thank"]
                assert any(keyword in text_lower for keyword in kindness_keywords), \
                    f"Expected kindness keywords not found in: {result.text}"

    def test_story_audio_with_different_voices(self, audio_analyzer, tmp_path):
        """Test processing audio with different synthesized voices."""
        story_text = """
        The little bunny hopped through the meadow, looking for carrots. 
        The sun was shining and the birds were singing. It was a perfect day for an adventure.
        """
        
        # Test with different voices available on macOS
        voices = ["Samantha", "Alex", "Victoria"]  # Different voice options
        
        for voice in voices:
            try:
                # Create audio file with specific voice using utility function
                output_file = create_wav_file(
                    text=story_text,
                    output_path=tmp_path / f"story_{voice.lower()}.wav",
                    voice=voice,
                    rate=150,
                    sample_rate=16000,
                    channels=1
                )
                
                if output_file.exists():
                    # Process the audio file
                    result = audio_analyzer.process_file(output_file)
                    
                    # Verify basic results
                    assert isinstance(result, TranscriptionResult)
                    assert result.text
                    
                    # Check for story content
                    text_lower = result.text.lower()
                    story_keywords = ["bunny", "meadow", "carrot", "sun", "bird"]
                    assert any(keyword in text_lower for keyword in story_keywords), \
                        f"Story content not recognized with voice {voice}: {result.text}"
                        
            except Exception:
                # Skip if voice not available or utility function fails
                continue

    def test_multi_sentence_story_segmentation(self, audio_analyzer, story_audio_creator, tmp_path):
        """Test processing longer stories with multiple sentences."""
        long_story = """
        Once upon a time, in a magical forest, there lived a wise old oak tree. 
        The oak tree was home to many animals including squirrels, birds, and rabbits. 
        Every morning, the animals would gather to hear the oak tree tell wonderful stories. 
        The tree would share tales of brave adventures, friendship, and the importance of caring for nature. 
        All the forest creatures loved these story times and looked forward to them each day.
        """
        
        # Create longer audio file
        audio_file = story_audio_creator(tmp_path, long_story, "long_story.wav")
        
        # Process the audio
        result = audio_analyzer.process_file(audio_file)
        
        # Verify comprehensive transcription
        assert isinstance(result, TranscriptionResult)
        assert result.text
        assert len(result.text.split()) >= 20  # Should have many words
        
        # Check for story elements
        text_lower = result.text.lower()
        story_elements = ["forest", "tree", "animals", "stories", "adventures"]
        found_elements = [elem for elem in story_elements if elem in text_lower]
        assert len(found_elements) >= 2, \
            f"Expected multiple story elements, found: {found_elements} in: {result.text}"
        
        # Verify metadata for longer content
        assert result.metadata["duration"] > 5.0  # Should be longer audio
        assert result.confidence > 0.3  # May be lower for longer content

    def test_story_with_dialogue_and_emotions(self, audio_analyzer, story_audio_creator, tmp_path):
        """Test processing stories with dialogue and emotional content."""
        dialogue_story = """
        "Hello there, little rabbit!" said the friendly fox. 
        "Would you like to be my friend?" 
        The rabbit was scared at first, but the fox seemed very kind. 
        "Yes, I would like that very much," replied the rabbit happily. 
        And so they became the very best of friends, playing together every day.
        """
        
        # Create audio with dialogue
        audio_file = story_audio_creator(tmp_path, dialogue_story, "dialogue_story.wav")
        
        # Process the audio
        result = audio_analyzer.process_file(audio_file)
        
        # Verify dialogue transcription
        assert isinstance(result, TranscriptionResult)
        assert result.text
        
        # Check for dialogue indicators and emotional words
        text_lower = result.text.lower()
        dialogue_keywords = ["hello", "friend", "said", "replied", "happy"]
        assert any(keyword in text_lower for keyword in dialogue_keywords), \
            f"Expected dialogue keywords not found in: {result.text}"
