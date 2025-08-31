# ADR-010: Podcast Analysis Architecture

## Status
Accepted

## Context

The media analyzer system needs to support podcast episode analysis, including RSS feed processing, audio transcription, and content analysis. This capability extends the existing subject identification system to handle audio content from podcast feeds.

**Current System Capabilities:**
- Subject identification from text content
- Database storage for analyzed content
- CLI interface for content analysis
- Modular processor architecture

**New Requirements:**
- RSS feed parsing and episode discovery
- Audio transcription from streaming sources
- Integration with existing subject identification
- Scalable processing for large podcast archives

**Technical Constraints:**
- Memory efficient processing for large audio files
- Network resilient for unreliable podcast feeds
- Configurable transcription quality vs performance
- Integration with existing CLI and processor patterns

## Decision

We will implement a comprehensive podcast analysis architecture with four core components: PodcastAnalyzer for orchestration, RSSFeedConnector for feed processing, WhisperStreamingService for transcription, and integration with the existing SubjectIdentifier for content analysis.


### 1. Component Architecture

**Core Components:**
- **PodcastAnalyzer**: Main orchestrator for complete episode analysis
- **RSSFeedConnector**: RSS feed parsing and episode metadata extraction  
- **WhisperStreamingService**: Streaming audio transcription
- **SubjectIdentifier**: Story subject extraction (existing component)

**Data Flow:**
```
RSS URL → Episode Metadata → Audio Stream → Transcription → Subject Analysis → Results
```

### 2. RSS Feed Processing

**Implementation**: `RSSFeedConnector` class
- **XML Parsing**: Standard library `xml.etree.ElementTree` for RSS/XML parsing
- **Async HTTP**: `aiohttp` for non-blocking RSS feed fetching
- **Validation**: URL format validation and feed structure verification
- **Metadata Extraction**: Episode title, description, audio URL, duration, publication date

**Key Features:**
- Robust error handling for malformed feeds
- Support for common RSS extensions (iTunes, podcast namespaces)
- Duration parsing from multiple formats (ISO 8601, human readable)
- Audio URL extraction with format validation

### 3. Streaming Audio Transcription

**Implementation**: `WhisperStreamingService` class
- **Model**: OpenAI Whisper via `openai-whisper` package
- **Streaming**: Direct audio URL processing without local storage
- **Audio Processing**: `pydub` for format conversion and audio handling
- **Efficiency**: Configurable model sizes (tiny, base, small, medium, large)

**Architecture Pattern:**
```python
class WhisperStreamingService(StreamingTranscriptionService):
    """Whisper-based streaming transcription with audio stream processing."""
    
    async def transcribe_stream(self, audio_url: str) -> TranscriptionResult:
        # 1. Stream audio directly from URL
        # 2. Convert to Whisper-compatible format
        # 3. Process with selected Whisper model
        # 4. Return structured transcription result
```

### 4. Analysis Orchestration

**Implementation**: `PodcastAnalyzer` class
- **Configuration-Driven**: Flexible configuration for all services
- **Async Processing**: Non-blocking episode analysis
- **Error Isolation**: Component failures don't crash entire analysis
- **Resource Management**: Proper cleanup of audio streams and temporary files

**Analysis Pipeline:**
```python
async def analyze_episode(url: str, options: AnalysisOptions) -> StreamingAnalysisResult:
    # 1. Parse RSS feed and extract episode metadata
    # 2. Stream and transcribe episode audio  
    # 3. Extract subjects from transcription
    # 4. Return comprehensive analysis result
```

### 5. Data Models

**Core Models** (defined in `media_analyzer.models.podcast`):
- **PodcastEpisode**: Complete episode metadata (title, description, duration, etc.)
- **StreamingAnalysisResult**: Full analysis result with transcription and subjects
- **AnalysisOptions**: Configurable analysis parameters

