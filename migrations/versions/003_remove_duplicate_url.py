"""Migration 003: Remove duplicate image_url column from icons table.

This migration:
1. Drops the image_url column since it's redundant with url column
2. Updates any database constraints/indexes as needed
"""

from sqlalchemy import text
from migrations.utils import BaseMigration


class Migration003RemoveDuplicateUrl(BaseMigration):
    """Remove duplicate image_url column from icons table."""
    
    version = "003"
    description = "Remove duplicate image_url column from icons table"
    dependencies = ["002"]  # Depends on rich metadata migration
    
    def upgrade(self, connection) -> None:
        """Remove duplicate image_url column."""
        self.log_progress("Starting upgrade - removing duplicate image_url column")
        
        # Check if the image_url column exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons' AND column_name = 'image_url'
        """)
        result = connection.execute(check_query).fetchone()
        
        if result:
            # Drop any indexes on the image_url column first
            self.log_progress("Dropping indexes on image_url column")
            connection.execute(text('DROP INDEX IF EXISTS idx_icons_image_url'))
            connection.execute(text('DROP INDEX IF EXISTS idx_icons_image_url_unique'))
            
            # Drop the column
            self.log_progress("Dropping image_url column")
            connection.execute(text('ALTER TABLE icons DROP COLUMN image_url'))
            
            self.log_progress("image_url column removed successfully")
        else:
            self.log_progress("image_url column does not exist, skipping removal")
        
        # Update icon_metadata to mark this migration as applied
        connection.execute(text('''
            UPDATE icons 
            SET icon_metadata = jsonb_set(
                COALESCE(icon_metadata, '{}'::jsonb),
                '{duplicate_url_removed}',
                'true'::jsonb
            )
            WHERE icon_metadata IS NULL OR NOT icon_metadata ? 'duplicate_url_removed'
        '''))
    
    def downgrade(self, connection) -> None:
        """Add back the image_url column (as a copy of url)."""
        self.log_progress("Starting downgrade - adding back image_url column")
        
        # Check if the image_url column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons' AND column_name = 'image_url'
        """)
        result = connection.execute(check_query).fetchone()
        
        if not result:
            # Add the image_url column back
            self.log_progress("Adding image_url column")
            connection.execute(text('ALTER TABLE icons ADD COLUMN image_url VARCHAR(500)'))
            
            # Copy url values to image_url
            self.log_progress("Copying url values to image_url")
            connection.execute(text('UPDATE icons SET image_url = url WHERE url IS NOT NULL'))
            
            # Create index on image_url
            self.log_progress("Creating index on image_url")
            connection.execute(text('CREATE INDEX idx_icons_image_url ON icons(image_url)'))
            
            self.log_progress("image_url column restored successfully")
        else:
            self.log_progress("image_url column already exists, skipping restoration")
        
        # Remove the migration marker from icon_metadata
        connection.execute(text('''
            UPDATE icons 
            SET icon_metadata = icon_metadata - 'duplicate_url_removed'
            WHERE icon_metadata ? 'duplicate_url_removed'
        '''))
