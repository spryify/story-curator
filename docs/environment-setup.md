# Environment Setup Guide

## Prerequisites

### PostgreSQL Database
The Icon Curator feature requires PostgreSQL for both development and production:

1. **Install PostgreSQL**:
   - **macOS**: `brew install postgresql`
   - **Ubuntu**: `sudo apt-get install postgresql postgresql-contrib`
   - **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

2. **Start PostgreSQL service**:
   - **macOS**: `brew services start postgresql`
   - **Ubuntu**: `sudo systemctl start postgresql`
   - **Windows**: Use Services application

3. **Create databases**:
   ```bash
   createdb story_curator_dev
   createdb story_curator_test
   ```

4. **Set environment variables** (optional):
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=story_curator_dev
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   export TEST_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/story_curator_test
   ```

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

After installation, both `media-analyzer` and `icon-curator` commands will be available in your environment.

### Media Analyzer Examples
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

### Icon Curator Examples
```bash
# Get help on available commands
icon-curator --help

# Scrape and store icons from yotoicons.com
icon-curator scrape

# Search for icons by keyword
icon-curator search "animal"

# Get statistics about stored icons
icon-curator stats

# Search with category filter
icon-curator search "nature" --category "outdoors" --limit 20
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
