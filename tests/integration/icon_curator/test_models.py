"""Test-specific database models for SQLite compatibility."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

TestBase = declarative_base()


class TestIconModel(TestBase):
    """SQLite-compatible model for testing."""
    
    __tablename__ = "icons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    image_url = Column(String(500), nullable=False)
    tags = Column(Text, default="")  # Store as comma-separated string for SQLite
    description = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    icon_metadata = Column(Text, default="{}")  # Store as JSON string for SQLite
    
    def __repr__(self) -> str:
        return f"<TestIconModel(id={self.id}, name='{self.name}', category='{self.category}')>"
