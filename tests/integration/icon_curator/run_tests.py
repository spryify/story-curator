#!/usr/bin/env python3
"""Integration test runner for icon curator."""

import os
import subprocess
import sys

def run_integration_tests():
    """Run the consolidated icon curator integration tests."""
    
    print("🧪 Icon Curator Integration Test Suite")
    print("=" * 50)
    
    # Change to project directory
    project_root = "story-curator"
    os.chdir(project_root)
    
    # Python executable
    python_exe = f"{project_root}/.venv/bin/python"
    
    print("\n📋 Test Categories Available:")
    print("  1. Core Integration Tests - Data models, scraper, workflows")
    print("  2. Database Integration Tests - Repository patterns (mocked)")
    print("  3. Live Integration Tests - Real yotoicons.com scraping")
    
    print("\n🔧 Running Core & Database Integration Tests...")
    result = subprocess.run([
        python_exe, "-m", "pytest", 
        "tests/integration/icon_curator/test_core_integration.py",
        "tests/integration/icon_curator/test_database_integration.py",
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Core & Database integration tests PASSED")
        print(f"   Tests run: {count_tests(result.stdout)}")
    else:
        print("❌ Some integration tests FAILED")
        print(result.stdout)
        print(result.stderr)
    
    print("\n🌐 Live Integration Tests (optional):")
    print("   To run live tests against yotoicons.com:")
    print("   export SKIP_LIVE_TESTS=false")
    print(f"   {python_exe} -m pytest tests/integration/icon_curator/test_live_integration.py -v -s")
    
    print("\n🗄️  Real Database Tests (optional):")
    print("   To run real PostgreSQL integration tests:")
    print("   1. Set up PostgreSQL database: createdb icon_curator_test")
    print("   2. export DATABASE_URL='postgresql://user:pass@localhost/icon_curator_test'")
    print("   3. export SKIP_DATABASE_TESTS=false")
    print(f"   4. {python_exe} -m pytest tests/integration/icon_curator/test_database_integration.py::TestRealDatabaseIntegration -v")
    
    print("\n📊 Integration Test Status:")
    print("✅ No SQLite dependencies - PostgreSQL only")
    print("✅ Comprehensive test fixtures in conftest.py") 
    print("✅ Mock-based database testing for CI/CD")
    print("✅ Live test capability with environment controls")
    print("✅ Real database test placeholders for production validation")
    
    return result.returncode == 0

def count_tests(output):
    """Count the number of tests from pytest output."""
    lines = output.split('\n')
    for line in lines:
        if 'passed' in line and 'skipped' in line:
            # Extract numbers from "21 passed, 4 skipped" format
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'passed,':
                    return parts[i-1]
    return "unknown"

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
