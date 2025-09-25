"""Real integration tests for database functionality.

These tests use actual database connections and test real integration between
components without mocks.
"""

import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.icon_extractor.models.icon import IconData
from src.icon_extractor.database.models import IconModel, Base
from src.icon_extractor.database.repository import IconRepository
from src.icon_extractor.database.connection import DatabaseManager
from src.icon_extractor.core.exceptions import DatabaseError, ValidationError

# Skip database tests if no test database is available
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:password@localhost:5432/story_curator_test')
SKIP_DB_TESTS = os.getenv('SKIP_DATABASE_TESTS', 'true').lower() == 'true'

pytestmark = pytest.mark.skipif(SKIP_DB_TESTS, reason="Database integration tests require PostgreSQL setup")


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine with cleanup."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup - drop all tables
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session with rollback."""
    TestSession = sessionmaker(bind=test_db_engine)
    session = TestSession()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture  
def icon_repository(test_db_session):
    """Create an IconRepository instance with test database session."""
    return IconRepository(test_db_session)


class TestDatabaseIntegration:
    """Integration tests that use real database connections."""
    
    @pytest.mark.integration
    def test_save_and_retrieve_icon(self, icon_repository, test_db_session):
        """Test saving an icon to database and retrieving it."""
        # Create test icon data
        icon_data = IconData(
            name="Test Integration Icon",
            url="https://example.com/integration-test.svg",
            tags=["integration", "test"],
            description="Icon for integration testing",
            category="Testing"
        )
        
        # Save to database
        saved_icon = icon_repository.save_icon(icon_data)
        test_db_session.commit()
        
        # Verify save
        assert saved_icon.id is not None
        assert saved_icon.name == icon_data.name
        assert saved_icon.url == icon_data.url
        assert saved_icon.tags == icon_data.tags
        
        # Retrieve from database
        retrieved_icon = icon_repository.get_icon_by_id(saved_icon.id)
        
        assert retrieved_icon is not None
        assert retrieved_icon.name == icon_data.name
        assert retrieved_icon.url == icon_data.url
        assert retrieved_icon.tags == icon_data.tags
        assert retrieved_icon.description == icon_data.description
        assert retrieved_icon.category == icon_data.category

    @pytest.mark.integration
    def test_search_icons_integration(self, icon_repository, test_db_session):
        """Test searching for icons in the database."""
        # Create test icons
        icons = [
            IconData(
                name="Cat Icon",
                url="https://example.com/cat.svg", 
                tags=["animal", "pet"],
                category="Animals"
            ),
            IconData(
                name="Dog Icon",
                url="https://example.com/dog.svg",
                tags=["animal", "pet"], 
                category="Animals"
            ),
            IconData(
                name="Tree Icon",
                url="https://example.com/tree.svg",
                tags=["nature", "plant"],
                category="Nature"
            )
        ]
        
        # Save all icons
        for icon in icons:
            icon_repository.save_icon(icon)
        test_db_session.commit()
        
        # Test search by category
        animal_icons = icon_repository.search_icons(category="Animals")
        assert len(animal_icons) == 2
        assert all(icon.category == "Animals" for icon in animal_icons)
        
        # Test search by tags
        pet_icons = icon_repository.search_icons(tags=["pet"])
        assert len(pet_icons) == 2
        assert all("pet" in icon.tags for icon in pet_icons)
        
        # Test search by query
        cat_icons = icon_repository.search_icons(query="Cat")
        assert len(cat_icons) == 1
        assert cat_icons[0].name == "Cat Icon"

    @pytest.mark.integration
    def test_database_url_consistency(self, test_db_session):
        """Test that database correctly stores single URL field (no image_url)."""
        # Create icon directly with database model
        icon_model = IconModel(
            name="URL Consistency Test",
            url="https://example.com/url-consistency.svg",
            tags=["url", "consistency"]
        )
        
        test_db_session.add(icon_model)
        test_db_session.commit()
        
        # Query the database directly to verify schema
        result = test_db_session.execute(
            text("SELECT url FROM icons WHERE name = :name"),
            {"name": "URL Consistency Test"}
        ).fetchone()
        
        assert result is not None
        assert result[0] == "https://example.com/url-consistency.svg"
        
        # Verify no image_url column exists
        try:
            test_db_session.execute(text("SELECT image_url FROM icons LIMIT 1"))
            pytest.fail("image_url column should not exist")
        except Exception as e:
            # This is expected - column should not exist
            assert "image_url" in str(e).lower()

    @pytest.mark.integration
    def test_database_manager_integration(self):
        """Test DatabaseManager with real database connection."""
        db_manager = DatabaseManager(TEST_DATABASE_URL)
        
        # Test connection
        with db_manager.get_session() as session:
            # Test basic database operations
            result = session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1
            
            # Test that icons table exists
            result = session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_name = 'icons'")
            ).fetchone()
            assert result is not None

    @pytest.mark.integration
    def test_repository_error_handling(self, icon_repository, test_db_session):
        """Test error handling in repository operations."""
        # Test retrieving non-existent icon
        non_existent = icon_repository.get_icon_by_id(99999)
        assert non_existent is None
        
        # Test invalid data
        with pytest.raises(ValidationError):
            invalid_icon = IconData(name="", url="", tags=[])  # Invalid empty fields
            icon_repository.save_icon(invalid_icon)


class TestEndToEndWorkflow:
    """End-to-end integration tests."""
    
    @pytest.mark.integration
    def test_save_search_retrieve_workflow(self, icon_repository, test_db_session):
        """Test basic workflow: create → save → search → retrieve."""
        # Step 1: Create and save icon
        original_icon = IconData(
            name="Workflow Test Icon",
            url="https://example.com/workflow.svg",
            tags=["workflow", "test"],
            category="Testing"
        )
        
        saved_icon = icon_repository.save_icon(original_icon)
        test_db_session.commit()
        
        # Verify save worked and we have an ID
        assert hasattr(saved_icon, 'id')
        assert saved_icon.name == "Workflow Test Icon"
        
        # Step 2: Search by URL
        found_icon = icon_repository.get_icon_by_url("https://example.com/workflow.svg")
        assert found_icon is not None
        assert found_icon.name == "Workflow Test Icon"
        
        # Step 3: Search by query
        search_results = icon_repository.search_icons(query="Workflow")
        assert len(search_results) >= 1
        workflow_icons = [icon for icon in search_results if "Workflow" in icon.name]
        assert len(workflow_icons) >= 1
