# Feature Requirement: Audio-to-Icon Pipeline with Podcast Support

**Feature ID**: FR-005-audio-to-icon-pipeline  
**Title**: Audio Content to Icon Matching Pipeline (Local Files & Podcasts)  
**Priority**: High  
**Status**: Draft  
**Assigned To**: AI Development Agent  
**Created**: 2025-08-27  
**Updated**: 2025-   - [ ] **NEW**: Integrate podcast components with existing audio_icon_matcher framework8-30

## Executive Summary

**Brief Description**: An end-to-end pipeline that analyzes both local audio files and streaming podcast episodes to identify primary subjects and automatically finds corresponding icons from the Yoto icon database.

**Business Value**: Enables automated icon discovery for both local audio content and podcast episodes from streaming platforms, reducing manual curation time and expanding content analysis capabilities to the vast ecosystem of podcast content. This supports content categorization accuracy for children's educational materials and podcast discovery workflows.

**Success Criteria**: Successfully match 85% of audio files and podcast episodes with relevant icons, with processing time under 30 seconds per local file and under 5 minutes for podcast episodes, achieving user satisfaction rating above 4.0/5.0.

## User Stories

### Primary User Story
```
As a content curator
I want to provide either a local audio file or a podcast episode URL and automatically get relevant icon suggestions
So that I can quickly categorize and visualize audio content from any source without manual searching
```

### Additional User Stories
```
As a content creator
I want to upload story audio files or provide podcast URLs and receive thematic icons
So that I can enhance my content with appropriate visual elements regardless of content source

As a podcast researcher
I want to analyze podcast episodes from streaming platforms by providing URLs
So that I can understand the topics and themes without downloading entire episodes

As a parent/educator
I want both local audio content and podcast episodes to be automatically tagged with visual icons
So that children can more easily identify and select content that interests them

As a system administrator
I want the audio-to-icon pipeline to handle both local files and streaming content reliably
So that it can support diverse content analysis workflows
```

## Functional Requirements

### Core Functionality
1. **Local Audio Processing**: Accept various audio formats (WAV, MP3, M4A) from local files and extract transcribed text using Whisper integration
2. **Podcast Episode Processing**: Accept podcast episode URLs from streaming platforms (RSS feeds, direct episode links) and process streaming audio
3. **Platform Integration**: Support for major podcast platforms through RSS feeds and direct audio stream access
4. **Subject Identification**: Analyze transcribed text to identify primary subjects, themes, and key entities relevant to children's content
5. **Icon Matching**: Query the Yoto icon database to find icons that match identified subjects with confidence scoring
6. **Results Compilation**: Return ranked list of matching icons with metadata and confidence scores
7. **Batch Processing**: Support processing multiple audio files and podcast episodes in sequence or parallel

### Input/Output Specifications
- **Inputs**: 
  - **Local Audio**: Audio file path or binary data (WAV, MP3, M4A formats)
  - **Podcast Episodes**: Podcast episode URLs (RSS feeds, direct episode links)
  - **Configuration**: Optional parameters (confidence threshold, max results, subject types)
  - **Context**: Optional context hints (target age group, content category, episode metadata)
- **Outputs**: 
  - JSON response with ranked icon matches
  - Processing metadata (transcription confidence, processing time, subject analysis results)
  - **Enhanced Podcast Data**: Episode metadata (title, description, duration, show name, publication date)
  - **Streaming Analytics**: Platform-specific metadata and streaming quality information
  - Error responses with detailed diagnostic information
- **Data Flow**: 
  - **Local**: Audio File → Transcription → Subject Analysis → Icon Database Query → Ranked Results
  - **Podcast**: Episode URL → Platform API → Audio Stream → Transcription → Subject Analysis → Icon Database Query → Ranked Results

### Behavior Specifications
- **Normal Operation**: 
  - **Local Files**: Process audio file end-to-end returning top 5 icon matches with confidence scores above 0.7
  - **Podcast Episodes**: Accept episode URL, authenticate with platform APIs when needed, stream audio segments for transcription, process results through analysis pipeline
- **Edge Cases**: 
  - Handle silent audio, multiple subjects, ambiguous content, and files with no clear subject matter
  - **Podcast-Specific**: Private/restricted content, rate limiting, network interruptions, partial transcriptions, multi-language content
