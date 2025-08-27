# Database Migrations

This directory contains the database migration system for the Story Curator project, designed specifically for PostgreSQL databases.

## Overview

The migration system provides versioned database schema changes with support for:

- **Forward migrations (upgrade)**: Apply new schema changes
- **Reverse migrations (downgrade)**: Rollback schema changes  
- **Migration tracking**: Keep track of which migrations have been applied
- **Preconditions**: Validate database state before applying migrations
- **PostgreSQL features**: Full support for PostgreSQL-specific features like GIN indexes, triggers, and extensions

## Directory Structure

```
migrations/
├── README.md                    # This file
├── __init__.py                 # Python package marker
├── migration_runner.py         # Main CLI tool for running migrations
├── migrate.sh                  # Convenience script for common operations
├── utils.py                    # Base classes and utilities
└── versions/                   # Individual migration files
    ├── __init__.py
    ├── 001_initial_schema.py   # Initial database schema
    ├── 002_add_rich_metadata.py
    └── 003_remove_duplicate_url.py
```

## Usage

### Using the CLI Tool Directly

The migration runner can be used directly:

```bash
# Show current migration status
python migrations/migration_runner.py --database-url "postgresql://user:pass@localhost/db" status

# Apply all pending migrations
python migrations/migration_runner.py --database-url "postgresql://user:pass@localhost/db" upgrade

# Downgrade to a specific version
python migrations/migration_runner.py --database-url "postgresql://user:pass@localhost/db" downgrade Migration001InitialSchema

# Show migration history
python migrations/migration_runner.py --database-url "postgresql://user:pass@localhost/db" history
```

### Using the Convenience Script

A convenience script is available in this directory:

```bash
# Show current migration status
./migrations/migrate.sh status

# Apply all pending migrations
./migrations/migrate.sh upgrade

# Downgrade to a specific version
./migrations/migrate.sh downgrade Migration001InitialSchema

# Show migration history
./migrations/migrate.sh history
```

### Environment Variables

The system uses these environment variables for database connection:

- `DATABASE_URL`: Full PostgreSQL connection URL (e.g., `postgresql://user:pass@localhost/db`)
- `DB_HOST`: Database host (default: `localhost`)
- `DB_PORT`: Database port (default: `5432`)
- `DB_NAME`: Database name (default: `story_curator_dev`)
- `DB_USER`: Database user (default: `postgres`)
- `DB_PASSWORD`: Database password (default: empty)

## Creating New Migrations

To create a new migration, add a new file in the `versions/` directory following the naming convention:

```
XXX_descriptive_name.py
```

Where `XXX` is the next sequential number (e.g., `004_add_user_preferences.py`).

### Migration File Template

```python
"""
Migration: Add user preferences table
Version: 004
Dependencies: 003_remove_duplicate_url
"""

from sqlalchemy import text
from migrations.utils import BaseMigration

class Migration004AddUserPreferences(BaseMigration):
    version = "004"
    description = "Add user preferences table"
    dependencies = ["003"]
    
    def check_preconditions(self, connection) -> bool:
        """Check if preconditions are met."""
        # Verify previous migration was applied
        result = connection.execute(text("SELECT 1 FROM applied_migrations WHERE version = '003'"))
        return result.fetchone() is not None
    
    def upgrade(self, connection) -> None:
        """Apply the migration."""
        connection.execute(text('''
            CREATE TABLE user_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                preference_key VARCHAR(100) NOT NULL,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key)
            )
        '''))
        
        connection.execute(text('''
            CREATE INDEX idx_user_preferences_user_id 
            ON user_preferences(user_id)
        '''))
    
    def downgrade(self, connection) -> None:
        """Rollback the migration."""
        connection.execute(text('DROP TABLE IF EXISTS user_preferences'))
```

## Database Connection

The migration system is designed specifically for PostgreSQL and includes:

- Automatic creation of the `applied_migrations` tracking table
- Support for PostgreSQL-specific features (GIN indexes, pg_trgm extension, etc.)
- Transaction-based migration execution
- Proper connection handling and cleanup

## Best Practices

1. **Always test migrations**: Test both upgrade and downgrade paths
2. **Use transactions**: Each migration runs in a transaction for safety
3. **Check preconditions**: Validate database state before making changes
4. **Document changes**: Include clear descriptions and comments
5. **Backup data**: Always backup production data before running migrations
6. **Sequential versioning**: Use sequential version numbers (001, 002, 003...)

## Troubleshooting

### Migration Fails

If a migration fails:

1. Check the error message in the logs
2. Verify database connection settings
3. Ensure preconditions are met
4. Check for conflicting database state

### Database Connection Issues

If you can't connect to the database:

1. Verify PostgreSQL is running
2. Check connection parameters (host, port, credentials)
3. Ensure database exists
4. Verify network connectivity

### Rollback Issues

If you need to manually fix migration state:

```sql
-- View applied migrations
SELECT * FROM applied_migrations ORDER BY applied_at;

-- Manually mark migration as applied (use carefully!)
INSERT INTO applied_migrations (version, description) 
VALUES ('001', 'Initial schema');

-- Remove migration record (for rollback)
DELETE FROM applied_migrations WHERE version = '002';
```
