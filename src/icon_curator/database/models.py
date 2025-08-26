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
    tags = Column(ARRAY(String), nullable=False, default=lambda: [])
    description = Column(Text)
    category = Column(String(100))
    
    # New rich metadata columns from yotoicons.com
    yoto_icon_id = Column(String(50), nullable=True, index=True)  # Icon ID from yotoicons (e.g., '278')
    primary_tag = Column(String(100), nullable=True)  # Primary tag (e.g., 'dinosaur')
    secondary_tag = Column(String(100), nullable=True)  # Secondary tag (e.g., 't-rex')
    artist = Column(String(100), nullable=True)  # Artist username (e.g., 'pangolinpaw')
    artist_id = Column(String(50), nullable=True)  # Artist ID from yotoicons (e.g., '1914')
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    icon_metadata = Column(JSONB, default=lambda: {})  # Additional flexible metadata
    
    def __init__(self, **kwargs):
        """Initialize IconModel with proper defaults."""
        # Set defaults for mutable types
        if 'tags' not in kwargs:
            kwargs['tags'] = []
        if 'icon_metadata' not in kwargs:
            kwargs['icon_metadata'] = {}
        super().__init__(**kwargs)
    
    # Create indexes for search performance
    __table_args__ = (
        Index('idx_icon_tags', 'tags', postgresql_using='gin'),
        Index('idx_icon_name_fts', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_icon_description_fts', 'description', postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'}),
        Index('idx_icon_category', 'category'),
        Index('idx_icon_created_at', 'created_at'),
        
        # Indexes for new rich metadata columns
        Index('idx_icon_yoto_id', 'yoto_icon_id'),  # For unique icon lookups
        Index('idx_icon_primary_tag', 'primary_tag'),  # For tag-based searches
        Index('idx_icon_secondary_tag', 'secondary_tag'),  # For secondary tag searches
        Index('idx_icon_artist', 'artist'),  # For artist-based searches
        Index('idx_icon_artist_id', 'artist_id'),  # For artist ID lookups
    )
    
    def __repr__(self) -> str:
        return f"<IconModel(id={self.id}, name='{self.name}', category='{self.category}')>"
