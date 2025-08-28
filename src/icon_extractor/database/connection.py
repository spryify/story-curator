"""Database connection and session management."""

import os
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from ..core.exceptions import DatabaseError


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection URL. If None, will read from environment.
        """
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self.database_url = database_url or self._get_database_url()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Default development database
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME', 'story_curator_dev')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', '')
            
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
        return db_url
    
    @property
    def engine(self) -> Engine:
        """Get database engine, creating it if necessary."""
        if self._engine is None:
            try:
                self._engine = create_engine(
                    self.database_url,
                    echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            except Exception as e:
                raise DatabaseError(f"Failed to create database engine: {e}") from e
        
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get session factory, creating it if necessary."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        
        return self._session_factory
    
    def get_session(self) -> Session:
        """Create a new database session."""
        try:
            return self.session_factory()
        except Exception as e:
            raise DatabaseError(f"Failed to create database session: {e}") from e
    
    def create_tables(self) -> None:
        """Create all database tables."""
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to create database tables: {e}") from e
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to drop database tables: {e}") from e


# Global database manager instance
db_manager = DatabaseManager()
