# Environment Setup Guide

## Quick Setup (Recommended)

For a complete development environment setup, run:

```bash
python scripts/setup_environment.py
```

This automated script will:
- ✅ Install all Python dependencies (production + development)
- ✅ Install the package in development mode
- ✅ Download required NLTK data (stopwords, tokenizers, etc.)
- ✅ Download spaCy English model
- ✅ Verify all critical dependencies
- ✅ Set up environment variables

## Manual Setup

### Prerequisites

#### System Dependencies
- **Python 3.9 or higher**
- **PostgreSQL** (required for Icon Curator feature)
- **System packages** (Ubuntu/Debian):
  ```bash
  sudo apt-get install ffmpeg portaudio19-dev
  ```

#### PostgreSQL Database Setup
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

### Python Environment Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     .\venv\Scripts\activate
     ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Download NLTK data**:
   ```python
   import nltk
   nltk.download('stopwords')
   nltk.download('punkt')
   nltk.download('wordnet')
   nltk.download('averaged_perceptron_tagger')
   ```

5. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Testing

After setup, verify everything works:

```bash
# Run all tests
pytest src/

# Run only unit tests (fast)
pytest src/ -m "not integration"

# Run only integration tests
pytest src/ -m "integration"
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

## Troubleshooting

### Common Issues

- **NLTK data issues:** The automated setup script will skip failed downloads and continue. You can manually download specific datasets if needed.
- **spaCy model issues:** Integration tests may fail if the English model isn't available. Ensure `en_core_web_sm` is installed.
- **ffmpeg issues:** Make sure both system ffmpeg and ffmpeg-python are installed for audio processing.
- **Import errors:** Ensure the package is installed in development mode (`pip install -e .`).
- **PostgreSQL connection issues:** Verify PostgreSQL service is running and databases are created.

### General Troubleshooting Steps

1. Ensure your virtual environment is activated
2. Verify your Python version (3.9 or higher required)
3. Check the logs for detailed error messages
4. Consult the documentation in the `docs/` directory
