# Environment Setup Guide

## Virtual Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     .\venv\Scripts\activate
     ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Using the CLI

After installation, the `media-analyzer` command will be available in your environment. Here are some example commands:

```bash
# Get help on available commands
media-analyzer --help

# Transcribe an audio file
media-analyzer transcribe path/to/audio.wav --language en

# Transcribe with custom options
media-analyzer transcribe audio.wav --language en --summary-length 500 --output results.txt

# Show detailed processing information
media-analyzer transcribe audio.mp3 --verbose
```

## Development Dependencies

For development work, install additional dependencies:
```bash
pip install -r requirements-dev.txt
```

## Troubleshooting

If you encounter issues:
1. Ensure your virtual environment is activated
2. Verify your Python version (3.9 or higher required)
3. Check the logs for detailed error messages
4. Consult the documentation in the `docs/` directory
