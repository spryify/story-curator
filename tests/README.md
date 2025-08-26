# Media Apps Test Suite

This directory contains the test suite for the Media Apps project, focusing on comprehensive testing of the audio analysis functionality.

## Test Structure

```
tests/
├── conftest.py               # Shared test fixtures and configuration
├── fixtures/                # Test fixtures and data
│   ├── audio/              # Audio test fixtures and samples
│   │   ├── test_tone.wav   # Sample WAV audio
│   │   └── test_speech.mp3 # Sample MP3 audio
├── integration/             # Integration and end-to-end tests
│   └── audio_analysis/      
│       └── test_pipeline.py # Tests for complete audio analysis pipeline
└── unit/                    # Unit tests for individual components
    ├── core/               
    │   └── test_analyzer.py # Tests for core analyzer functionality
    └── processors/          # Tests for individual processors
        ├── audio/
        │   └── test_processor.py
        └── text/
            └── test_processor.py
```

## Test Categories

### Unit Tests

Located in `tests/unit/`, these tests verify individual components in isolation:

1. **Core Analyzer Tests** (`unit/core/test_analyzer.py`)
   - Initialization and configuration
   - File path validation and security
   - Audio file processing workflow
   - Error handling and validation
   - Performance metrics collection

2. **Audio Processor Tests** (`unit/processors/audio/test_processor.py`)
   - Audio format validation
   - File loading and metadata extraction
   - Text extraction from audio
   - Children's content processing
   - Story narrative recognition
   - Error handling for invalid inputs
   - Support for different audio formats

3. **Text Processor Tests** (`unit/processors/text/test_processor.py`)
   - Text summarization functionality
   - Length constraints handling
   - Special character handling
   - Error handling for invalid inputs

### Integration Tests

Located in `tests/integration/`, these tests verify component interactions:

1. **Audio Analysis Pipeline Tests** (`integration/audio_analysis/test_pipeline.py`)
   - End-to-end audio processing workflow
   - Multi-format support
   - Language support
   - Error propagation
   - Performance with different file sizes
   - Concurrent processing capabilities

## Test Data

The `tests/fixtures/audio/` directory contains test audio files:
- `test_tone.wav`: WAV format test file with generated tones
- `test_speech.mp3`: MP3 format test file with speech content
- `story_test.wav`: WAV format test file with children's story content

## Test Configuration

`conftest.py` provides shared test fixtures:

- `test_audio_file`: Access to sample audio files
- `story_speech_options`: Speech generation options optimized for children's content
- `sample_story_wav`: Sample children's story audio file
- `test_config`: Standard test configuration with settings for:
  - Audio processing (model, device, sample rate)
  - Text processing (summary length, confidence thresholds)
  - Supported formats and durations

## Running Tests

Run specific test categories:
```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with coverage
pytest --cov=media_analyzer

# Run tests for a specific component
pytest tests/unit/core/test_analyzer.py
```

## Test Design Principles

1. **Isolation**: Unit tests are designed to test components in isolation using mocks where appropriate.

2. **Security**: Tests verify security measures including:
   - Path traversal prevention
   - Input validation
   - Resource limits

3. **Error Handling**: Tests verify proper error handling for:
   - Invalid inputs
   - Resource constraints
   - File system issues
   - Processing errors

4. **Performance**: Tests include performance verification:
   - Processing time metrics
   - Resource usage
   - Concurrent processing capabilities

5. **Cross-platform**: Tests are designed to run on multiple platforms:
   - Path handling is platform-agnostic
   - Temporary directory usage follows platform conventions
   - File format support is consistent

## Contributing

When adding new tests:

1. Follow the established directory structure
2. Include both unit and integration tests for new features
3. Update test documentation when adding new test categories
4. Ensure tests are properly isolated and use fixtures
5. Add appropriate error handling tests
6. Include performance considerations
7. Follow naming conventions:
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

## Test Coverage Goals

The project maintains the following coverage targets:
- Line coverage: >90%
- Branch coverage: >85%
- Function coverage: >95%

Critical components (security, file handling, error handling) require 100% coverage.