**Integration Models**:
- **TranscriptionResult**: Audio transcription output (from `media_analyzer.models.audio`)
- **Subject**: Identified story subjects (from `media_analyzer.models.subject`)

### 6. Configuration Strategy

**Hierarchical Configuration:**
```python
config = {
    'rss': {
        'timeout_seconds': 30,
        'max_episodes': 10
    },
    'transcription': {
        'model_size': 'base',  # Whisper model size
        'language': 'en',      # Target language
        'timeout_seconds': 300
    },
    'subject_identification': {
        'max_workers': 3,
        'timeout_ms': 800
    }
}
```

**AnalysisOptions Defaults:**
- **Language**: 'en' (audio language for transcription)
- **Max Duration**: 180 minutes (episode length limit)
- **Segment Length**: 300 seconds (audio processing chunk size)
- **Confidence Threshold**: 0.5 (minimum confidence for subject extraction)
- **Subject Extraction**: enabled (toggle topic analysis)

### 7. CLI Integration

**Command Structure** (see [ADR-004](ADR-004-cli-architecture.md) for full CLI architecture):
```bash
# Basic episode analysis
python -m media_analyzer.cli podcast analyze "https://example.com/podcast.rss"

# With configuration options
python -m media_analyzer.cli podcast analyze "https://feeds.megaphone.fm/example" \
    --language en \
    --max-duration 120 \
    --confidence-threshold 0.7 \
    --output results.json

# Metadata-only extraction
python -m media_analyzer.cli podcast metadata "https://example.com/podcast.rss"
```

## Implementation Rationale

### RSS Processing
- **Standard Library XML**: Reliable, security-conscious, no additional dependencies
- **aiohttp**: Async HTTP for non-blocking feed fetching
- **URL Validation**: Security and reliability for external feed URLs

### Audio Transcription  
- **Whisper Selection**: Best-in-class accuracy for speech recognition
- **Streaming Approach**: Memory efficient for large podcast episodes
- **Model Configurability**: Balance between accuracy and performance

### Service Integration
- **Dependency Injection**: Services passed as constructor parameters
- **Interface Abstraction**: Base classes enable service swapping
- **Error Boundary Pattern**: Component failures contained and reported

## Consequences

### Positive
- **Modular Design**: Each component can be developed and tested independently
- **Async Performance**: Non-blocking I/O for RSS feeds and audio streams
- **Configuration Flexibility**: Easy to adjust transcription quality vs speed
- **Error Resilience**: Component failures don't cascade through system
- **Memory Efficiency**: Streaming processing avoids loading entire episodes
- **Testing Clarity**: Clear unit/integration test separation per component

### Negative  
- **Complexity**: Multiple services require coordination and configuration
- **External Dependencies**: RSS feeds and audio URLs can be unreliable
- **Resource Requirements**: Whisper models require significant memory/compute
- **Network Dependency**: Requires internet access for RSS feeds and audio streams

### Technical Debt
- **Audio Format Support**: Currently optimized for common podcast formats
- **Rate Limiting**: No built-in rate limiting for RSS feed requests
- **Caching Strategy**: Limited caching of transcription results
- **Batch Processing**: Single-episode focus, no batch optimization

## Related ADRs
- [ADR-001: Core Architecture](ADR-001-core-architecture.md) - Overall system design
- [ADR-003: Error Handling](ADR-003-error-handling.md) - Error boundary patterns
- [ADR-006: Testing Strategy](ADR-006-testing-strategy.md) - Component testing approach
- [ADR-008: Subject Identification](ADR-008-subject-identification-strategy.md) - Subject processing integration

## Future Considerations
- **Real-time Processing**: Live podcast stream analysis
- **Batch Episode Processing**: Multiple episode analysis optimization
- **Advanced Audio Features**: Speaker identification, segment analysis
- **Alternative Transcription**: Support for other speech recognition services
- **Content Classification**: Age-appropriate content detection
- **Multilingual Support**: Enhanced language detection and processing
