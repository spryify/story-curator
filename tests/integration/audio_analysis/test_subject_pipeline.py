"""Integration tests for audio subject identification."""
import pytest
from pathlib import Path

from media_analyzer.core.analyzer import AudioAnalyzer
from media_analyzer.processors.audio.processor import AudioProcessor
from media_analyzer.processors.subject.identifier import SubjectIdentifier

@pytest.fixture
def audio_file_path(tmp_path) -> Path:
    """Create a temporary audio file for testing."""
    # This would be handled by a proper audio file fixture
    return tmp_path / "test_audio.wav"

@pytest.fixture
def audio_analyzer():
    """Create an AudioAnalyzer instance."""
    return AudioAnalyzer()

class TestAudioSubjectIntegration:
    """Integration test suite for audio subject identification."""
    
    def test_audio_to_subjects_pipeline(self, audio_analyzer, audio_file_path):
        """Test the complete pipeline from audio to subject identification."""
        # Process audio file
        audio_result = audio_analyzer.process_audio(audio_file_path)
        assert audio_result.text is not None
        
        # Identify subjects
        subject_identifier = SubjectIdentifier()
        subject_result = subject_identifier.identify_subjects(audio_result.text)
        
        # Verify complete pipeline
        assert subject_result.subjects is not None
        assert len(subject_result.subjects) > 0
        assert subject_result.categories is not None
        assert "processing_time_ms" in subject_result.metadata
        
    def test_performance_full_pipeline(self, audio_analyzer, audio_file_path):
        """Test performance of the complete pipeline."""
        import time
        
        start_time = time.time()
        
        # Process audio
        audio_result = audio_analyzer.process_audio(audio_file_path)
        
        # Identify subjects
        subject_identifier = SubjectIdentifier()
        subject_result = subject_identifier.identify_subjects(audio_result.text)
        
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Full pipeline should complete within reasonable time
        # Note: Audio processing might take longer, subject ID should be < 500ms
        subject_processing_time = subject_result.metadata["processing_time_ms"]
        assert subject_processing_time < 500
        
    def test_error_propagation(self, audio_analyzer, audio_file_path):
        """Test error handling across the pipeline."""
        # Test with invalid audio file
        with pytest.raises(Exception) as exc_info:
            audio_result = audio_analyzer.process_audio(Path("nonexistent.wav"))
        
        # Test with invalid text
        subject_identifier = SubjectIdentifier()
        with pytest.raises(Exception) as exc_info:
            subject_identifier.identify_subjects("")
            
    def test_context_preservation(self, audio_analyzer, audio_file_path):
        """Test that context is preserved throughout the pipeline."""
        from media_analyzer.processors.subject.models import Context
        
        # Process audio with context
        context = Context(
            domain="technology",
            language="en",
            confidence=1.0
        )
        
        audio_result = audio_analyzer.process_audio(
            audio_file_path, 
            {"domain": "technology"}
        )
        
        # Identify subjects with same context
        subject_identifier = SubjectIdentifier()
        subject_result = subject_identifier.identify_subjects(
            audio_result.text,
            context
        )
        
        # Verify context was preserved
        assert all(s.context.domain == "technology" for s in subject_result.subjects)
        
    def test_metadata_aggregation(self, audio_analyzer, audio_file_path):
        """Test that metadata is properly aggregated through the pipeline."""
        # Process audio
        audio_result = audio_analyzer.process_audio(audio_file_path)
        
        # Identify subjects
        subject_identifier = SubjectIdentifier()
        subject_result = subject_identifier.identify_subjects(audio_result.text)
        
        # Verify metadata from both stages
        assert "audio_processing" in subject_result.metadata
        assert "subject_identification" in subject_result.metadata
        assert "processing_time_ms" in subject_result.metadata
