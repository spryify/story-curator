#!/bin/bash

# Test runner script for the reorganized test structure
# Usage: ./scripts/run_tests.sh [module] [test_type] [pattern]
#
# Examples:
#   ./scripts/run_tests.sh                          # Run all tests
#   ./scripts/run_tests.sh media_analyzer           # Run all media_analyzer tests
#   ./scripts/run_tests.sh icon_extractor unit       # Run icon_extractor unit tests only
#   ./scripts/run_tests.sh media_analyzer integration test_audio  # Run audio integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"

# Ensure we're in the project directory
cd "$PROJECT_DIR"

MODULE="$1"
TEST_TYPE="$2"
PATTERN="$3"

# Build test path
TEST_PATH=""
if [ -n "$MODULE" ]; then
    if [ -n "$TEST_TYPE" ]; then
        TEST_PATH="src/$MODULE/tests_$TEST_TYPE/"
    else
        TEST_PATH="src/$MODULE/"
    fi
else
    TEST_PATH="src/"
fi

# Build pytest command
PYTEST_CMD="$PYTHON_CMD -m pytest $TEST_PATH"

if [ -n "$PATTERN" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $PATTERN"
fi

PYTEST_CMD="$PYTEST_CMD -v"

echo "Running tests with command: $PYTEST_CMD"
echo "=================================================="

# Run the tests
$PYTEST_CMD
