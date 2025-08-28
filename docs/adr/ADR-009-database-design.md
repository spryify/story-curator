# ADR-009: Database Design for Icon Curator

## Status
Accepted

## Context
The Icon Curator feature (FR-004-yoto-icons-db) requires a robust database design for storing, indexing, and querying Yoto icons scraped from yotoicons.com. The database must support:

1. **Efficient Storage**: Store icon metadata, URLs, tags, and categories
2. **Fast Search**: Support full-text search across names, tags, and descriptions
3. **Scalability**: Handle thousands of icons with minimal performance degradation
4. **Data Integrity**: Ensure data consistency and prevent duplicates
5. **Development Consistency**: Use the same database technology in development and production

## Decision
We will use **PostgreSQL** as the primary database for both development and production environments with the following design:

### Core Schema Design
```sql
-- Main icons table with PostgreSQL-specific features
CREATE TABLE icons (
    id SERIAL PRIMARY KEY,
    yoto_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    image_url TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    tags TEXT[] DEFAULT '{}',  -- PostgreSQL native array
    category VARCHAR(100),
    description TEXT,
    icon_metadata JSONB DEFAULT '{}',  -- PostgreSQL native JSONB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for optimal query performance
CREATE INDEX idx_icons_name_gin ON icons USING GIN(to_tsvector('english', name));
CREATE INDEX idx_icons_tags_gin ON icons USING GIN(tags);
CREATE INDEX idx_icons_category ON icons(category);
CREATE INDEX idx_icons_metadata_gin ON icons USING GIN(icon_metadata);
CREATE INDEX idx_icons_created_at ON icons(created_at);
CREATE INDEX idx_icons_yoto_id ON icons(yoto_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update timestamps
CREATE TRIGGER update_icons_updated_at 
    BEFORE UPDATE ON icons 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### Key Design Decisions

1. **PostgreSQL Native Types**:
   - `TEXT[]` for tags - enables efficient array operations and GIN indexing
   - `JSONB` for metadata - provides structured data storage with indexing support
   - `TIMESTAMP WITH TIME ZONE` for proper timezone handling

2. **Indexing Strategy**:
   - GIN indexes for full-text search on names and tags
   - GIN index on JSONB metadata for structured queries
   - Standard B-tree indexes for exact matches and sorting

3. **Data Integrity**:
   - `yoto_id` UNIQUE constraint prevents duplicate icons from source
   - `url` UNIQUE constraint prevents duplicate URLs
   - NOT NULL constraints on essential fields

4. **Performance Optimization**:
   - SERIAL primary key for efficient joins
   - Automatic timestamp updates via triggers
   - Optimized column types and sizes

## Alternatives Considered

### 1. SQLite + PostgreSQL Dual Approach
- **Pros**: Fast local testing, no external dependencies for development
- **Cons**: Feature mismatch between databases, testing inconsistencies, maintenance overhead
- **Rejected**: Creates development/production parity issues

### 2. MongoDB
- **Pros**: Natural JSON document storage, flexible schema
- **Cons**: Less mature full-text search, team unfamiliarity, additional complexity
- **Rejected**: PostgreSQL provides equivalent JSON capabilities with better ecosystem

### 3. MySQL
- **Pros**: Widely used, good performance
- **Cons**: Limited array and JSON support compared to PostgreSQL, less advanced indexing
- **Rejected**: PostgreSQL offers superior features for our use case

## Consequences

### Positive
1. **Development-Production Parity**: Identical database features and behavior across environments
2. **Advanced Search Capabilities**: GIN indexes provide excellent full-text search performance
3. **Structured Data Support**: Native JSONB support for flexible metadata storage
4. **Array Operations**: Native array support for tags enables efficient queries
5. **Ecosystem Maturity**: Rich tooling and library support for PostgreSQL
6. **Migration System**: Robust schema evolution with version control and rollback capabilities
7. **Transaction Safety**: All database changes protected by ACID transactions
8. **Operational Transparency**: Clear status reporting and migration history tracking

### Negative
1. **Development Setup**: Requires PostgreSQL installation for local development
2. **Resource Usage**: Higher memory footprint compared to SQLite for testing
3. **Complexity**: More complex than simple file-based databases
4. **Migration Dependencies**: Requires careful ordering and dependency management for schema changes

### Migration Strategy
1. **Development Environment**: Update all developers to use PostgreSQL locally
2. **Test Suite**: Modify test fixtures to use PostgreSQL features
3. **CI/CD**: Configure PostgreSQL service for continuous integration
4. **Documentation**: Update setup guides for PostgreSQL requirements

### Database Migrations System
A robust migration system has been implemented to manage schema evolution:

#### Migration Architecture
- **Base Class Pattern**: All migrations inherit from `BaseMigration` class with standardized interface
- **Version-Based Tracking**: Sequential numbered migrations (001, 002, 003, etc.)
- **Dependency Management**: Each migration can declare dependencies on previous migrations
- **Transaction Safety**: All migrations run within database transactions for atomicity
- **Idempotent Operations**: Migrations can be run multiple times safely

#### Migration Components
```python
# Base migration class with SQLAlchemy integration
class BaseMigration:
    version: str = None  # e.g., "001"
    description: str = None
    dependencies: List[str] = []
    
    def upgrade(self, connection) -> None:
        """Apply the migration"""
        raise NotImplementedError
        
    def downgrade(self, connection) -> None:
        """Rollback the migration"""
        raise NotImplementedError
