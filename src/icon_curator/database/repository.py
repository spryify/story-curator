"""Repository for icon data access."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import or_, func, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import IconModel
from .connection import db_manager
from ..models.icon import IconData, ScrapingResult
from ..core.exceptions import DatabaseError, ValidationError


class IconRepository:
    """Repository for managing icon data in the database."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize repository with optional session."""
        self._session = session
    
    @property
    def session(self) -> Session:
        """Get database session."""
        if self._session is None:
            self._session = db_manager.get_session()
        return self._session
    
    def save_icon(self, icon_data: IconData) -> IconModel:
        """Save icon data to database.
        
        Args:
            icon_data: Icon data to save
            
        Returns:
            Saved icon model
            
        Raises:
            DatabaseError: If save operation fails
            ValidationError: If icon data is invalid
        """
        # Validate required fields
        if not icon_data.name or not icon_data.url:
            raise ValidationError("Icon must have name and url")
        
        try:
            # Check if icon already exists by URL or yoto_icon_id
            existing = None
            
            # First check by URL
            existing = self.session.query(IconModel).filter_by(url=icon_data.url).first()
            
            # If not found by URL, check by yoto_icon_id if available
            if not existing and icon_data.metadata and icon_data.metadata.get('icon_id'):
                existing = self.session.query(IconModel).filter_by(
                    yoto_icon_id=icon_data.metadata.get('icon_id')
                ).first()
            
            if existing:
                # Update existing icon with new rich metadata
                existing.name = icon_data.name
                existing.image_url = icon_data.url  # Use url field for both url and image_url in database
                existing.tags = icon_data.tags
                existing.description = icon_data.description
                existing.category = icon_data.category
                
                # Extract and save rich metadata
                metadata = icon_data.metadata or {}
                existing.yoto_icon_id = metadata.get('icon_id')
                existing.primary_tag = metadata.get('primary_tag')
                existing.secondary_tag = metadata.get('secondary_tag')
                existing.artist = metadata.get('artist')
                existing.artist_id = metadata.get('artist_id')
                existing.icon_metadata = metadata
                
                existing.updated_at = datetime.utcnow()
                icon_model = existing
            else:
                # Extract rich metadata for new icon
                metadata = icon_data.metadata or {}
                
                # Create new icon
                icon_model = IconModel(
                    name=icon_data.name,
                    url=icon_data.url,
                    image_url=icon_data.url,  # Use url field for image_url in database
                    tags=icon_data.tags,
                    description=icon_data.description,
                    category=icon_data.category,
                    
                    # New rich metadata fields
                    yoto_icon_id=metadata.get('icon_id'),
                    primary_tag=metadata.get('primary_tag'),
                    secondary_tag=metadata.get('secondary_tag'),
                    artist=metadata.get('artist'),
                    artist_id=metadata.get('artist_id'),
                    
                    icon_metadata=metadata,
                )
                self.session.add(icon_model)
            
            self.session.commit()
            return icon_model
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to save icon: {e}") from e
    
    def get_icon_by_id(self, icon_id: int) -> Optional[IconModel]:
        """Get icon by ID.
        
        Args:
            icon_id: Icon ID to retrieve
            
        Returns:
            Icon model or None if not found
        """
        try:
            return self.session.query(IconModel).filter_by(id=icon_id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get icon by ID: {e}") from e
    
    def get_icon_by_url(self, url: str) -> Optional[IconModel]:
        """Get icon by URL.
        
        Args:
            url: Icon URL to search for
            
        Returns:
            Icon model or None if not found
        """
        try:
            return self.session.query(IconModel).filter_by(url=url).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get icon by URL: {e}") from e
    
    def search_icons(
        self, 
        query: str, 
        category: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[IconModel]:
        """Search icons by text query, category, and/or tags.
        
        Args:
            query: Text query to search in name and description
            category: Category to filter by
            tags: Tags to filter by (any match)
            limit: Maximum number of results
            
        Returns:
            List of matching icon models
        """
        try:
            db_query = self.session.query(IconModel)
            
            # Text search in name and description
            if query:
                search_filter = or_(
                    IconModel.name.ilike(f"%{query}%"),
                    IconModel.description.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
            
            # Category filter
            if category:
                db_query = db_query.filter(IconModel.category == category)
            
            # Tags filter
            if tags:
                for tag in tags:
                    db_query = db_query.filter(IconModel.tags.any(tag))
            
            return db_query.limit(limit).all()
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search icons: {e}") from e
    
    def search_icons_by_artist(self, artist: str, limit: int = 50) -> List[IconModel]:
        """Search icons by artist name.
        
        Args:
            artist: Artist username to search for
            limit: Maximum number of results
            
        Returns:
            List of matching icon models
        """
        try:
            return (
                self.session.query(IconModel)
                .filter(IconModel.artist.ilike(f"%{artist}%"))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search icons by artist: {e}") from e

    def search_icons_by_yoto_id(self, yoto_icon_id: str) -> Optional[IconModel]:
        """Search for icon by Yoto icon ID.
        
        Args:
            yoto_icon_id: Yoto icon ID to search for
            
        Returns:
            Matching icon model or None
        """
        try:
            return (
                self.session.query(IconModel)
                .filter(IconModel.yoto_icon_id == yoto_icon_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search icon by Yoto ID: {e}") from e

    def search_icons_advanced(
        self, 
        query: Optional[str] = None,
        category: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        artist: Optional[str] = None,
        primary_tag: Optional[str] = None,
        secondary_tag: Optional[str] = None,
        limit: int = 50
    ) -> List[IconModel]:
        """Advanced search with rich metadata support.
        
        Args:
            query: Text query to search in name and description
            category: Category to filter by
            tags: Tags to filter by (any match)
            artist: Artist username to filter by
            primary_tag: Primary tag to filter by
            secondary_tag: Secondary tag to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching icon models
        """
        try:
            db_query = self.session.query(IconModel)
            
            # Text search in name, description, and rich metadata
            if query:
                search_filter = or_(
                    IconModel.name.ilike(f"%{query}%"),
                    IconModel.description.ilike(f"%{query}%"),
                    IconModel.primary_tag.ilike(f"%{query}%"),
                    IconModel.secondary_tag.ilike(f"%{query}%"),
                    IconModel.artist.ilike(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
            
            # Category filter
            if category:
                db_query = db_query.filter(IconModel.category == category)
            
            # Tags filter (array contains)
            if tags:
                for tag in tags:
                    db_query = db_query.filter(IconModel.tags.any(tag))
            
            # Artist filter
            if artist:
                db_query = db_query.filter(IconModel.artist.ilike(f"%{artist}%"))
            
            # Primary tag filter
            if primary_tag:
                db_query = db_query.filter(IconModel.primary_tag.ilike(f"%{primary_tag}%"))
            
            # Secondary tag filter
            if secondary_tag:
                db_query = db_query.filter(IconModel.secondary_tag.ilike(f"%{secondary_tag}%"))
            
            return db_query.limit(limit).all()
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search icons: {e}") from e
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories.
        
        Returns:
            List of category names
        """
        try:
            result = self.session.query(IconModel.category).distinct().filter(
                IconModel.category.isnot(None)
            ).all()
            return [row[0] for row in result]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get categories: {e}") from e
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags.
        
        Returns:
            List of tag names
        """
        try:
            # PostgreSQL-specific query to unnest array column
            result = self.session.execute(
                text("SELECT DISTINCT unnest(tags) as tag FROM icons WHERE tags IS NOT NULL")
            ).fetchall()
            return [row[0] for row in result]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get tags: {e}") from e
    
    def get_icon_count(self) -> int:
        """Get total number of icons.
        
        Returns:
            Total icon count
        """
        try:
            return self.session.query(func.count(IconModel.id)).scalar()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get icon count: {e}") from e
    
    def delete_icon(self, icon_id: int) -> bool:
        """Delete icon by ID.
        
        Args:
            icon_id: Icon ID to delete
            
        Returns:
            True if icon was deleted, False if not found
        """
        try:
            icon = self.session.query(IconModel).filter_by(id=icon_id).first()
            if icon:
                self.session.delete(icon)
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Failed to delete icon: {e}") from e
    
    def close(self):
        """Close the database session."""
        if self._session:
            self._session.close()
            self._session = None