- **Error Conditions**: 
  - Graceful handling of corrupted audio files, database connection failures, and processing timeouts
  - **Podcast-Specific**: Invalid URLs, platform API failures, transcription service limits, unsupported streaming formats

## Non-Functional Requirements

### Performance Requirements
- **Response Time**: 
  - Local files: Complete processing within 30 seconds for audio files up to 5 minutes
  - Podcast episodes: Complete analysis within 5 minutes for episodes up to 3 hours
- **Throughput**: Handle 10 concurrent requests (mix of local files and podcast episodes) with linear scaling
- **Memory Usage**: 
  - Maximum 512MB per local audio file processing session
  - Maximum 1GB RAM per concurrent podcast episode analysis
- **CPU Usage**: Efficient use of available CPU cores for parallel processing components with minimal local compute for streaming content

### Security Requirements
- **Input Validation**: Validate audio file formats and sizes, and sanitize podcast URLs to prevent injection attacks
- **Data Protection**: 
  - Secure handling of potentially sensitive local audio content with no persistent storage
  - Secure handling of platform API keys and user authentication tokens for podcast access
- **Access Control**: 
  - API-based access control for batch processing capabilities
  - Respect platform content policies and user access permissions for podcast content
- **Audit Requirements**: Log all processing attempts and platform API calls with anonymized metadata for performance monitoring and compliance

### Reliability Requirements
- **Availability**: 99.5% uptime for processing requests
- **Error Handling**: Comprehensive error recovery with detailed error codes and user-friendly messages
- **Recovery**: Automatic retry logic for transient failures with exponential backoff
- **Data Integrity**: Ensure consistent results for identical inputs and maintain database connection integrity

### Usability Requirements
- **User Interface**: Clear CLI interface with progress indicators and verbose mode
- **Accessibility**: Support for various audio content types including children's stories, educational content, and music
- **Documentation**: Complete API documentation with examples and troubleshooting guide
- **Error Messages**: Clear, actionable error messages that help users resolve issues

## Technical Specifications

### Architecture Integration
- **Related ADRs**: 
  - ADR-001 (Core Architecture)
  - ADR-002 (Plugin Architecture) 
  - ADR-008 (Subject Identification Strategy)
  - ADR-009 (Database Design)
  - ADR-010 (Podcast Analysis Architecture) - **NEW for podcast support**

### Component Design

**Current Implementation Status**: The `audio_icon_matcher` component already provides a functional implementation of the core local audio processing pipeline with CLI interface. This document describes both the existing functionality and planned enhancements for podcast support.

- **Existing Components (audio_icon_matcher)**: 
  - AudioIconPipeline (main orchestrator for local audio files)
  - CLI interface with process, validate, formats, and info commands
  - Full integration with media_analyzer subject identification
  - Complete local audio file processing workflow
- **New Components (to be implemented)**: 
  - **Podcast-Specific Components**:
    - PodcastAnalyzer (podcast episode orchestration)
    - RSSFeedConnector (RSS feed parsing and episode metadata extraction)
    - WhisperStreamingService (streaming audio transcription)
- **Components to be Modified**: 
  - AudioIconPipeline (add podcast episode processing support)
  - CLI interface (add podcast-specific commands and options)
  - SubjectIdentifier (from media_analyzer - enhanced podcast-specific content patterns)
  - DatabaseManager (icon search optimization)
- **Integration Points**: 
  - Audio Icon Matcher framework integration
  - Icon Extractor database connectivity
  - CLI command interface (supporting both file paths and URLs)
  - **Podcast Platform Integration**: RSS feed processors and streaming audio handlers

