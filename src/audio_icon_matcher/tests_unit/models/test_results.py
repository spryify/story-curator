"""Tests for results models."""

import pytest
from unittest.mock import Mock

from audio_icon_matcher.models.results import IconMatch, AudioIconResult
from icon_extractor.models.icon import IconData


class TestIconMatch:
    """Test suite for IconMatch model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.icon_data = IconData(
            name="Test Icon",
            url="https://example.com/test.png",
            tags=["test"],
            description="Test description"
        )
    
    def test_icon_match_creation(self):
        """Test creating an IconMatch instance."""
        match = IconMatch(
            icon=self.icon_data,
            confidence=0.85,
            match_reason="Keyword match: test",
            subjects_matched=["test", "keyword"]
        )
        
        assert match.icon == self.icon_data
        assert match.confidence == 0.85
        assert match.match_reason == "Keyword match: test"
        assert match.subjects_matched == ["test", "keyword"]
    
    def test_icon_match_with_empty_subjects(self):
        """Test creating IconMatch with empty subjects list."""
        match = IconMatch(
            icon=self.icon_data,
            confidence=0.5,
            match_reason="Basic match",
            subjects_matched=[]
        )
        
        assert match.icon == self.icon_data
        assert match.confidence == 0.5
        assert match.match_reason == "Basic match"
        assert match.subjects_matched == []
    
    def test_icon_match_confidence_validation(self):
        """Test confidence value validation."""
        # Valid confidence values
        match1 = IconMatch(icon=self.icon_data, confidence=0.0, match_reason="Zero", subjects_matched=[])
        match2 = IconMatch(icon=self.icon_data, confidence=1.0, match_reason="One", subjects_matched=[])
        match3 = IconMatch(icon=self.icon_data, confidence=0.5, match_reason="Half", subjects_matched=[])
        
        assert match1.confidence == 0.0
        assert match2.confidence == 1.0
        assert match3.confidence == 0.5
    
    def test_icon_match_equality(self):
        """Test IconMatch equality comparison."""
        match1 = IconMatch(
            icon=self.icon_data,
            confidence=0.8,
            match_reason="test",
            subjects_matched=["test"]
        )
        
        match2 = IconMatch(
            icon=self.icon_data,
            confidence=0.8,
            match_reason="test",
            subjects_matched=["test"]
        )
        
        match3 = IconMatch(
            icon=self.icon_data,
            confidence=0.9,  # Different confidence
            match_reason="test",
            subjects_matched=["test"]
        )
        
        assert match1 == match2
        assert match1 != match3
    
    def test_icon_match_with_multiple_subjects(self):
        """Test IconMatch with multiple matched subjects."""
        match = IconMatch(
            icon=self.icon_data,
            confidence=0.9,
            match_reason="Multiple matches",
            subjects_matched=["keyword1", "keyword2", "entity1"]
        )
        
        assert len(match.subjects_matched) == 3
        assert "keyword1" in match.subjects_matched
        assert "keyword2" in match.subjects_matched
        assert "entity1" in match.subjects_matched
    
    def test_icon_match_confidence_edge_cases(self):
        """Test IconMatch with edge case confidence values."""
        # Very low confidence
        low_match = IconMatch(
            icon=self.icon_data,
            confidence=0.001,
            match_reason="Very low match",
            subjects_matched=[]
        )
        assert low_match.confidence == 0.001
        
        # Very high confidence  
        high_match = IconMatch(
            icon=self.icon_data,
            confidence=0.999,
            match_reason="Very high match",
            subjects_matched=[]
        )
        assert high_match.confidence == 0.999
    
    def test_icon_match_complex_match_reason(self):
        """Test IconMatch with complex match reason."""
        complex_reason = "Keyword match: 'artificial intelligence' (0.9), Tag match: 'AI' (0.8), Description boost: +0.1"
        
        match = IconMatch(
            icon=self.icon_data,
            confidence=0.95,
            match_reason=complex_reason,
            subjects_matched=["artificial intelligence", "AI"]
        )
        
        assert match.match_reason == complex_reason
        assert len(match.subjects_matched) == 2


class TestAudioIconResult:
    """Test suite for AudioIconResult model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.icon_data = IconData(
            name="Result Icon",
            url="https://example.com/result.png",
            tags=["test"]
        )
        
        self.icon_match = IconMatch(
            icon=self.icon_data,
            confidence=0.8,
            match_reason="Test match",
            subjects_matched=["test"]
        )
    
    def test_audio_icon_result_success(self):
        """Test creating successful AudioIconResult."""
        result = AudioIconResult(
            success=True,
            transcription="This is a test transcription",
            transcription_confidence=0.95,
            subjects={"keywords": [{"name": "test", "confidence": 0.9}]},
            icon_matches=[self.icon_match],
            processing_time=1.25,
            metadata={"source": "test"}
        )
        
        assert result.success is True
        assert result.transcription == "This is a test transcription"
        assert result.transcription_confidence == 0.95
        assert "keywords" in result.subjects
        assert len(result.icon_matches) == 1
        assert result.processing_time == 1.25
        assert result.metadata["source"] == "test"
        assert result.error is None
    
    def test_audio_icon_result_failure(self):
        """Test creating failed AudioIconResult."""
        result = AudioIconResult(
            success=False,
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=0.5,
            metadata={},
            error="Transcription failed"
        )
        
        assert result.success is False
        assert result.transcription == ""
        assert result.transcription_confidence == 0.0
        assert result.subjects == {}
        assert result.icon_matches == []
        assert result.processing_time == 0.5
        assert result.metadata == {}
        assert result.error == "Transcription failed"
    
    def test_audio_icon_result_partial_success(self):
        """Test AudioIconResult with partial success (transcription but no matches)."""
        result = AudioIconResult(
            success=True,
            transcription="No matching icons found",
            transcription_confidence=0.8,
            subjects={"keywords": [{"name": "unmatchable", "confidence": 0.7}]},
            icon_matches=[],
            processing_time=2.1,
            metadata={"attempts": 3}
        )
        
        assert result.success is True
        assert result.transcription == "No matching icons found"
        assert len(result.icon_matches) == 0
        assert result.subjects["keywords"][0]["name"] == "unmatchable"
        assert result.metadata["attempts"] == 3
    
    def test_audio_icon_result_multiple_matches(self):
        """Test AudioIconResult with multiple icon matches."""
        icon_data2 = IconData(
            name="Second Icon",
            url="https://example.com/second.png",
            tags=["test"]
        )
        
        match2 = IconMatch(
            icon=icon_data2,
            confidence=0.6,
            match_reason="Secondary match",
            subjects_matched=["test"]
        )
        
        result = AudioIconResult(
            success=True,
            transcription="Multiple icons found",
            transcription_confidence=0.9,
            subjects={"keywords": [{"name": "test", "confidence": 0.85}]},
            icon_matches=[self.icon_match, match2],
            processing_time=3.0,
            metadata={"total_icons_searched": 1000}
        )
        
        assert len(result.icon_matches) == 2
        assert result.icon_matches[0] == self.icon_match
        assert result.icon_matches[1] == match2
        assert result.metadata["total_icons_searched"] == 1000
    
    def test_audio_icon_result_equality(self):
        """Test AudioIconResult equality comparison."""
        result1 = AudioIconResult(
            success=True,
            transcription="test",
            transcription_confidence=0.8,
            subjects={},
            icon_matches=[],
            processing_time=1.0,
            metadata={}
        )
        
        result2 = AudioIconResult(
            success=True,
            transcription="test",
            transcription_confidence=0.8,
            subjects={},
            icon_matches=[],
            processing_time=1.0,
            metadata={}
        )
        
        result3 = AudioIconResult(
            success=False,  # Different success status
            transcription="test",
            transcription_confidence=0.8,
            subjects={},
            icon_matches=[],
            processing_time=1.0,
            metadata={}
        )
        
        assert result1 == result2
        assert result1 != result3
    
    def test_audio_icon_result_with_error_details(self):
        """Test AudioIconResult with detailed error information."""
        result = AudioIconResult(
            success=False,
            transcription="",
            transcription_confidence=0.0,
            subjects={},
            icon_matches=[],
            processing_time=0.1,
            metadata={"error_stage": "transcription"},
            error="Audio file format not supported: .xyz"
        )
        
        assert result.success is False
        assert result.error == "Audio file format not supported: .xyz"
        assert result.metadata["error_stage"] == "transcription"
        assert result.processing_time == 0.1
