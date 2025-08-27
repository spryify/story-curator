"""Unit tests for database models."""

import pytest
from datetime import datetime

from src.icon_curator.database.models import IconModel


class TestIconModel:
    """Test cases for IconModel."""
    
    def test_icon_model_creation(self):
        """Test creating an IconModel instance."""
        model = IconModel(
            name="Test Icon",
            url="https://example.com/test.svg",
            tags=["test", "example"],
            description="A test icon",
            category="Testing",
            metadata={"source": "test"}
        )
        
        assert model.name == "Test Icon"
        assert model.url == "https://example.com/test.svg"
        assert model.tags == ["test", "example"]
        assert model.description == "A test icon"
        assert model.category == "Testing"
        assert model.metadata == {"source": "test"}
        assert model.id is None  # Not set until saved
    
    def test_icon_model_repr(self):
        """Test IconModel string representation."""
        model = IconModel(
            id=1,
            name="Test Icon",
            url="https://example.com/test.svg",
            tags=["test"],
            category="Testing"
        )
        
        repr_str = repr(model)
        assert "IconModel" in repr_str
        assert "id=1" in repr_str
        assert "Test Icon" in repr_str
        assert "Testing" in repr_str
    
    def test_icon_model_defaults(self):
        """Test IconModel with default values."""
        model = IconModel(
            name="Minimal Icon",
            url="https://example.com/minimal.svg"
        )
        
        assert model.name == "Minimal Icon"
        assert model.url == "https://example.com/minimal.svg"
        assert model.tags == []  # Default empty list
        assert model.description is None
        assert model.category is None
        assert model.icon_metadata == {}  # Default empty dict
        assert model.created_at is None  # Will be set by database
        assert model.updated_at is None  # Will be set by database
    
    def test_icon_model_table_name(self):
        """Test that the table name is correctly set."""
        assert IconModel.__tablename__ == "icons"
