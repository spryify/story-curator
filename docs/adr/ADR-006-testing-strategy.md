# ADR-006: Testing Strategy

## Status
Accepted

## Context
The Story Curator requires comprehensive testing to ensure reliability, maintainability, and correctness. Given the system's complex dependencies (SpaCy models, Whisper AI, PostgreSQL database), we need a clear testing strategy that provides both fast development feedback and real-world validation.

## Decision
We will implement a **strict two-tier testing strategy** with complete separation between unit and integration tests:

### 1. Unit Tests (`tests_unit/`) - MOCK ALL DEPENDENCIES
**Philosophy**: Complete component isolation using mocks for all external dependencies

**Organization:**
```
src/component/tests_unit/
├── cli/              # CLI unit tests (mocked processors)
├── core/             # Core component tests (mocked models)
├── processors/       # Processor tests (mocked external services)
│   ├── audio/       # Audio processor tests (mocked Whisper)
│   ├── subject/     # Subject processor tests (mocked SpaCy)
│   └── text/        # Text processor tests (mocked algorithms)
├── models/          # Data model tests (no external deps)
└── utils/           # Utility function tests (mocked I/O)
```

**Mock Strategy:**
- **SpaCy Models**: Mock `spacy.load()` and NLP pipeline components
- **Database Operations**: Mock all PostgreSQL connections and queries
- **File I/O**: Mock file system operations and audio loading
- **External APIs**: Mock Whisper, audio processing libraries
- **System Calls**: Mock OS-specific operations (e.g., `say` command)

### 2. Integration Tests (`tests_integration/`) - NO MOCKS
**Philosophy**: Real component interaction validation with actual dependencies

**Organization:**
## Directory Structure

Tests are organized to mirror the source code structure for easy navigation:

```
src/media_analyzer/
├── processors/
│   ├── audio/
│   │   └── audio_processor.py
│   ├── podcast/  
│   │   ├── analyzer.py
│   │   └── rss_connector.py
│   ├── subject/
│   │   ├── processors/
│   │   │   ├── entity_processor.py
│   │   │   ├── keyword_processor.py
│   │   │   └── topic_processor.py
│   │   └── subject_identifier.py
│   └── text/
│       └── text_processor.py
├── tests_unit/                    # Fast, isolated unit tests
│   └── processors/
│       ├── audio/
│       ├── podcast/
│       ├── subject/
│       │   ├── test_entity_processor.py         # Mocked SpaCy
│       │   ├── test_keyword_processor.py
│       │   ├── test_topic_processor.py
│       │   └── test_subject_identification.py   # Mocked dependencies
│       └── text/
└── tests_integration/             # Real dependency integration tests
    └── processors/
        ├── audio/
        │   └── test_audio_processor_integration.py      # Real Whisper
        ├── podcast/
        │   └── test_podcast_analyzer_integration.py     # Real RSS feeds
        ├── subject/
        │   ├── processors/
        │   │   └── test_entity_processor_integration.py # Real SpaCy model
        │   ├── test_subject_identifier_integration.py   # Real external deps
        │   └── test_subject_pipeline_integration.py     # Full audio->subjects
        └── text/
```

**Real Component Strategy:**
- **SpaCy Models**: Load and execute actual `en_core_web_sm` model
- **Database Operations**: Real PostgreSQL database with test schema
- **Audio Processing**: Real Whisper model execution and file processing
- **Pipeline Integration**: Complete end-to-end workflows with real data

### 3. Test Execution Strategy

**Unit Tests** - Development Workflow:
```bash
# Fast feedback during development (runs in ~12 seconds)
pytest src/media_analyzer/tests_unit/ -v              # All unit tests
pytest src/media_analyzer/tests_unit/processors/subject/ -v  # Subject processing only
pytest src/media_analyzer/tests_unit/processors/audio/ -v   # Audio processing only
```

**Integration Tests** - Validation Workflow:
```bash
# Real component validation (slower, more comprehensive ~63 seconds)
pytest src/media_analyzer/tests_integration/ -v       # All integration tests
pytest src/media_analyzer/tests_integration/processors/subject/ -v  # Subject integration
pytest src/media_analyzer/tests_integration/processors/audio/ -v    # Audio integration
```

**Specific Test Categories**:
```bash
# Test specific processors with both unit and integration
pytest src/media_analyzer/tests_unit/processors/subject/test_entity_processor.py -v
pytest src/media_analyzer/tests_integration/processors/subject/processors/test_entity_processor_integration.py -v

# Test complete pipelines (integration only)
pytest src/media_analyzer/tests_integration/processors/subject/test_subject_pipeline_integration.py -v
```

### 4. Coverage Requirements
- **Unit Test Coverage**: 95%+ (isolated component logic)
- **Integration Test Coverage**: 80%+ (real component interactions)
- **Critical Path Coverage**: 100% (both unit and integration)
- **Branch Coverage**: 90%+ (comprehensive scenario coverage)

### 5. Testing Tools
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting and enforcement
- **pytest-mock**: Mocking framework for unit tests
- **unittest.mock**: Python standard library mocking
- **pytest-benchmark**: Performance testing for integration tests

