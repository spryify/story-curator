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
        if not icon_data.name or not icon_data.url or not icon_data.image_url:
            raise ValidationError("Icon must have name, url, and image_url")
        
        try:
            # Check if icon already exists by URL
            existing = self.session.query(IconModel).filter_by(url=icon_data.url).first()
            
            if existing:
                # Update existing icon
                existing.name = icon_data.name
                existing.image_url = icon_data.image_url
                existing.tags = icon_data.tags
                existing.description = icon_data.description
                existing.category = icon_data.category
                existing.icon_metadata = icon_data.metadata or {}
                existing.updated_at = datetime.utcnow()
                icon_model = existing
            else:
                # Create new icon
                icon_model = IconModel(
                    name=icon_data.name,
                    url=icon_data.url,
                    image_url=icon_data.image_url,
                    tags=icon_data.tags,
                    description=icon_data.description,
                    category=icon_data.category,
                    icon_metadata=icon_data.metadata or {},
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
