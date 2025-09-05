# Feature Requirement: Audio Subject Identification

**Feature ID**: FR-002-audio-subject-identification  
**Title**: Audio Subject Identification  
**Priority**: High  
**Status**: In Progress - Enhancement Phase  
**Assigned To**: GitHub Copilot  
**Created**: 2025-08-24  
**Updated**: 2025-09-02

## Executive Summary

**Brief Description**: Implement functionality to analyze transcribed audio text and identify the main subject(s) or topic(s) being discussed.

**Business Value**: Enables automatic categorization and indexing of audio content, making it easier for users to organize and search through audio files based on their subject matter.

**Current Status**: The basic subject identification is implemented but testing revealed quality issues with keyword extraction and icon matching. Generic words like "her", "very", "end" were causing irrelevant matches (e.g., "her" → Frozen princess icons). This enhancement phase focuses on improving semantic matching quality by leveraging established NLP libraries.

**Success Criteria**: 
- Successfully identify primary subject(s) in 90% of test cases
- Subject identification completes in under 800ms for typical audio transcripts
- False positive rate below 10%
- **NEW**: Problematic generic word filtering (pronouns like "her", "him", common words like "very", "end") 
- **NEW**: Semantic similarity matching over literal string matching
- **NEW**: Leverage established NLP libraries (NLTK, spaCy) instead of custom implementations

## User Stories

### Primary User Story
```
As a content analyst
I want to automatically identify the main subjects discussed in audio files
So that I can quickly categorize and organize large collections of audio content
```

### Additional User Stories
```
As a researcher
I want to search for audio files by their subject matter
So that I can find relevant audio content efficiently

As a data scientist
I want to extract structured subject metadata from audio transcripts
So that I can analyze trends and patterns in audio content
```

## Enhancement Phase - NLP Library Integration (September 2025)

### Problem Statement
Integration testing revealed significant quality issues with the current custom implementation:

1. **Generic Word Problem**: Keywords like "her", "very", "end", "ever" were getting high confidence scores and causing irrelevant icon matches
2. **Poor Semantic Understanding**: Literal string matching produced semantically meaningless results  
3. **Reinventing the Wheel**: Custom stop word lists, semantic groups, and compound word detection duplicate existing NLP libraries
4. **Maintenance Burden**: Custom implementations require ongoing maintenance and tuning

### Test Case Evidence
**Problematic Episode**: "The Pot of Gold" from Circle Round podcast
- Original: "her" (0.90 confidence) → Frozen princess icons ❌
- Original: "end" (0.90 confidence) → Calendar/Apple icons ❌  
- Original: "very" (1.00 confidence) → Irrelevant matches ❌

**Expected Behavior**: 
- Filter out generic pronouns and common words
- Focus on story-relevant terms: "leprechauns", "gold", "ireland", "tale"
- Semantic matching for related concepts

### Enhancement Goals
1. **Replace Custom NLP with Established Libraries**
   - Use NLTK for comprehensive stop words and WordNet semantic relationships
   - Leverage spaCy for advanced tokenization, POS tagging, and word vectors
   - Integrate Gensim for semantic similarity via pre-trained embeddings

2. **Improve Keyword Quality**
   - Comprehensive stop word filtering using NLTK corpora
   - Semantic relevance scoring using word embeddings
   - Context-aware compound phrase detection

3. **Enable Semantic Matching**
   - Word similarity using spaCy word vectors
   - Synonym mapping via WordNet
   - Semantic word groups for categories (animals, colors, nature, etc.)

## Functional Requirements

### Core Functionality
1. **Subject Extraction**: Analyze transcribed text to identify key subjects and topics
2. **Confidence Scoring**: Provide confidence scores for identified subjects
3. **Multi-subject Support**: Handle cases where multiple subjects are discussed
4. **Subject Categorization**: Group related subjects into broader categories
5. **Context Awareness**: Consider context when identifying subjects

### Input/Output Specifications
- **Inputs**: 
  - Transcribed text from audio file
  - Optional context parameters (domain, expected subjects, etc.)
- **Outputs**: 
  - List of identified subjects with confidence scores
  - Subject categories and relationships
  - Processing metadata (time taken, model used, etc.)
