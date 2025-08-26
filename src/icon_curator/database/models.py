"""Database models for icon storage."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class IconModel(Base):
    """SQLAlchemy model for storing icon data."""
    
    __tablename__ = "icons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=False, unique=True)
    image_url = Column(String(500), nullable=False)
    tags = Column(ARRAY(String), nullable=False, default=list)
    description = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    icon_metadata = Column(JSONB, default=dict)
    
    # Create indexes for search performance
    __table_args__ = (
        Index('idx_icon_tags', 'tags', postgresql_using='gin'),
        Index('idx_icon_name_fts', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_icon_description_fts', 'description', postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'}),
        Index('idx_icon_category', 'category'),
        Index('idx_icon_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<IconModel(id={self.id}, name='{self.name}', category='{self.category}')>"
