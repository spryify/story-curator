# CLI Package

This package contains the command-line interface modules for the media-analyzer application.

## Structure

- `audio.py` - Contains the CLI commands for audio file processing
  - Main command group: `media-analyzer`
  - Subcommands:
    - `transcribe` - Transcribe and analyze audio files

## Usage

After installing the package, you can use the CLI as follows:

```bash
# Get help
media-analyzer --help

# Transcribe an audio file
media-analyzer transcribe path/to/audio.wav --language en

# Transcribe with custom summary length and save to file
media-analyzer transcribe speech.wav -l en -s 500 -o output.txt

# Show detailed processing information
media-analyzer transcribe audio.mp3 --verbose
```

## Adding New Commands

When adding new commands:
1. Create a new module for the command group if needed
2. Use Click decorators to define commands and options
3. Update the `__init__.py` to export the new command group
4. Update setup.py entry points if adding a new main command

## Development

Follow these best practices:
- Use Click for command-line argument parsing
- Use Rich for terminal output formatting
- Include comprehensive help messages
- Provide meaningful error messages
- Add verbose output options for debugging
