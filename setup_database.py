#!/usr/bin/env python
"""Database setup script for Icon Curator."""

import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from icon_curator.database.connection import db_manager
from icon_curator.core.exceptions import DatabaseError


def setup_database():
    """Set up the database with tables and indexes."""
    print("Setting up Icon Curator database...")
    
    try:
        # Create tables
        print("Creating database tables...")
        db_manager.create_tables()
        
        # Test connection
        print("Testing database connection...")
        with db_manager.get_session() as session:
            # Simple query to test connection
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✅ Database setup completed successfully!")
        print(f"Database URL: {db_manager.database_url}")
        
    except DatabaseError as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during database setup: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    print("Icon Curator Database Setup")
    print("=" * 30)
    
    # Check if PostgreSQL environment is set up
    if not os.getenv('DATABASE_URL'):
        print("Environment variables:")
        print(f"  DB_HOST: {os.getenv('DB_HOST', 'localhost')}")
        print(f"  DB_PORT: {os.getenv('DB_PORT', '5432')}")
        print(f"  DB_NAME: {os.getenv('DB_NAME', 'icon_curator_dev')}")
        print(f"  DB_USER: {os.getenv('DB_USER', 'postgres')}")
        print()
    
    setup_database()


if __name__ == "__main__":
    main()
