"""Migration 004: Fix num_downloads column in icons table.

This migration corrects the icon metadata schema:
- Removes the incorrectly named 'artist_id' column  
- Adds the correct 'num_downloads' column for storing download counts from yotoicons
- Updates any existing data to use the correct field names
"""

from sqlalchemy import text
from migrations.utils import BaseMigration


class Migration004FixNumDownloadsColumn(BaseMigration):
    """Fix num_downloads column in icons table."""
    
    version = "004"
    description = "Fix num_downloads column in icons table"
    dependencies = ["003"]  # Depends on previous migration
    
    def upgrade(self, connection) -> None:
        """Fix the num_downloads column."""
        self.log_progress("Starting upgrade - fixing num_downloads column")
        
        # Check if artist_id column exists (needs to be removed)
        check_artist_id = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons' AND column_name = 'artist_id'
        """)
        artist_id_exists = bool(connection.execute(check_artist_id).fetchone())
        
        # Check if num_downloads column exists (needs to be added if missing)
        check_num_downloads = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons' AND column_name = 'num_downloads'
        """)
        num_downloads_exists = bool(connection.execute(check_num_downloads).fetchone())
        
        # If we have artist_id but not num_downloads, we need to migrate the data
        if artist_id_exists and not num_downloads_exists:
            self.log_progress("Migrating artist_id data to num_downloads column")
            
            # Add num_downloads column
            connection.execute(text('ALTER TABLE icons ADD COLUMN num_downloads VARCHAR(50)'))
            
            # Copy data from artist_id to num_downloads (since artist_id was incorrectly storing download counts)
            connection.execute(text('UPDATE icons SET num_downloads = artist_id WHERE artist_id IS NOT NULL'))
            
            # Drop the artist_id column and its index
            connection.execute(text('DROP INDEX IF EXISTS idx_icon_artist_id'))
            connection.execute(text('ALTER TABLE icons DROP COLUMN artist_id'))
            
            self.log_progress("Successfully migrated artist_id to num_downloads and removed artist_id column")
            
        elif artist_id_exists and num_downloads_exists:
            self.log_progress("Both columns exist - removing duplicate artist_id column")
            
            # Just remove the duplicate artist_id column
            connection.execute(text('DROP INDEX IF EXISTS idx_icon_artist_id'))
            connection.execute(text('ALTER TABLE icons DROP COLUMN artist_id'))
            
        elif not num_downloads_exists:
            self.log_progress("Adding missing num_downloads column")
            
            # Just add the missing column
            connection.execute(text('ALTER TABLE icons ADD COLUMN num_downloads VARCHAR(50)'))
            
        else:
            self.log_progress("Schema is already correct - no changes needed")
        
        # Ensure we have the correct index for num_downloads
        check_index = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'icons' AND indexname = 'idx_icon_num_downloads'
        """)
        index_exists = bool(connection.execute(check_index).fetchone())
        
        if not index_exists:
            self.log_progress("Creating index for num_downloads column")
            connection.execute(text('CREATE INDEX idx_icon_num_downloads ON icons (num_downloads)'))
        
        self.log_progress("Migration 004 completed successfully")

    def downgrade(self, connection) -> None:
        """Reverse the num_downloads column fix."""
        self.log_progress("Starting downgrade - reverting num_downloads column changes")
        
        # Check if num_downloads column exists
        check_num_downloads = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'icons' AND column_name = 'num_downloads'
        """)
        num_downloads_exists = bool(connection.execute(check_num_downloads).fetchone())
        
        if num_downloads_exists:
            # Add back artist_id column
            connection.execute(text('ALTER TABLE icons ADD COLUMN artist_id VARCHAR(50)'))
            
            # Copy data back from num_downloads to artist_id
            connection.execute(text('UPDATE icons SET artist_id = num_downloads WHERE num_downloads IS NOT NULL'))
            
            # Create the old index
            connection.execute(text('CREATE INDEX idx_icon_artist_id ON icons (artist_id)'))
            
            # Drop the num_downloads column and its index
            connection.execute(text('DROP INDEX IF EXISTS idx_icon_num_downloads'))
            connection.execute(text('ALTER TABLE icons DROP COLUMN num_downloads'))
            
            self.log_progress("Successfully reverted num_downloads changes")
        else:
            self.log_progress("num_downloads column doesn't exist - no changes needed")
        
        self.log_progress("Migration 004 downgrade completed")
