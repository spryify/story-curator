"""Example script showing how to use the icon curator CLI."""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a CLI command and display results."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd="story-curator"
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Exit code: {result.returncode}")
        
    except Exception as e:
        print(f"Error running command: {e}")


def main():
    """Demonstrate the icon curator CLI functionality."""
    
    print("Icon Curator CLI Demo")
    print("====================")
    
    python_path = "/Users/saparya/Documents/Projects/story-curator/.venv/bin/python"
    
    # Show help
    run_command(
        f"{python_path} -m src.icon_extractor.cli.main --help",
        "Show CLI help"
    )
    
    # Show stats (will fail gracefully if no database)
    run_command(
        f"{python_path} -m src.icon_extractor.cli.main stats",
        "Show database statistics"
    )
    
    # Show search help
    run_command(
        f"{python_path} -m src.icon_extractor.cli.main search --help",
        "Show search command help"
    )
    
    # Show scrape help
    run_command(
        f"{python_path} -m src.icon_extractor.cli.main scrape --help",
        "Show scrape command help"
    )
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    print("\nTo actually use the icon curator:")
    print("1. Set up a PostgreSQL database")
    print("2. Set DATABASE_URL environment variable")
    print("3. Run: python -m src.icon_extractor.cli.main scrape")
    print("4. Run: python -m src.icon_extractor.cli.main search 'your query'")


if __name__ == "__main__":
    main()
