#!/usr/bin/env bash
#
# Convenience script for running PostgreSQL database migrations.
#
# This script provides a simpler interface for common migration operations.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_RUNNER="$SCRIPT_DIR/migration_runner.py"
PYTHON_CMD="${PYTHON_CMD:-python}"

# Default database URL (can be overridden with DATABASE_URL environment variable)
DEFAULT_DB_URL="postgresql://postgres:@localhost:5432/icon_curator_dev"
DATABASE_URL="${DATABASE_URL:-$DEFAULT_DB_URL}"

# Check if virtual environment is activated
if [[ -n "$VIRTUAL_ENV" ]]; then
    PYTHON_CMD="$VIRTUAL_ENV/bin/python"
elif [[ -f "$SCRIPT_DIR/../.venv/bin/python" ]]; then
    PYTHON_CMD="$SCRIPT_DIR/../.venv/bin/python"
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status      Show current migration status"
    echo "  upgrade     Apply all pending migrations"
    echo "  downgrade   Rollback to specific version"
    echo "  history     Show migration history"
    echo "  help        Show this help message"
    echo ""
    echo "Options:"
    echo "  -v, --verbose          Verbose output"
    echo "  --database-url URL     Custom database URL"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL    PostgreSQL connection URL (default: $DEFAULT_DB_URL)"
    echo ""
    echo "Examples:"
    echo "  $0 status                                    # Show status"
    echo "  $0 upgrade                                   # Apply all migrations"
    echo "  $0 upgrade Migration002AddRichMetadata      # Upgrade to specific version"
    echo "  $0 downgrade Migration001InitialSchema      # Downgrade to specific version"
    echo "  $0 -v status                                # Verbose status"
    echo ""
}

# Parse arguments
VERBOSE=""
CUSTOM_DB_URL=""
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --database-url)
            CUSTOM_DB_URL="--database-url $2"
            shift 2
            ;;
        status|upgrade|downgrade|history|help)
            COMMAND="$1"
            shift
            break
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set database URL argument
if [[ -n "$CUSTOM_DB_URL" ]]; then
    DB_URL_ARG="$CUSTOM_DB_URL"
else
    DB_URL_ARG="--database-url $DATABASE_URL"
fi

# Handle commands
case $COMMAND in
    help|"")
        show_usage
        exit 0
        ;;
    status|history)
        exec "$PYTHON_CMD" "$MIGRATION_RUNNER" $VERBOSE $DB_URL_ARG "$COMMAND"
        ;;
    upgrade)
        if [[ $# -gt 0 ]]; then
            # Upgrade to specific version
            exec "$PYTHON_CMD" "$MIGRATION_RUNNER" $VERBOSE $DB_URL_ARG "$COMMAND" "$1"
        else
            # Upgrade to latest
            exec "$PYTHON_CMD" "$MIGRATION_RUNNER" $VERBOSE $DB_URL_ARG "$COMMAND"
        fi
        ;;
    downgrade)
        if [[ $# -eq 0 ]]; then
            echo "Error: downgrade command requires a target version"
            echo "Example: $0 downgrade Migration001InitialSchema"
            exit 1
        fi
        exec "$PYTHON_CMD" "$MIGRATION_RUNNER" $VERBOSE $DB_URL_ARG "$COMMAND" "$1"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
