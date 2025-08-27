"""Migration utilities and base classes."""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Exception raised during migration operations."""
    pass


class BaseMigration(ABC):
    """Base class for all database migrations following SQLAlchemy patterns."""
    
    # These should be set as class attributes in subclasses
    version: str = ""
    description: str = ""
    dependencies: list[str] = []
    
    def __init__(self):
        if not self.version:
            raise MigrationError(f"Migration {self.__class__.__name__} must define a 'version' class attribute")
        if not self.description:
            raise MigrationError(f"Migration {self.__class__.__name__} must define a 'description' class attribute")
    
    @abstractmethod
    def upgrade(self, connection) -> None:
        """Apply the migration.
        
        Args:
            connection: SQLAlchemy database connection
        """
        pass
    
    @abstractmethod
    def downgrade(self, connection) -> None:
        """Rollback the migration.
        
        Args:
            connection: SQLAlchemy database connection
        """
        pass
    
    def check_preconditions(self, connection) -> bool:
        """Check if preconditions for this migration are met.
        
        Args:
            connection: SQLAlchemy database connection
            
        Returns:
            bool: True if preconditions are met, False otherwise
        """
        # Default implementation: check that all dependencies are applied
        from sqlalchemy import text
        
        for dep_version in self.dependencies:
            result = connection.execute(
                text("SELECT COUNT(*) FROM applied_migrations WHERE version = :version"),
                {"version": dep_version}
            )
            if (result.scalar() or 0) == 0:
                logger.warning(f"Migration {self.version}: dependency {dep_version} not applied")
                return False
        return True
    
    def log_progress(self, message: str) -> None:
        """Log migration progress."""
        logger.info(f"[{self.version}] {message}")


class MigrationRegistry:
    """Registry to track applied migrations in PostgreSQL."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_database_url()
        self._ensure_migration_table()
    
    def _get_database_url(self) -> str:
        """Get PostgreSQL database URL from environment."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Default development database
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME', 'story_curator_dev')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', '')
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        return database_url
    
    def _ensure_migration_table(self) -> None:
        """Ensure the migrations tracking table exists in PostgreSQL."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.database_url)
        with engine.connect() as conn:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS applied_migrations (
                    id SERIAL PRIMARY KEY,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            conn.commit()
    
    def is_applied(self, version: str) -> bool:
        """Check if a migration version has been applied."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.database_url)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM applied_migrations WHERE version = :version"),
                {"version": version}
            )
            count = result.scalar()
            return (count or 0) > 0
    
    def mark_applied(self, version: str, description: str) -> None:
        """Mark a migration as applied."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.database_url)
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO applied_migrations (version, description) VALUES (:version, :description) ON CONFLICT (version) DO NOTHING"),
                {"version": version, "description": description}
            )
            conn.commit()
    
    def mark_reverted(self, version: str) -> None:
        """Mark a migration as reverted."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.database_url)
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM applied_migrations WHERE version = :version"),
                {"version": version}
            )
            conn.commit()
    
    def get_applied_migrations(self) -> list[str]:
        """Get list of applied migration versions."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.database_url)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT version FROM applied_migrations ORDER BY applied_at")
            )
            return [row[0] for row in result.fetchall()]
