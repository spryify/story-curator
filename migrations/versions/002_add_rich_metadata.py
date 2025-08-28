"""Migration 002: Add rich metadata columns to icons table.

This migration adds the following columns to support rich metadata from yotoicons.com:
- yoto_icon_id: Icon ID from yotoicons (e.g., '278')  
- primary_tag: Primary tag (e.g., 'dinosaur')
- secondary_tag: Secondary tag (e.g., 't-rex')
- artist: Artist username (e.g., 'pangolinpaw')
- num_downloads: Number of downloads from yotoicons (e.g., '1914')
"""

from sqlalchemy import text
from migrations.utils import BaseMigration


class Migration002AddRichMetadata(BaseMigration):
    """Add rich metadata columns to icons table."""
    
    version = "002"
    description = "Add rich metadata columns to icons table"
    dependencies = ["001"]  # Depends on initial schema
    
    def upgrade(self, connection) -> None:
        """Add rich metadata columns."""
        self.log_progress("Starting upgrade - adding rich metadata columns")
        
        # Check which columns already exist
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons'
        """)
        existing_columns = {row[0] for row in connection.execute(check_query)}
        
        # Define columns to add
        columns_to_add = {
            'yoto_icon_id': 'VARCHAR(50)',
            'primary_tag': 'VARCHAR(100)', 
            'secondary_tag': 'VARCHAR(100)',
            'artist': 'VARCHAR(100)',
            'num_downloads': 'VARCHAR(50)'
        }
        
        # Add columns that don't exist
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                self.log_progress(f"Adding column: {column_name}")
                connection.execute(text(f'ALTER TABLE icons ADD COLUMN {column_name} {column_type}'))
            else:
                self.log_progress(f"Column {column_name} already exists, skipping")
        
        # Add indexes for the new columns
        self.log_progress("Creating indexes for rich metadata columns")
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_icons_yoto_icon_id ON icons(yoto_icon_id)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_icons_primary_tag ON icons(primary_tag)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS idx_icons_artist ON icons(artist)'))
        
        # Update the icon_metadata JSONB column to include rich metadata structure
        connection.execute(text('''
            UPDATE icons 
            SET icon_metadata = jsonb_set(
                COALESCE(icon_metadata, '{}'::jsonb),
                '{rich_metadata_added}',
                'true'::jsonb
            )
            WHERE icon_metadata IS NULL OR NOT icon_metadata ? 'rich_metadata_added'
        '''))
        
        self.log_progress("Rich metadata columns added successfully")
    
    def downgrade(self, connection) -> None:
        """Remove rich metadata columns."""
        self.log_progress("Starting downgrade - removing rich metadata columns")
        
        # Remove the columns
        columns_to_remove = ['yoto_icon_id', 'primary_tag', 'secondary_tag', 'artist', 'num_downloads']
        
        for column_name in columns_to_remove:
            self.log_progress(f"Removing column: {column_name}")
            connection.execute(text(f'ALTER TABLE icons DROP COLUMN IF EXISTS {column_name}'))
        
        # Remove the rich metadata marker from JSONB
        connection.execute(text('''
            UPDATE icons 
            SET icon_metadata = icon_metadata - 'rich_metadata_added'
            WHERE icon_metadata ? 'rich_metadata_added'
        '''))
        
        self.log_progress("Rich metadata columns removed successfully")