## Consequences

### Positive
- **Fast Development Feedback**: Unit tests provide immediate validation in <30 seconds
- **Real-World Confidence**: Integration tests ensure actual component compatibility
- **Clear Test Purpose**: Developers know exactly what each test type validates
- **Debugging Efficiency**: Unit test failures indicate logic issues, integration failures indicate dependency issues
- **CI/CD Optimization**: Unit tests run on every commit, integration tests on pull requests
- **Maintenance Clarity**: Mock changes don't affect integration test validity

### Negative
- **Dual Maintenance**: Both unit and integration tests require maintenance
- **Mock Synchronization**: Unit test mocks must stay synchronized with real interfaces
- **Integration Test Complexity**: Real dependencies require more sophisticated test setup
- **Resource Requirements**: Integration tests need actual models and database access
- **Time Investment**: Initial setup requires creating both mock and real test scenarios

## Implementation Notes

### 1. Unit Test Implementation with Mocks

**SpaCy Model Mocking:**
```python
@pytest.fixture
def mock_entity_processor():
    """EntityProcessor with mocked SpaCy model for unit testing."""
    with patch('spacy.load') as mock_load:
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_doc.ents = [Mock(text="Alice", label_="PERSON")]
        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp
        yield EntityProcessor()

def test_entity_extraction_logic(mock_entity_processor):
    """Test entity extraction logic without loading real models."""
    result = mock_entity_processor.process("Alice met Bob")
    assert len(result.entities) == 1
    assert result.entities[0].text == "Alice"
```

**Database Mocking:**
```python
@pytest.fixture
def mock_icon_service():
    """IconExtractionService with mocked database for unit testing."""
    with patch('src.icon_extractor.database.connection.get_connection'):
        service = IconExtractionService()
        service.search = Mock(return_value=[
            IconResult(name="story", url="http://example.com", score=0.95)
        ])
        yield service
```

### 2. Integration Test Implementation with Real Components

**Real SpaCy Model Usage:**
```python
@pytest.fixture
def entity_processor():
    """EntityProcessor with real SpaCy model for integration testing."""
    return EntityProcessor()  # Loads actual en_core_web_sm model

def test_real_entity_recognition(entity_processor):
    """Test entity recognition with actual SpaCy model."""
    text = "Alice visited the magical forest with Bob."
    result = entity_processor.process(text)
    
    # Verify real model correctly identifies entities
    person_entities = [e for e in result.entities if e.label == "PERSON"]
    assert len(person_entities) >= 2
    assert any(e.text in ["Alice", "Bob"] for e in person_entities)
```

**Real Audio Generation:**
```python
@pytest.fixture
def story_audio_files(tmp_path):
    """Generate real audio files using macOS 'say' command."""
    stories = {
        "magic_garden": "Once upon a time, there was a magical garden...",
        "ocean_adventure": "Deep beneath the ocean waves..."
    }
    
    audio_files = {}
    for story_name, story_text in stories.items():
        audio_path = tmp_path / f"{story_name}.wav"
        create_story_audio_file(audio_path, story_text, voice="Samantha")
        audio_files[story_name] = audio_path
    
    return audio_files
```

### 3. Test Isolation and Mock Management

**Mock Fixture Management:**
```python
# Centralized mock fixtures in conftest.py
@pytest.fixture(autouse=True)
def reset_spacy_cache():
    """Ensure SpaCy models don't leak between unit tests."""
    import spacy
    spacy.util.registry._get_all().clear()
    yield
    spacy.util.registry._get_all().clear()

@pytest.fixture
def mock_whisper_model():
    """Centralized Whisper mock for consistent behavior."""
    with patch('whisper.load_model') as mock_load:
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Mock transcription result',
            'language': 'en'
        }
        mock_load.return_value = mock_model
        yield mock_model
```

**Integration Test Environment:**
```python
# Environment setup for integration tests
@pytest.fixture(scope="session")
def integration_database():
    """Set up real PostgreSQL database for integration tests."""
    db_url = os.getenv('TEST_DATABASE_URL')
    if not db_url:
        pytest.skip("Integration tests require TEST_DATABASE_URL")
    
    # Create test schema and populate with test data
    setup_test_database(db_url)
    yield db_url
    cleanup_test_database(db_url)
```

### 4. Benefits of This Strategy

**Unit Test Benefits:**
- **Speed**: Complete suite runs in under 30 seconds
- **Isolation**: No external dependencies can break tests
- **Determinism**: Consistent results regardless of environment
- **Focus**: Tests component logic, not integration complexity

**Integration Test Benefits:**
- **Reality Check**: Ensures components work with actual dependencies
- **Performance Validation**: Real processing times and resource usage
- **Compatibility**: Verifies model versions and API compatibility
- **Confidence**: End-to-end validation with real data flows

## References
- [Clean Architecture](ADR-001-core-architecture.md) - Component isolation principles
- [Error Handling](ADR-003-error-handling.md) - Testing error scenarios
- [Type Safety](ADR-005-type-safety.md) - Testing with proper types
- pytest documentation - Testing framework best practices
- unittest.mock documentation - Mocking strategies and patterns