### Data Model
- **Data Structures**: 
  ```python
  @dataclass
  class AudioToIconRequest:
      # Support both local files and podcast URLs
      audio_source: Union[Path, str]  # File path or podcast URL
      source_type: Literal["local", "podcast"]  # Source type indicator
      max_results: int = 5
      confidence_threshold: float = 0.7
      context_hints: Optional[Dict[str, Any]] = None

  @dataclass  
  class IconMatch:
      icon_id: str
      icon_name: str
      icon_path: Path
      confidence_score: float
      matching_subjects: List[str]
      metadata: Dict[str, Any]

  @dataclass
  class AudioToIconResponse:
      matches: List[IconMatch]
      processing_metadata: Dict[str, Any]
      transcription_text: str
      identified_subjects: List[str]
      # Enhanced for podcast support
      source_metadata: Optional[Dict[str, Any]] = None  # Episode metadata for podcasts

  # Podcast-specific data structures
  @dataclass
  class PodcastEpisode:
      url: str
      title: str
      description: str
      duration_seconds: int
      publication_date: datetime
      show_name: str
      audio_url: str
      
  @dataclass
  class StreamingAnalysisResult:
      episode: PodcastEpisode
      transcription: str
      subjects: List[str]
      matched_icons: List[IconMatch]
      processing_metadata: Dict[str, Any]
  ```
- **Database Changes**: 
  - Add indexing on icon subjects and themes for faster matching queries
  - **NEW**: Podcast episode cache table for processed episodes and analysis history
- **Configuration**: 
  - Pipeline configuration for timeouts, thresholds, and processing options
  - **NEW**: RSS feed processing settings, streaming transcription service configuration

### API Design

**Current Implementation**: The following API already exists in the `audio_icon_matcher` component:

```python
# Existing AudioIconPipeline class
class AudioIconPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the audio-to-icon pipeline."""
        pass
    
    def process(
        self, 
        audio_file: str, 
        max_icons: int = 10,
        confidence_threshold: float = 0.3
    ) -> AudioIconResult:
        """Process a single audio file and return icon matches."""
        pass
    
    def validate_audio_file(self, audio_file: str) -> bool:
        """Validate an audio file for processing."""
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        pass
```

**Planned Extensions for Podcast Support**:

```python
# New podcast-specific API components
class PodcastAnalyzer:
    def analyze_episode(self, url: str, options: AnalysisOptions = None) -> StreamingAnalysisResult:
        """Analyze a single podcast episode from URL."""
        pass
    
    def analyze_from_rss(self, rss_url: str, episode_filter: Optional[Dict] = None) -> List[StreamingAnalysisResult]:
        """Analyze episodes from an RSS feed with optional filtering."""
        pass
```

## Podcast-Specific Requirements

### Supported Platforms and Sources
- **RSS Feeds**: Generic podcast RSS/XML feed processing
- **Direct Audio URLs**: Direct MP3/M4A episode links
- **Platform URLs**: Episode links from major platforms (when accessible)

### Podcast Processing Pipeline
```
Episode URL → RSS Feed Parser → Episode Metadata → Audio Stream → 
Transcription Service → Subject Analysis → Icon Matching → Enhanced Results
```

### Podcast-Specific Configuration
```python
@dataclass
class PodcastAnalysisOptions:
    language: str = "en"  # Audio language for transcription
    max_duration_minutes: int = 180  # Maximum episode length to process
    segment_length_seconds: int = 300  # Audio processing chunk size
    confidence_threshold: float = 0.5  # Minimum confidence for subject extraction
    extract_subjects: bool = True  # Enable/disable topic analysis
    
    # RSS-specific options
    max_episodes_per_feed: int = 10  # Limit episodes per RSS feed
    episode_age_limit_days: Optional[int] = 30  # Only process recent episodes
```

### Enhanced CLI Interface
```bash
# Local audio file processing (current implementation)
audio-icon-matcher process /path/to/audio.mp3
audio-icon-matcher process /path/to/audio.mp3 --max-icons 15 --confidence-threshold 0.5
audio-icon-matcher process /path/to/audio.mp3 --output-format json --output-file results.json

# Additional utility commands
audio-icon-matcher validate /path/to/audio.mp3    # Validate audio file
audio-icon-matcher formats                        # List supported formats
audio-icon-matcher info                          # Show tool information

# Podcast episode processing (planned enhancement)
# Note: The following commands represent planned functionality that will be added
# to support podcast episodes as described in this FR-005 requirement
audio-icon-matcher process-podcast "https://example.com/podcast.rss"
audio-icon-matcher process-podcast "https://example.com/episode.mp3" \
    --language en \
    --max-duration 120 \
    --confidence-threshold 0.7 \
    --output-format json \
    --output-file results.json

# Batch processing with mixed sources (planned enhancement)
audio-icon-matcher batch \
    /path/to/audio1.mp3 \
    --podcast "https://example.com/episode1.mp3" \
    /path/to/audio2.wav \
    --podcast "https://feeds.example.com/show.rss"
```