- **Data Flow**: 
  1. Receive transcribed text
  2. Preprocess text for analysis
  3. Extract candidate subjects
  4. Score and rank subjects
  5. Categorize and group subjects
  6. Return structured results

### Behavior Specifications
- **Normal Operation**: 
  - Process text and return subjects within 800ms
  - Handle texts up to 100,000 words
  - Support multiple languages (initially English)
- **Edge Cases**:
  - Very short texts (< 10 words)
  - Technical/specialized content
  - Mixed language content
- **Error Conditions**:
  - Invalid input text format
  - Processing timeout
  - Insufficient context for identification

## Non-Functional Requirements

### Performance Requirements
- **Response Time**: < 800ms for texts up to 10,000 words
- **Throughput**: Process 100 requests/minute
- **Memory Usage**: < 500MB per process
- **CPU Usage**: < 50% CPU utilization per process

### Security Requirements
- **Input Validation**: Sanitize all input text
- **Data Protection**: No storage of processed text
- **Access Control**: API access controlled via authentication
- **Audit Requirements**: Log all processing attempts and results

### Reliability Requirements
- **Availability**: 99.9% uptime
- **Error Handling**: Graceful degradation with partial results
- **Recovery**: Automatic retry for failed processing
- **Data Integrity**: Validate all input/output data

### Usability Requirements
- **User Interface**: Clean API interface
- **Accessibility**: Support for international character sets
- **Documentation**: Complete API documentation with examples
- **Error Messages**: Clear, actionable error messages

## Technical Specifications

### Architecture Integration
- **Related ADRs**: 
  - ADR-003 (Error Handling)
  - ADR-005 (Type Safety)
  - ADR-007 (Logging)

### Component Design
- **New Components**:
  ```python
  class SubjectIdentifier:
      def identify_subjects(self, text: str) -> List[Subject]
      def get_subject_categories(self) -> List[Category]
      def analyze_context(self, text: str) -> Context
  
  class Subject:
      name: str
      confidence: float
      category: Optional[Category]
      context: Context
  
  class Category:
      name: str
      description: str
      parent: Optional[Category]
  
  class Context:
      domain: str
      language: str
      confidence: float
  ```
- **Modified Components**:
  - AudioProcessor: Add subject identification integration
  - TextProcessor: Enhanced text preprocessing
- **Integration Points**:
  - Hooks into existing text processing pipeline
  - Integration with audio analysis workflow
  - Export interface for search/indexing systems

### Data Model
- **Data Structures**:
  - Subject entity with metadata
  - Category hierarchy
  - Context information
- **Database Changes**: None required
- **Configuration**:
  - Subject identification model settings
  - Category definitions
  - Performance tuning parameters

### API Design
```python
@dataclass
class SubjectAnalysisResult:
    subjects: List[Subject]
    categories: List[Category]
    metadata: Dict[str, Any]

class SubjectAnalyzer:
    def analyze_text(
        self, 
        text: str,
        context: Optional[Context] = None
    ) -> SubjectAnalysisResult:
        """
        Analyze text to identify subjects and categories.
        
        Args:
            text: The transcribed text to analyze
            context: Optional context information
            
        Returns:
            SubjectAnalysisResult containing identified subjects,
            categories, and analysis metadata
            
        Raises:
            InvalidInputError: If text is invalid
            ProcessingError: If analysis fails
            TimeoutError: If processing exceeds time limit
        """
        pass
```

## Enhanced Technical Specifications (NLP Library Integration)

### Required NLP Libraries
Based on existing requirements.txt, these libraries are already available:
- **NLTK (>=3.8.1)**: Stop words, WordNet synonyms, tokenization
- **spaCy (>=3.7.2)**: Advanced NLP, word vectors, POS tagging
- **Gensim (>=4.3.2)**: Word embeddings, semantic similarity
- **scikit-learn (>=1.3.1)**: TF-IDF, feature extraction

### Enhanced Component Design