```

#### Migration Tracking
- **Applied Migrations Table**: `applied_migrations` table tracks completed migrations
- **Status Queries**: Real-time status of pending/applied migrations
- **History Tracking**: Complete audit trail of when migrations were applied
- **Precondition Validation**: Ensures dependencies are met before execution

#### CLI Tools
- **Migration Runner**: Python CLI tool for executing migrations
  ```bash
  python migrations/migration_runner.py status      # Show current status
  python migrations/migration_runner.py upgrade     # Apply pending migrations
  python migrations/migration_runner.py downgrade   # Rollback last migration
  python migrations/migration_runner.py history     # Show migration history
  ```
- **Shell Wrapper**: Convenience script `migrations/migrate.sh` for common operations
  ```bash
  ./migrations/migrate.sh status    # Quick status check
  ./migrations/migrate.sh upgrade   # Apply migrations with environment detection
  ```

#### Current Migration Timeline
1. **Migration 001**: Initial schema creation with icons table and indexes
2. **Migration 002**: Added rich metadata columns (JSONB support, additional fields)
3. **Migration 003**: Cleanup of duplicate columns and schema optimization

#### Migration Best Practices Discovered
- **Connection Parameter Passing**: Migrations receive SQLAlchemy connection objects for proper transaction management
- **PostgreSQL-Specific Features**: Migrations utilize native PostgreSQL types (ARRAY, JSONB)
- **Index Creation Strategy**: GIN indexes created for optimal search performance
- **Constraint Management**: Proper handling of unique constraints and foreign keys

## Implementation Details

### SQLAlchemy Model
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class IconModel(Base):
    __tablename__ = "icons"
    
    id = Column(Integer, primary_key=True)
    yoto_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    image_url = Column(Text, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    tags = Column(ARRAY(String), default=[])
    category = Column(String(100))
    description = Column(Text)
    icon_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### Database Configuration
```python
# Development and Production
DATABASE_URL = "postgresql://user:password@localhost:5432/story_curator"

# Test Database
TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/story_curator_test"
```

### Search Query Examples
```sql
-- Full-text search across names
SELECT * FROM icons 
WHERE to_tsvector('english', name) @@ plainto_tsquery('english', 'animal');

-- Tag array queries
SELECT * FROM icons WHERE 'nature' = ANY(tags);

-- JSONB metadata queries
SELECT * FROM icons WHERE icon_metadata @> '{"color": "blue"}';

-- Combined search with ranking
SELECT *, ts_rank(to_tsvector('english', name), query) as rank
FROM icons, plainto_tsquery('english', 'cat dog') query
WHERE to_tsvector('english', name) @@ query
ORDER BY rank DESC;
```

## Monitoring and Maintenance

### Performance Monitoring
- Query execution time tracking
- Index usage analysis
- Database size monitoring
- Connection pool metrics
- Migration execution time and success rates

### Maintenance Tasks
- Regular `ANALYZE` to update statistics
- Periodic `VACUUM` for space reclamation
- Index maintenance and rebuilding
- Backup and recovery procedures
- Migration status audits and validation

### Schema Evolution Management
- **Version Control Integration**: All migration files tracked in git
- **Testing Protocol**: Each migration tested against real PostgreSQL instance
- **Rollback Procedures**: Downgrade paths tested and documented
- **Production Deployment**: Staged migration process with status validation
- **Environment Consistency**: Same migration system across dev/staging/production

## Compliance

### Data Privacy
- No personally identifiable information stored
- Public icon data only
- Compliance with web scraping ethics

### Performance Requirements
- Search queries under 50ms (as per FR-004)
- Support for 10,000+ icons
- Concurrent user support

## References
- [PostgreSQL Array Documentation](https://www.postgresql.org/docs/current/arrays.html)
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [SQLAlchemy Migration Patterns](https://docs.sqlalchemy.org/en/20/core/metadata.html)
- FR-004-yoto-icons-db.md - Feature Specification
- ADR-003: Error Handling Strategy
- ADR-005: Type Safety Standards
- Migration System: `/migrations/` directory with version-controlled schema changes

---

**Decision Date**: August 26, 2025  
**Decision Makers**: GitHub Copilot (AI Agent)  
**Last Updated**: August 27, 2025  
**Review Date**: February 26, 2026  
**Status**: Accepted - Migration System Implemented