## Implementation Guidance for AI Agents

### Required Templates
- **Primary Template**: pipeline_template.py (for main orchestrator)
- **Supporting Templates**: processor_template.py, database_query_template.py, cli_command_template.py
- **NEW Podcast Templates**: podcast_processor_template.py, rss_connector_template.py

### Required Examples
- **Reference Examples**: icon_extractor_demo.py (for database integration patterns)
- **Similar Implementations**: audio_icon_matcher CLI structure, subject identification patterns

### Implementation Steps
1. **Setup Phase**
   - [ ] Read related ADRs: ADR-001, ADR-002, ADR-008, ADR-009, **ADR-010** (podcast architecture)
   - [ ] Review templates: pipeline_template.py, processor_template.py, **podcast_processor_template.py**
   - [ ] Review templates: pipeline_template.py, processor_template.py
   - [ ] Study examples: icon_extractor_demo.py, existing audio_icon_matcher patterns, **podcast streaming examples**

2. **Core Implementation**
   - [ ] Enhance existing AudioIconPipeline class to support podcast episode processing
   - [ ] Implement IconMatcher with database query optimization
   - [ ] Add ResultRanker with confidence scoring algorithms
   - [ ] **NEW**: Implement PodcastAnalyzer with RSS feed processing and streaming transcription
   - [ ] **NEW**: Create RSSFeedConnector for podcast metadata extraction
   - [ ] **NEW**: Add WhisperStreamingService for efficient audio transcription
   - [ ] Integrate comprehensive error handling and logging following ADR-007

3. **Integration Phase**
   - [ ] Integrate with existing AudioProcessor and SubjectIdentifier components
   - [ ] **NEW**: Integrate podcast components with existing media analyzer framework
   - [ ] Connect to icon database using established database patterns
   - [ ] Add CLI commands supporting both file paths and podcast URLs using cli_command_template.py
   - [ ] Add configuration management for pipeline parameters and podcast-specific settings

4. **Testing Phase**
   - [ ] Write unit tests for each component with 95% coverage target
   - [ ] Add integration tests with real audio files and icon database
   - [ ] **NEW**: Add podcast integration tests with real RSS feeds and streaming episodes
   - [ ] Add performance tests to validate response time requirements (local and streaming)
   - [ ] Add end-to-end tests with various audio content types and podcast sources

5. **Documentation Phase**
   - [ ] Create comprehensive API documentation covering both local and podcast processing
   - [ ] Add usage examples and CLI help documentation for mixed content sources
   - [ ] Update architectural documentation with pipeline integration and podcast components
   - [ ] Create troubleshooting guide for common issues including podcast-specific problems

### Code Quality Requirements
- **Type Safety**: 100% mypy compliance with comprehensive type hints
- **Code Style**: 100% black and ruff compliance following project standards
- **Test Coverage**: 95% minimum coverage across all pipeline components
- **Documentation**: All public APIs documented with examples and error cases
- **Performance**: Meet specified 30-second processing time and memory requirements

## Acceptance Criteria

### Functional Acceptance Criteria
- [ ] **AC-F1**: Pipeline successfully processes both WAV, MP3, M4A audio files and podcast episodes from URLs
- [ ] **AC-F2**: Returns relevant icon matches with confidence scores for children's story content and podcast episodes  
- [ ] **AC-F3**: Handles batch processing of mixed content (local files and podcast episodes)
- [ ] **AC-F4**: Provides detailed error messages for invalid inputs and processing failures (both local and streaming)
- [ ] **AC-F5**: Supports configuration of confidence thresholds and result limits for all content types
- [ ] **AC-F6**: **NEW**: Successfully parses RSS feeds and extracts episode metadata
- [ ] **AC-F7**: **NEW**: Processes streaming audio without requiring full episode downloads
- [ ] **AC-F8**: **NEW**: Integrates podcast episode metadata with icon matching results