#### EnhancedKeywordExtractor
```python
class EnhancedKeywordExtractor:
    """Enhanced keyword extractor using established NLP libraries."""
    
    def __init__(self):
        # NLTK resources
        self.stop_words = set(nltk.corpus.stopwords.words('english'))
        self.wordnet = nltk.corpus.wordnet
        
        # spaCy model for semantic analysis
        self.nlp = spacy.load("en_core_web_sm")
        
        # Custom domain-specific additions
        self._load_domain_stop_words()
    
    def process(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract keywords using NLP libraries."""
        # Use spaCy for tokenization and POS tagging
        doc = self.nlp(text)
        
        # Filter using NLTK stop words + custom domain words
        # Score using semantic relevance + TF-IDF
        # Detect compound phrases using dependency parsing
        pass
```

#### EnhancedIconMatcher  
```python
class EnhancedIconMatcher:
    """Enhanced icon matcher using semantic similarity."""
    
    def __init__(self):
        # Load spaCy model with word vectors
        self.nlp = spacy.load("en_core_web_md")  # Medium model with vectors
        
        # NLTK WordNet for synonyms
        self.wordnet = nltk.corpus.wordnet
        
        # Semantic word groups (can be loaded from JSON/YAML)
        self._load_semantic_groups()
    
    def find_matching_icons(
        self, 
        subjects: Dict[str, Any], 
        limit: int = 10,
        min_confidence: float = 0.3
    ) -> List[IconMatch]:
        """Find icons using semantic similarity."""
        # Use spaCy word vectors for similarity
        # Apply WordNet synonym expansion
        # Filter using semantic relevance thresholds
        pass
```

### Library Integration Strategy

#### Phase 1: NLTK Integration
1. **Stop Words**: Replace custom stop word lists with NLTK's comprehensive corpora
2. **WordNet**: Use for synonym detection and semantic relationships
3. **Tokenization**: Leverage NLTK's robust tokenizers

#### Phase 2: spaCy Integration  
1. **Word Vectors**: Use pre-trained embeddings for semantic similarity
2. **POS Tagging**: Improve keyword filtering with part-of-speech information
3. **Dependency Parsing**: Better compound phrase detection

#### Phase 3: Semantic Enhancement
1. **Gensim Models**: Word2Vec/FastText for advanced similarity
2. **TF-IDF**: scikit-learn for term importance scoring
3. **Custom Domains**: Extend with story/podcast-specific semantic groups

### Implementation Plan

#### Step 1: Library Setup and Validation
- Verify all required NLP libraries are properly installed
- Download necessary language models (spaCy en_core_web_md)
- Download NLTK data (stopwords, wordnet, punkt)

#### Step 2: Enhanced Keyword Extractor
- Replace custom stop words with NLTK stopwords corpus
- Add semantic relevance scoring using word embeddings
- Implement compound phrase detection using dependency parsing

#### Step 3: Enhanced Icon Matcher
- Implement semantic similarity using spaCy word vectors
- Add WordNet synonym expansion for better matching  
- Create semantic word groups for categorized matching

#### Step 4: Integration and Testing
- Update AudioIconPipeline to use enhanced components
- Run comparative tests against original implementation
- Validate improvements using problematic test cases

### Success Metrics for Enhancement

#### Quality Improvements
- **Problematic Word Filtering**: 100% filtering of identified problematic words ("her", "very", "end", etc.)
- **Semantic Relevance**: >80% of matched icons should be semantically relevant to story content
- **False Positive Reduction**: <5% false positive rate for irrelevant matches

#### Performance Criteria
- **Processing Time**: No degradation in processing time (<800ms)
- **Memory Usage**: <100MB additional memory for NLP models
- **Accuracy**: >85% accuracy on story content keyword extraction

#### Maintainability Benefits
- **Code Reduction**: 50% reduction in custom NLP code
- **Library Reliability**: Use battle-tested NLP libraries instead of custom implementations  
- **Update Path**: Clear path for model updates and improvements

### Risk Mitigation

#### Potential Issues
1. **Model Size**: spaCy models can be large (50-500MB)
2. **Cold Start**: Initial model loading time
3. **Language Support**: Currently English-only, may need expansion

#### Mitigation Strategies
1. **Lazy Loading**: Load models only when needed
2. **Model Caching**: Cache loaded models across requests
3. **Fallback Strategy**: Graceful degradation to simpler methods if advanced models fail

---

**Implementation Status**: Ready for implementation
**Next Steps**: Begin Phase 1 - Library setup and validation
**Review Date**: 2025-09-15
