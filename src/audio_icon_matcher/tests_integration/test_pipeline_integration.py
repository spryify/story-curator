"""Integration tests for AudioIconPipeline."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from audio_icon_matcher.core.pipeline import AudioIconPipeline
from audio_icon_matcher.models.results import AudioIconResult, IconMatch
from audio_icon_matcher.core.exceptions import AudioIconValidationError, AudioIconProcessingError


class TestAudioIconPipelineIntegration:
    """Integration tests for the AudioIconPipeline."""
    
    def test_pipeline_with_real_components_mock_dependencies(self):
        """Test pipeline with real components but mocked external dependencies."""
        # Mock external dependencies
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
             patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
             patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
            
            # Set up mocks
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.return_value = Path("/test/audio.wav")
            mock_audio.extract_text.return_value = Mock(
                text="This is a test about cats and music",
                language="en",
                confidence=0.9
            )
            mock_audio_class.return_value = mock_audio
            
            mock_subject = Mock()
            mock_subject_result = Mock()
            mock_subject_result.subjects = set()
            mock_subject_result.categories = set()
            mock_subject_result.metadata = {}
            mock_subject.identify_subjects.return_value = mock_subject_result
            mock_subject_class.return_value = mock_subject
            
            mock_icon_service = Mock()
            mock_icon_service.search_icons.return_value = []
            mock_icon_service_class.return_value = mock_icon_service
            
            # Create pipeline
            pipeline = AudioIconPipeline()
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                result = pipeline.process(temp_path)
                
                # Verify the result structure
                assert isinstance(result, AudioIconResult)
                assert result.success is True
                assert result.transcription is not None
                assert result.processing_time > 0
                
                # Verify that all components were called
                mock_audio.validate_file.assert_called_once()
                mock_audio.extract_text.assert_called_once()
                mock_subject.identify_subjects.assert_called_once()
                
            finally:
                os.unlink(temp_path)
    
    def test_pipeline_error_propagation(self):
        """Test that errors propagate correctly through the pipeline."""
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class:
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.side_effect = ValueError("Invalid audio format")
            mock_audio_class.return_value = mock_audio
            
            pipeline = AudioIconPipeline()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                with pytest.raises(AudioIconValidationError):
                    pipeline.process(temp_path)
            finally:
                os.unlink(temp_path)
    
    def test_pipeline_with_different_audio_formats(self):
        """Test pipeline with different supported audio formats."""
        formats_to_test = [".wav", ".mp3", ".m4a"]
        
        for audio_format in formats_to_test:
            with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
                 patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
                 patch('icon_extractor.core.service.IconExtractionService'):
                
                # Set up mocks
                mock_audio = Mock()
                mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
                mock_audio.validate_file.return_value = Path(f"/test/audio{audio_format}")
                mock_audio.extract_text.return_value = Mock(
                    text="Test audio content",
                    language="en",
                    confidence=0.8
                )
                mock_audio_class.return_value = mock_audio
                
                mock_subject = Mock()
                mock_subject_result = Mock()
                mock_subject_result.subjects = set()
                mock_subject_result.categories = set()
                mock_subject_result.metadata = {}
                mock_subject.identify_subjects.return_value = mock_subject_result
                mock_subject_class.return_value = mock_subject
                
                pipeline = AudioIconPipeline()
                
                with tempfile.NamedTemporaryFile(suffix=audio_format, delete=False) as f:
                    temp_path = f.name
                
                try:
                    result = pipeline.process(temp_path)
                    assert result.success is True
                    assert result.transcription == "Test audio content"
                finally:
                    os.unlink(temp_path)
    
    def test_end_to_end_with_mocked_database(self):
        """Test end-to-end pipeline with mocked database interactions."""
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
             patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
             patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
            
            # Set up audio processor mock
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.return_value = Path("/test/audio.wav")
            mock_audio.extract_text.return_value = Mock(
                text="I love my pet cat, she's adorable",
                language="en",
                confidence=0.95
            )
            mock_audio_class.return_value = mock_audio
            
            # Set up subject identifier mock
            mock_subject = Mock()
            mock_subject_result = Mock()
            
            # Mock subjects
            mock_cat_subject = Mock()
            mock_cat_subject.name = "cat"
            mock_cat_subject.confidence = 0.9
            mock_cat_subject.subject_type.value = "KEYWORD"
            
            mock_pet_subject = Mock()
            mock_pet_subject.name = "pet"
            mock_pet_subject.confidence = 0.8
            mock_pet_subject.subject_type.value = "TOPIC"
            
            mock_subject_result.subjects = {mock_cat_subject, mock_pet_subject}
            mock_subject_result.categories = set()
            mock_subject_result.metadata = {"processing_time_ms": 150}
            mock_subject.identify_subjects.return_value = mock_subject_result
            mock_subject_class.return_value = mock_subject
            
            # Set up icon service mock
            mock_icon_service = Mock()
            mock_cat_icon = Mock()
            mock_cat_icon.name = "Cute Cat Icon"
            mock_cat_icon.url = "https://icons.example.com/cat.svg"
            mock_cat_icon.tags = ["animal", "pet", "cat"]
            mock_cat_icon.category = "Animals"
            mock_cat_icon.description = "A cute cat icon"
            
            mock_pet_icon = Mock()
            mock_pet_icon.name = "Pet Icon"
            mock_pet_icon.url = "https://icons.example.com/pet.svg"
            mock_pet_icon.tags = ["pet", "care"]
            mock_pet_icon.category = "Animals"
            mock_pet_icon.description = "General pet icon"
            
            mock_icon_service.search_icons.side_effect = [
                [mock_cat_icon],  # First call for "cat"
                [mock_pet_icon],  # Second call for "pet"
                [],               # Additional calls return empty
                []
            ]
            mock_icon_service_class.return_value = mock_icon_service
            
            # Create and run pipeline
            pipeline = AudioIconPipeline()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                result = pipeline.process(temp_path, max_icons=5, confidence_threshold=0.3)
                
                # Verify the complete result
                assert result.success is True
                assert result.transcription == "I love my pet cat, she's adorable"
                assert result.transcription_confidence == 0.95
                assert len(result.icon_matches) > 0
                
                # Check that we got icon matches
                icon_names = [match.icon.name for match in result.icon_matches]
                assert "Cute Cat Icon" in icon_names or "Pet Icon" in icon_names
                
                # Verify subjects were extracted
                assert 'keywords' in result.subjects or 'topics' in result.subjects
                
                # Verify processing metadata
                assert result.processing_time > 0
                assert 'subjects_found' in result.metadata
                assert 'icons_found' in result.metadata
                
            finally:
                os.unlink(temp_path)
    
    def test_performance_with_large_subject_set(self):
        """Test pipeline performance with a large number of subjects."""
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
             patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
             patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
            
            # Create a large set of mock subjects
            mock_subjects = set()
            for i in range(50):  # 50 subjects
                mock_subject = Mock()
                mock_subject.name = f"subject_{i}"
                mock_subject.confidence = 0.5 + (i % 50) / 100  # Varying confidence
                mock_subject.subject_type.value = "KEYWORD" if i % 2 == 0 else "TOPIC"
                mock_subjects.add(mock_subject)
            
            # Set up mocks
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.return_value = Path("/test/audio.wav")
            mock_audio.extract_text.return_value = Mock(
                text="Long audio content with many subjects...",
                language="en",
                confidence=0.85
            )
            mock_audio_class.return_value = mock_audio
            
            mock_subject = Mock()
            mock_subject_result = Mock()
            mock_subject_result.subjects = mock_subjects
            mock_subject_result.categories = set()
            mock_subject_result.metadata = {"processing_time_ms": 500}
            mock_subject.identify_subjects.return_value = mock_subject_result
            mock_subject_class.return_value = mock_subject
            
            mock_icon_service = Mock()
            mock_icon_service.search_icons.return_value = []  # No icons for simplicity
            mock_icon_service_class.return_value = mock_icon_service
            
            pipeline = AudioIconPipeline()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                import time
                start_time = time.time()
                result = pipeline.process(temp_path, max_icons=10)
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                # Verify it completes in reasonable time (less than 5 seconds for 50 subjects)
                assert processing_time < 5.0
                assert result.success is True
                assert result.metadata['subjects_found'] == 50
                
            finally:
                os.unlink(temp_path)
    
    def test_concurrent_pipeline_usage(self):
        """Test that multiple pipelines can run concurrently."""
        import threading
        import time
        
        results = []
        errors = []
        
        def run_pipeline():
            try:
                with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
                     patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
                     patch('icon_extractor.core.service.IconExtractionService'):
                    
                    # Set up mocks
                    mock_audio = Mock()
                    mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
                    mock_audio.validate_file.return_value = Path("/test/audio.wav")
                    mock_audio.extract_text.return_value = Mock(
                        text="Concurrent test audio",
                        language="en",
                        confidence=0.8
                    )
                    mock_audio_class.return_value = mock_audio
                    
                    mock_subject = Mock()
                    mock_subject_result = Mock()
                    mock_subject_result.subjects = set()
                    mock_subject_result.categories = set()
                    mock_subject_result.metadata = {}
                    mock_subject.identify_subjects.return_value = mock_subject_result
                    mock_subject_class.return_value = mock_subject
                    
                    pipeline = AudioIconPipeline()
                    
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        temp_path = f.name
                    
                    try:
                        result = pipeline.process(temp_path)
                        results.append(result)
                    finally:
                        os.unlink(temp_path)
                        
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(3):  # 3 concurrent pipelines
            thread = threading.Thread(target=run_pipeline)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        for result in results:
            assert result.success is True
            assert result.transcription == "Concurrent test audio"


class TestPipelineRealWorldScenarios:
    """Test pipeline with realistic scenarios."""
    
    def test_music_description_scenario(self):
        """Test pipeline with music-related audio description."""
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
             patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
             patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
            
            # Set up realistic music scenario
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.return_value = Path("/test/music.mp3")
            mock_audio.extract_text.return_value = Mock(
                text="This is a beautiful jazz piano composition with smooth saxophone melodies",
                language="en",
                confidence=0.92
            )
            mock_audio_class.return_value = mock_audio
            
            # Mock music-related subjects
            jazz_subject = Mock()
            jazz_subject.name = "jazz"
            jazz_subject.confidence = 0.9
            jazz_subject.subject_type.value = "KEYWORD"
            
            piano_subject = Mock()
            piano_subject.name = "piano"
            piano_subject.confidence = 0.85
            piano_subject.subject_type.value = "KEYWORD"
            
            music_subject = Mock()
            music_subject.name = "music"
            music_subject.confidence = 0.8
            music_subject.subject_type.value = "TOPIC"
            
            mock_subject = Mock()
            mock_subject_result = Mock()
            mock_subject_result.subjects = {jazz_subject, piano_subject, music_subject}
            mock_subject_result.categories = set()
            mock_subject_result.metadata = {"processing_time_ms": 200}
            mock_subject.identify_subjects.return_value = mock_subject_result
            mock_subject_class.return_value = mock_subject
            
            # Mock music-related icons
            piano_icon = Mock()
            piano_icon.name = "Piano Icon"
            piano_icon.url = "https://icons.example.com/piano.svg"
            piano_icon.tags = ["instrument", "music", "piano"]
            piano_icon.category = "Music"
            
            jazz_icon = Mock()
            jazz_icon.name = "Jazz Music Icon"
            jazz_icon.url = "https://icons.example.com/jazz.svg"
            jazz_icon.tags = ["jazz", "music", "genre"]
            jazz_icon.category = "Music"
            
            mock_icon_service = Mock()
            mock_icon_service.search_icons.side_effect = [
                [jazz_icon],       # jazz search
                [piano_icon],      # piano search
                [jazz_icon, piano_icon],  # music search
                []
            ]
            mock_icon_service_class.return_value = mock_icon_service
            
            pipeline = AudioIconPipeline()
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            try:
                result = pipeline.process(temp_path, max_icons=5, confidence_threshold=0.4)
                
                assert result.success is True
                assert "jazz" in result.transcription.lower()
                assert "piano" in result.transcription.lower()
                assert len(result.icon_matches) > 0
                
                # Should find music-related icons
                icon_names = [match.icon.name for match in result.icon_matches]
                assert any("Piano" in name or "Jazz" in name for name in icon_names)
                
            finally:
                os.unlink(temp_path)
    
    def test_nature_sounds_scenario(self):
        """Test pipeline with nature sounds description."""
        with patch('media_analyzer.processors.audio.audio_processor.AudioProcessor') as mock_audio_class, \
             patch('media_analyzer.processors.subject.subject_identifier.SubjectIdentifier') as mock_subject_class, \
             patch('icon_extractor.core.service.IconExtractionService') as mock_icon_service_class:
            
            mock_audio = Mock()
            mock_audio.SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}
            mock_audio.validate_file.return_value = Path("/test/nature.wav")
            mock_audio.extract_text.return_value = Mock(
                text="Birds singing in the forest with flowing water from a nearby stream",
                language="en",
                confidence=0.88
            )
            mock_audio_class.return_value = mock_audio
            
            # Mock nature-related subjects
            birds_subject = Mock()
            birds_subject.name = "birds"
            birds_subject.confidence = 0.9
            birds_subject.subject_type.value = "KEYWORD"
            
            forest_subject = Mock()
            forest_subject.name = "forest"
            forest_subject.confidence = 0.85
            forest_subject.subject_type.value = "KEYWORD"
            
            water_subject = Mock()
            water_subject.name = "water"
            water_subject.confidence = 0.8
            water_subject.subject_type.value = "KEYWORD"
            
            nature_subject = Mock()
            nature_subject.name = "nature"
            nature_subject.confidence = 0.75
            nature_subject.subject_type.value = "TOPIC"
            
            mock_subject = Mock()
            mock_subject_result = Mock()
            mock_subject_result.subjects = {birds_subject, forest_subject, water_subject, nature_subject}
            mock_subject_result.categories = set()
            mock_subject_result.metadata = {"processing_time_ms": 180}
            mock_subject.identify_subjects.return_value = mock_subject_result
            mock_subject_class.return_value = mock_subject
            
            # Mock nature-related icons
            bird_icon = Mock()
            bird_icon.name = "Bird Icon"
            bird_icon.url = "https://icons.example.com/bird.svg"
            bird_icon.tags = ["bird", "animal", "nature"]
            bird_icon.category = "Animals"
            
            tree_icon = Mock()
            tree_icon.name = "Forest Tree Icon"
            tree_icon.url = "https://icons.example.com/tree.svg"
            tree_icon.tags = ["tree", "forest", "nature"]
            tree_icon.category = "Nature"
            
            mock_icon_service = Mock()
            mock_icon_service.search_icons.side_effect = [
                [bird_icon],      # birds search
                [tree_icon],      # forest search
                [],               # water search (no results)
                [bird_icon, tree_icon]  # nature search
            ]
            mock_icon_service_class.return_value = mock_icon_service
            
            pipeline = AudioIconPipeline()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                result = pipeline.process(temp_path, max_icons=10, confidence_threshold=0.3)
                
                assert result.success is True
                assert len(result.icon_matches) > 0
                
                # Should have nature-related matches
                match_reasons = [match.match_reason for match in result.icon_matches]
                subjects_matched = []
                for match in result.icon_matches:
                    subjects_matched.extend(match.subjects_matched)
                
                assert any("birds" in subject or "forest" in subject or "nature" in subject 
                          for subject in subjects_matched)
                
            finally:
                os.unlink(temp_path)