### Technical Acceptance Criteria
- [ ] **AC-T1**: All unit tests pass with 95% coverage
- [ ] **AC-T2**: Integration tests pass with real audio files and icon database
- [ ] **AC-T3**: Performance requirements met (30s processing, 512MB memory)
- [ ] **AC-T4**: Security requirements satisfied (input validation, data protection)
- [ ] **AC-T5**: Code quality gates pass (mypy, ruff, black)
- [ ] **AC-T6**: Documentation complete with examples and troubleshooting

### User Experience Acceptance Criteria
- [ ] **AC-UX1**: CLI provides clear progress indicators and helpful error messages
- [ ] **AC-UX2**: Results include meaningful confidence scores and matching explanations
- [ ] **AC-UX3**: Processing completes within acceptable time limits for typical use cases

## Test Scenarios

### Happy Path Scenarios
1. **Test Case 1**: Children's Story Processing
   - **Input**: "Once upon a time" fairy tale audio file (WAV, 2 minutes)
   - **Expected Output**: 3-5 relevant fairy tale icons with confidence > 0.7
   - **Validation**: Verify icon relevance and confidence scoring accuracy

2. **Test Case 2**: Educational Content Processing
   - **Input**: Science lesson audio about weather (MP3, 3 minutes)
   - **Expected Output**: Weather-related icons (sun, rain, clouds) with high confidence
   - **Validation**: Confirm subject identification accuracy and icon relevance

3. **Test Case 3**: Batch Processing
   - **Input**: 5 different audio files with various subjects
   - **Expected Output**: Appropriate icons for each file with processing metadata
   - **Validation**: All files processed successfully with consistent results

### Error Path Scenarios
1. **Error Test 1**: Invalid Audio File
   - **Input**: Corrupted or non-audio file
   - **Expected Behavior**: Clear error message with file validation details
   - **Validation**: No system crash, helpful error guidance provided

2. **Error Test 2**: Database Connection Failure
   - **Input**: Valid audio file but icon database unavailable
   - **Expected Behavior**: Graceful error handling with retry suggestions
   - **Validation**: Proper error logging and user notification

3. **Error Test 3**: Empty Audio Content
   - **Input**: Silent audio file with no transcribable content
   - **Expected Behavior**: Appropriate handling with "no content" response
   - **Validation**: System handles edge case without errors

### Edge Case Scenarios
1. **Edge Case 1**: Multiple Subject Content
   - **Scenario**: Audio with multiple distinct subjects (animals, vehicles, food)
   - **Expected Behavior**: Return icons for all identified subjects with appropriate scoring
   - **Validation**: Verify comprehensive subject detection and balanced results

2. **Edge Case 2**: Very Long Audio File
   - **Scenario**: 10-minute audio file with extensive content
   - **Expected Behavior**: Successful processing within time limits
   - **Validation**: Performance requirements met, memory usage controlled

3. **Edge Case 3**: Ambiguous Content
   - **Scenario**: Abstract or metaphorical content without clear subjects
   - **Expected Behavior**: Return general category icons with lower confidence scores
   - **Validation**: System handles ambiguity gracefully without errors

## Dependencies

### Internal Dependencies
- **Core**: Audio Icon Matcher framework, configuration management, logging system
- **Audio Processing**: AudioProcessor with Whisper integration, transcription capabilities
- **Subject Identification**: SubjectIdentifier (from media_analyzer) with enhanced children's content recognition
- **Database**: Icon database with search optimization, connection pooling
- **CLI Framework**: Command interface, progress reporting, error handling

### External Dependencies
- **Libraries**: whisper, sqlite3, click, pydub, requests
- **Services**: Local icon database, file system access
- **Configuration**: Database connection settings, processing parameters, timeout values
- **Podcast Dependencies**: RSS feed parsers (feedparser), streaming audio libraries (httpx)

### Cross-Component Dependencies
- **media_analyzer Integration**: 
  - SubjectIdentifier for content analysis
  - PodcastAnalyzer for episode processing (from ADR-010)
  - RSSFeedConnector for feed parsing
  - WhisperStreamingService for transcription
- **icon_extractor Integration**:
  - Database connectivity and icon search capabilities
  - Icon metadata and categorization systems

### Development Dependencies
- **Testing Tools**: pytest with audio file fixtures, database testing utilities
- **Development Tools**: mypy, black, ruff, coverage reporting tools

