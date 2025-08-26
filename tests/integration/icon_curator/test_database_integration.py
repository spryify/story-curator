"""Integration tests for database repository."""

import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.icon_curator.database.models import Base, IconModel
from src.icon_curator.database.repository import IconRepository
from src.icon_curator.models.icon import IconData
from src.icon_curator.core.exceptions import DatabaseError, ValidationError


@pytest.fixture(scope="function")
def test_db_session():
    """Create an in-memory SQLite database for testing."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def repository(test_db_session):
    """Create a repository instance with test database session."""
    return IconRepository(session=test_db_session)


@pytest.fixture
def sample_icon_data():
    """Create sample icon data for testing."""
    return IconData(
        name="Test Icon",
        url="https://yotoicons.com/test-icon",
        image_url="https://yotoicons.com/images/test-icon.svg",
        tags=["test", "sample"],
        description="A test icon for unit tests",
        category="Testing",
        metadata={"source": "test"}
    )


class TestIconRepository:
    """Integration tests for IconRepository."""
    
    def test_save_new_icon(self, repository, sample_icon_data):
        """Test saving a new icon to the database."""
        result = repository.save_icon(sample_icon_data)
        
        assert result.id is not None
        assert result.name == sample_icon_data.name
        assert result.url == sample_icon_data.url
        assert result.image_url == sample_icon_data.image_url
        assert result.tags == sample_icon_data.tags
        assert result.description == sample_icon_data.description
        assert result.category == sample_icon_data.category
        assert result.metadata == sample_icon_data.metadata
        assert result.created_at is not None
        assert result.updated_at is not None
    
    def test_save_icon_validation_error(self, repository):
        """Test that saving invalid icon data raises ValidationError."""
        # Missing required fields
        invalid_icon = IconData(
            name="",  # Empty name
            url="https://example.com/test",
            image_url="",  # Empty image URL
            tags=[]
        )
        
        with pytest.raises(ValidationError):
            repository.save_icon(invalid_icon)
    
    def test_update_existing_icon(self, repository, sample_icon_data):
        """Test updating an existing icon."""
        # Save original icon
        original = repository.save_icon(sample_icon_data)
        original_updated_at = original.updated_at
        
        # Update the icon data
        sample_icon_data.description = "Updated description"
        sample_icon_data.tags = ["updated", "test"]
        
        # Save updated icon (same URL)
        updated = repository.save_icon(sample_icon_data)
        
        # Should be the same record
        assert updated.id == original.id
        assert updated.description == "Updated description"
        assert updated.tags == ["updated", "test"]
        assert updated.updated_at > original_updated_at
    
    def test_get_icon_by_id(self, repository, sample_icon_data):
        """Test retrieving icon by ID."""
        saved = repository.save_icon(sample_icon_data)
        
        retrieved = repository.get_icon_by_id(saved.id)
        
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.name == saved.name
        assert retrieved.url == saved.url
    
    def test_get_icon_by_id_not_found(self, repository):
        """Test retrieving non-existent icon by ID."""
        result = repository.get_icon_by_id(999)
        assert result is None
    
    def test_get_icon_by_url(self, repository, sample_icon_data):
        """Test retrieving icon by URL."""
        saved = repository.save_icon(sample_icon_data)
        
        retrieved = repository.get_icon_by_url(sample_icon_data.url)
        
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.url == sample_icon_data.url
    
    def test_get_icon_by_url_not_found(self, repository):
        """Test retrieving non-existent icon by URL."""
        result = repository.get_icon_by_url("https://example.com/not-found")
        assert result is None
    
    def test_search_icons_by_name(self, repository, sample_icon_data):
        """Test searching icons by name."""
        repository.save_icon(sample_icon_data)
        
        results = repository.search_icons(query="Test")
        
        assert len(results) == 1
        assert results[0].name == sample_icon_data.name
    
    def test_search_icons_by_description(self, repository, sample_icon_data):
        """Test searching icons by description."""
        repository.save_icon(sample_icon_data)
        
        results = repository.search_icons(query="unit tests")
        
        assert len(results) == 1
        assert results[0].description == sample_icon_data.description
    
    def test_search_icons_by_category(self, repository, sample_icon_data):
        """Test searching icons by category."""
        repository.save_icon(sample_icon_data)
        
        results = repository.search_icons(query="", category="Testing")
        
        assert len(results) == 1
        assert results[0].category == "Testing"
    
    def test_search_icons_no_results(self, repository, sample_icon_data):
        """Test search with no matching results."""
        repository.save_icon(sample_icon_data)
        
        results = repository.search_icons(query="nonexistent")
        
        assert len(results) == 0
    
    def test_search_icons_with_limit(self, repository):
        """Test search with result limit."""
        # Create multiple icons
        for i in range(10):
            icon_data = IconData(
                name=f"Icon {i}",
                url=f"https://example.com/icon-{i}",
                image_url=f"https://example.com/icon-{i}.svg",
                tags=["test"],
                description="Search test icon"
            )
            repository.save_icon(icon_data)
        
        results = repository.search_icons(query="Icon", limit=5)
        
        assert len(results) == 5
    
    def test_get_icon_count(self, repository, sample_icon_data):
        """Test getting total icon count."""
        assert repository.get_icon_count() == 0
        
        repository.save_icon(sample_icon_data)
        
        assert repository.get_icon_count() == 1
    
    def test_delete_icon(self, repository, sample_icon_data):
        """Test deleting an icon."""
        saved = repository.save_icon(sample_icon_data)
        
        # Delete the icon
        result = repository.delete_icon(saved.id)
        
        assert result is True
        assert repository.get_icon_by_id(saved.id) is None
    
    def test_delete_icon_not_found(self, repository):
        """Test deleting non-existent icon."""
        result = repository.delete_icon(999)
        assert result is False
    
    def test_get_all_categories(self, repository):
        """Test getting all unique categories."""
        # Create icons with different categories
        for category in ["Animals", "Nature", "Transport"]:
            icon_data = IconData(
                name=f"Icon {category}",
                url=f"https://example.com/{category.lower()}",
                image_url=f"https://example.com/{category.lower()}.svg",
                tags=[],
                category=category
            )
            repository.save_icon(icon_data)
        
        categories = repository.get_all_categories()
        
        assert len(categories) == 3
        assert "Animals" in categories
        assert "Nature" in categories
        assert "Transport" in categories
