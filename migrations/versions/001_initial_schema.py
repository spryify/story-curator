"""Migration 001: Initial schema setup.

Creates the initial database schema with the icons table and basic indexes.
This represents the state before any rich metadata was added.
"""

from sqlalchemy import text
from migrations.utils import BaseMigration


class Migration001InitialSchema(BaseMigration):
    """Initial database schema setup."""
    
    version = "001"
    description = "Initial database schema setup with icons table"
    dependencies = []  # No dependencies for initial migration
    
    def upgrade(self, connection) -> None:
        """Create initial database schema."""
        self.log_progress("Creating initial database schema")
        
        # Create icons table
        self.log_progress("Creating icons table")
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS icons (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL UNIQUE,
                tags TEXT[],
                description TEXT,
                category VARCHAR(100),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                icon_metadata JSONB DEFAULT '{}'::jsonb
            )
        """))
        
        # Create basic indexes
        self.log_progress("Creating basic indexes")
        
        # Index for name searches
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_icons_name ON icons(name)"))
        
        # Index for category searches
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_icons_category ON icons(category)"))
        
        # Index for created_at for sorting
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_icons_created_at ON icons(created_at)"))
        
        # GIN index for tags array searches (PostgreSQL specific)
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_icons_tags ON icons USING GIN(tags)"))
        
        # Full text search indexes (requires pg_trgm extension)
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_icons_name_fts 
            ON icons USING GIN(name gin_trgm_ops)
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_icons_description_fts 
            ON icons USING GIN(description gin_trgm_ops)
        """))
        
        # Create trigger for updating updated_at timestamp
        self.log_progress("Creating update trigger")
        connection.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language plpgsql
        """))
        
        connection.execute(text("""
            CREATE TRIGGER update_icons_updated_at
            BEFORE UPDATE ON icons
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at()
        """))
        
        self.log_progress("Initial schema created successfully")
    
    def downgrade(self, connection) -> None:
        """Drop initial database schema."""
        self.log_progress("Dropping initial database schema")
        
        # Drop trigger and function
        connection.execute(text("DROP TRIGGER IF EXISTS update_icons_updated_at ON icons"))
        connection.execute(text("DROP FUNCTION IF EXISTS update_updated_at()"))
        
        # Drop table (this will also drop all indexes)
        connection.execute(text("DROP TABLE IF EXISTS icons"))
        
        self.log_progress("Initial schema dropped successfully")
