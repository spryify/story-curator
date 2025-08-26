"""Simplified integration tests for core functionality."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .test_models import TestBase, TestIconModel
from src.icon_curator.models.icon import IconData
from src.icon_curator.core.exceptions import ValidationError


@pytest.fixture(scope="function")
def test_db_session():
    """Create an in-memory SQLite database for testing."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestBase.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestIconCuratorBasicFunctionality:
    """Basic integration tests for icon curator functionality."""
    
    def test_icon_data_creation(self):
        """Test creating IconData objects."""
        icon = IconData(
            name="Test Icon",
            url="https://yotoicons.com/test",
            image_url="https://yotoicons.com/test.svg",
            tags=["test"],
            description="A test icon",
            category="Testing"
        )
        
        assert icon.name == "Test Icon"
        assert icon.url == "https://yotoicons.com/test"
        assert icon.image_url == "https://yotoicons.com/test.svg"
        assert icon.tags == ["test"]
        assert icon.description == "A test icon"
        assert icon.category == "Testing"
        assert isinstance(icon.created_at, datetime)
        assert isinstance(icon.updated_at, datetime)
        assert icon.metadata == {}
    
    def test_test_model_creation(self, test_db_session):
        """Test creating and saving test icon models."""
        model = TestIconModel(
            name="Test Icon Model",
            url="https://example.com/test",
            image_url="https://example.com/test.svg",
            tags="test,example",
            description="Test model",
            category="Testing"
        )
        
        test_db_session.add(model)
        test_db_session.commit()
        
        # Query back from database
        saved_model = test_db_session.query(TestIconModel).filter_by(name="Test Icon Model").first()
        
        assert saved_model is not None
        assert saved_model.name == "Test Icon Model"
        assert saved_model.url == "https://example.com/test"
        assert saved_model.image_url == "https://example.com/test.svg"
        assert saved_model.tags == "test,example"
        assert saved_model.description == "Test model"
        assert saved_model.category == "Testing"
        assert saved_model.id is not None
        assert saved_model.created_at is not None
    
    def test_model_search_functionality(self, test_db_session):
        """Test basic search functionality."""
        # Create multiple test icons
        icons = [
            TestIconModel(
                name="Animal Icon",
                url="https://example.com/animal",
                image_url="https://example.com/animal.svg",
                tags="animal,cute",
                category="Animals"
            ),
            TestIconModel(
                name="Plant Icon",
                url="https://example.com/plant",
                image_url="https://example.com/plant.svg",
                tags="plant,nature",
                category="Nature"
            ),
            TestIconModel(
                name="Car Icon",
                url="https://example.com/car",
                image_url="https://example.com/car.svg",
                tags="car,vehicle",
                category="Transport"
            )
        ]
        
        for icon in icons:
            test_db_session.add(icon)
        test_db_session.commit()
        
        # Test search by name
        animal_results = test_db_session.query(TestIconModel).filter(
            TestIconModel.name.like("%Animal%")
        ).all()
        assert len(animal_results) == 1
        assert animal_results[0].name == "Animal Icon"
        
        # Test search by category
        nature_results = test_db_session.query(TestIconModel).filter(
            TestIconModel.category == "Nature"
        ).all()
        assert len(nature_results) == 1
        assert nature_results[0].name == "Plant Icon"
        
        # Test count
        total_count = test_db_session.query(TestIconModel).count()
        assert total_count == 3