## Risks and Mitigation

### Technical Risks
- **Risk 1**: Audio transcription accuracy issues
  - **Impact**: Poor subject identification leading to irrelevant icon matches
  - **Probability**: Medium
  - **Mitigation**: Implement confidence thresholds, fallback subject detection methods

- **Risk 2**: Icon database query performance degradation
  - **Impact**: Slow response times affecting user experience
  - **Probability**: Medium  
  - **Mitigation**: Database indexing optimization, query caching, connection pooling

- **Risk 3**: Memory usage exceeding limits with large audio files
  - **Impact**: System instability or processing failures
  - **Probability**: Low
  - **Mitigation**: Streaming processing, file size validation, memory monitoring

### Implementation Risks
- **Complexity Risk**: Integration of multiple complex components
  - **Mitigation**: Incremental development with comprehensive testing at each stage

- **Integration Risk**: Compatibility issues between existing components
  - **Mitigation**: Thorough integration testing, API contract validation

## Timeline and Milestones

### Development Phases
1. **Phase 1 - Design & Setup** (3 days)
   - Complete technical design and architecture review
   - Set up development environment with all dependencies
   - Create initial pipeline structure and interfaces

2. **Phase 2 - Core Implementation** (5 days)
   - Implement enhanced AudioIconPipeline with podcast support
   - Create IconMatcher with database integration
   - Add ResultRanker with confidence scoring
   - Implement comprehensive error handling

3. **Phase 3 - Integration & CLI** (3 days)
   - Integrate with existing media_analyzer components
   - Add CLI interface with progress reporting
   - Implement batch processing capabilities
   - Add configuration management

4. **Phase 4 - Testing & Documentation** (4 days)
   - Complete unit and integration test suites
   - Performance and security testing
   - API documentation and user guides
   - System optimization and bug fixes

### Key Milestones
- **Milestone 1**: Core pipeline architecture complete - Day 3
- **Milestone 2**: Enhanced AudioIconPipeline with podcast support working - Day 8  
- **Milestone 3**: CLI and batch processing complete - Day 11
- **Milestone 4**: Full testing and documentation complete - Day 15

## Success Metrics

### Development Metrics
- **Implementation Time**: Complete within 15 days
- **Code Quality Score**: 100% mypy, black, ruff compliance
- **Test Coverage**: 95% minimum across all components
- **Bug Count**: Less than 5 critical bugs in final implementation

### User Metrics
- **Processing Accuracy**: 85% relevant icon matches for test content
- **Processing Speed**: Average processing time under 20 seconds
- **User Satisfaction**: 4.0/5.0 rating in usability testing
- **Error Rate**: Less than 5% processing failures on valid inputs

### Business Metrics
- **Value Delivered**: Automated icon matching reduces manual curation time by 70%
- **Cost Efficiency**: Development cost justified by time savings for content creators
- **Adoption Rate**: Feature used for 80% of new audio content processing

## Post-Implementation

### Monitoring Requirements
- **Performance Monitoring**: Track processing times, memory usage, and success rates
- **Usage Analytics**: Monitor feature adoption, most common audio types, and user patterns
- **Error Monitoring**: Track error rates, failure patterns, and user-reported issues

### Maintenance Requirements
- **Regular Updates**: Icon database updates, subject detection improvements
- **Performance Optimization**: Query optimization, memory usage improvements
- **Security Updates**: Input validation enhancements, dependency updates

### Future Enhancements
- **Planned Improvements**: Machine learning-based confidence scoring, visual similarity matching
- **Extensibility**: Support for additional audio formats, custom icon databases
- **Integration Opportunities**: Integration with content management systems, web interfaces

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-08-27 | AI Development Agent | Initial version |
| 1.1 | 2025-08-30 | AI Development Agent | Extended to support podcast episode processing |
| 1.2 | 2025-08-30 | AI Development Agent | Corrected CLI interface to match actual audio_icon_matcher implementation |

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | TBD | TBD | [Pending] |
| Tech Lead | TBD | TBD | [Pending] |
| AI Agent | GitHub Copilot | 2025-08-27 | [Approved] |

---

**Template Version**: 1.0  
**Last Updated**: 2025-08-30 (CLI interface corrected)  
**Next Review**: 2025-09-30
