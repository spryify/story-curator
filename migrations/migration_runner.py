#!/usr/bin/env python3
"""Database migration runner.

This script provides a command-line interface for running database migrations.

Usage:
    python migration_runner.py upgrade [version]   # Upgrade to latest or specific version
    python migration_runner.py downgrade [version] # Downgrade to specific version
    python migration_runner.py status              # Show migration status
    python migration_runner.py history             # Show migration history
"""

import argparse
import importlib
import logging
import sys
from pathlib import Path
from typing import List, Type, Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from migrations.utils import BaseMigration, MigrationRegistry, MigrationError

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Main migration runner for PostgreSQL database."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.registry = MigrationRegistry(database_url)
        self.migrations_dir = Path(__file__).parent / "versions"
        self._available_migrations: List[Type[BaseMigration]] = []
        self._load_migrations()
    
    def _load_migrations(self) -> None:
        """Load all available migration classes."""
        self._available_migrations = []
        
        # Get all Python files in versions directory
        migration_files = sorted(self.migrations_dir.glob("*.py"))
        
        for file_path in migration_files:
            if file_path.name.startswith("__"):
                continue
            
            # Import the module
            module_name = f"migrations.versions.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Find migration classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseMigration) and 
                        attr != BaseMigration):
                        self._available_migrations.append(attr)
                        
            except ImportError as e:
                logger.warning(f"Could not import migration {file_path}: {e}")
        
        # Sort by version/filename
        self._available_migrations.sort(key=lambda m: m.__module__)
    
    def get_pending_migrations(self) -> List[Type[BaseMigration]]:
        """Get list of pending (unapplied) migrations."""
        applied = set(self.registry.get_applied_migrations())
        pending = []
        
        for migration_class in self._available_migrations:
            # Create instance to get version number
            instance = migration_class()
            if instance.version not in applied:
                pending.append(migration_class)
        
        return pending
    
    def upgrade(self, target_version: Optional[str] = None) -> None:
        """Run upgrade migrations.
        
        Args:
            target_version: Specific version to upgrade to. If None, upgrades to latest.
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations to apply.")
            return
        
        # If target version specified, only run up to that version
        if target_version:
            pending = [m for m in pending if m.__name__ <= target_version]
        
        logger.info(f"Applying {len(pending)} migration(s)...")
        
        # Create database connection
        from sqlalchemy import create_engine
        engine = create_engine(self.registry.database_url)
        
        for migration_class in pending:
            try:
                migration = migration_class()
                
                with engine.connect() as conn:
                    trans = conn.begin()
                    
                    try:
                        # Validate preconditions
                        if not migration.check_preconditions(conn):
                            raise MigrationError(f"Preconditions not met for {migration.version}")
                        
                        migration.log_progress("Starting upgrade")
                        migration.upgrade(conn)
                        
                        # Mark as applied
                        self.registry.mark_applied(migration.version, migration.description)
                        migration.log_progress("Successfully applied")
                        
                        trans.commit()
                        
                    except Exception as e:
                        trans.rollback()
                        raise e
                        
            except Exception as e:
                logger.error(f"Migration {migration_class.__name__} failed: {e}")
                raise MigrationError(f"Migration failed: {e}") from e
    
    def downgrade(self, target_version: str) -> None:
        """Run downgrade migrations.
        
        Args:
            target_version: Version to downgrade to.
        """
        applied = self.registry.get_applied_migrations()
        
        # Find migrations to revert (those applied after target version)
        to_revert = []
        for version in reversed(applied):  # Revert in reverse order
            if version > target_version:
                # Find the migration class
                migration_class = next((m for m in self._available_migrations 
                                      if m.__name__ == version), None)
                if migration_class:
                    to_revert.append(migration_class)
        
        if not to_revert:
            logger.info(f"Already at or before version {target_version}")
            return
        
        logger.info(f"Reverting {len(to_revert)} migration(s)...")
        
        for migration_class in to_revert:
            try:
                migration = migration_class()
                migration.log_progress("Starting downgrade")
                migration.downgrade()
                
                # Mark as reverted
                self.registry.mark_reverted(migration.version)
                migration.log_progress("Successfully reverted")
                
            except Exception as e:
                logger.error(f"Downgrade of {migration_class.__name__} failed: {e}")
                raise MigrationError(f"Downgrade failed: {e}") from e
    
    def status(self) -> None:
        """Show current migration status."""
        applied = set(self.registry.get_applied_migrations())
        
        print("Migration Status:")
        print("================")
        
        for migration_class in self._available_migrations:
            instance = migration_class()
            status = "✓ Applied" if instance.version in applied else "✗ Pending"
            print(f"{migration_class.__name__:<30} {status:<10} {instance.description}")
        
        pending_count = len(self.get_pending_migrations())
        print(f"\nTotal: {len(self._available_migrations)} migrations, {pending_count} pending")
    
    def history(self) -> None:
        """Show migration history."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(self.registry.database_url)
        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT version, description, applied_at 
                FROM applied_migrations 
                ORDER BY applied_at DESC
            '''))
            
            print("Migration History:")
            print("==================")
            
            for row in result.fetchall():
                version, description, applied_at = row
                print(f"{applied_at} - {version}: {description}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    parser.add_argument("--database-url", help="PostgreSQL database URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Run upgrade migrations")
    upgrade_parser.add_argument("version", nargs="?", help="Target version (optional)")
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Run downgrade migrations")
    downgrade_parser.add_argument("version", help="Target version")
    
    # Status command
    subparsers.add_parser("status", help="Show migration status")
    
    # History command
    subparsers.add_parser("history", help="Show migration history")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create runner
    runner = MigrationRunner(args.database_url)
    
    try:
        if args.command == "upgrade":
            runner.upgrade(args.version)
        elif args.command == "downgrade":
            runner.downgrade(args.version)
        elif args.command == "status":
            runner.status()
        elif args.command == "history":
            runner.history()
        else:
            parser.print_help()
            return 1
    
    except MigrationError as e:
        logger.error(f"Migration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
