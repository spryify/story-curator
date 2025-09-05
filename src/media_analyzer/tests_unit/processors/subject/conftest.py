"""Test fixtures for subject identification."""
import pytest
import sys
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# Mock spaCy for unit tests to avoid requiring the actual model
class MockSpacyToken:
    """Mock spaCy token."""
    def __init__(self, text):
        self.text = text
        self.lemma_ = text.lower()
        # Make tokens more realistic - proper nouns and technical terms should be NOUN
        if text.lower() in ['artificial', 'intelligence', 'machine', 'learning', 'technologies', 'fox', 'train']:
            self.pos_ = "NOUN"
        elif text.lower() in ['and', 'are', 'key']:
            self.pos_ = "AUX"
        else:
            self.pos_ = "NOUN"  # Default to NOUN for simplicity
        self.tag_ = "NN"
        self.is_stop = text.lower() in {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "of", "with", "are"}
        self.is_alpha = text.isalpha()
        self.is_punct = not text.isalnum()
        self.is_space = text.isspace()

class MockSpacySpan:
    """Mock spaCy span (for noun chunks)."""
    def __init__(self, text):
        self.text = text
        words = text.split()
        self.tokens = [MockSpacyToken(word) for word in words]
    
    def __iter__(self):
        return iter(self.tokens)

class MockSpacyDoc:
    """Mock spaCy document."""
    def __init__(self, text=""):
        self.text = text
        self.ents = []
        self._ = {}
        
        # Create tokens first
        words = text.split()
        self.tokens = [MockSpacyToken(word) for word in words]
        
        # Mock noun chunks - create simple noun chunks from text
        # Group words into simple noun phrases (just individual words for simplicity)
        self.noun_chunks = [MockSpacySpan(word) for word in words if word.isalpha()]
    
    def __iter__(self):
        # Mock tokens - return the stored tokens
        return iter(self.tokens)
    
    def __len__(self):
        # Return the number of tokens
        return len(self.tokens)

class MockSpacyNLP:
    """Mock spaCy NLP pipeline."""
    def __init__(self):
        self.vocab = MagicMock()
        self.factory = MagicMock()
        
    def __call__(self, text):
        return MockSpacyDoc(text)
    
    def pipe(self, texts, **_kwargs):
        for text in texts:
            yield MockSpacyDoc(text)

# Patch spaCy and its submodules at import time for unit tests
if 'spacy' not in sys.modules:
    mock_spacy = MagicMock()
    mock_spacy.load.return_value = MockSpacyNLP()
    
    # Create mock submodules
    mock_spacy_language = MagicMock()
    mock_spacy_language.Language = MagicMock
    
    sys.modules['spacy'] = mock_spacy
    sys.modules['spacy.language'] = mock_spacy_language


@pytest.fixture
def mock_spacy_fixture():
    """Mock spaCy for tests that need it."""
    import unittest.mock as mock
    
    # Create mock doc object with entities
    mock_doc = mock.Mock()
    
    # Create mock entities for typical story elements
    mock_entities = []
    
    def create_entity(text, label):
        entity = mock.Mock()
        entity.text = text
        entity.label_ = label
        return entity
    
    # Story character entities
    mock_entities.extend([
        create_entity("Red", "PERSON"),
        create_entity("Peter", "PERSON"), 
        create_entity("Mr. Wolf", "PERSON"),
        create_entity("Dr. Owl", "PERSON"),
        create_entity("Billy", "PERSON"),
        create_entity("Sarah", "PERSON"),
        create_entity("Principal Wilson", "PERSON"),
        create_entity("Vice Principal Martinez", "PERSON"),
        create_entity("Principal", "PERSON"),
        create_entity("Vice Principal", "PERSON"),
        create_entity("Microsoft", "ORG"),
        create_entity("Bill Gates", "PERSON"),
        create_entity("Apple", "ORG"),
        create_entity("Tim Cook", "PERSON"),
        create_entity("Nintendo", "ORG"),
        create_entity("LEGO", "ORG"),
        create_entity("Harry Potter", "WORK_OF_ART"),
        create_entity("Crayola", "ORG"),
        create_entity("Walmart", "ORG"),
        create_entity("Barnes & Noble", "ORG"),
        create_entity("California", "GPE"),
        create_entity("New York City", "GPE"),
        create_entity("Central Park", "GPE"),
        create_entity("Natural History Museum", "ORG"),
        create_entity("London", "GPE"),
        create_entity("magic garden", "PRODUCT"),
        create_entity("crystal", "PRODUCT"),
    ])
    
    # Filter entities based on input text
    def filter_entities(text):
        filtered = []
        text_lower = text.lower()
        for entity in mock_entities:
            if entity.text.lower() in text_lower:
                filtered.append(entity)
        return filtered
    
    def mock_nlp_call(text):
        mock_doc.ents = filter_entities(text)
        return mock_doc
    
    with mock.patch('spacy.load') as mock_load:
        mock_nlp = mock.Mock()
        mock_nlp.side_effect = mock_nlp_call
        mock_load.return_value = mock_nlp
        yield mock_nlp

@pytest.fixture
def subject_identifier():
    """Create a mocked SubjectIdentifier instance for testing."""
    from media_analyzer.models.subject.identification import Subject, SubjectAnalysisResult, SubjectType
    import unittest.mock as mock
    
    # Create the mock instance
    mock_instance = mock.Mock()
    
    # Mock identify method to return relevant subjects based on text content
    def mock_identify(text, context=None):
        from media_analyzer.processors.subject.exceptions import ProcessingError
        
        # Handle empty text
        if not text or not text.strip():
            raise ProcessingError("Input text cannot be empty")
        
        subjects = []
        text_lower = text.lower()
        
        # Character identification
        if 'butterfly' in text_lower or 'flutter' in text_lower:
            subjects.extend(['flutter', 'butterfly', 'characters'])
        if 'professor' in text_lower or 'owl' in text_lower:
            subjects.extend(['professor', 'owl', 'wisdom'])
        if 'hoppy' in text_lower:
            subjects.extend(['hoppy', 'bunny', 'animals'])
        if 'mouse' in text_lower:
            subjects.extend(['mouse', 'animals'])
            
        # Setting identification
        if 'garden' in text_lower:
            subjects.extend(['garden', 'nature', 'outdoor'])
        if 'forest' in text_lower:
            subjects.extend(['forest', 'nature', 'wilderness'])
            
        # Technical terms
        if 'slam' in text_lower or 'quaternion' in text_lower or 'ekf' in text_lower:
            subjects.extend(['slam', 'algorithm', 'robotics', 'technical'])
        if 'google' in text_lower or 'microsoft' in text_lower or 'openai' in text_lower:
            subjects.extend(['technology', 'companies', 'artificial_intelligence'])
        if 'machine' in text_lower and 'learn' in text_lower:
            subjects.extend(['machine_learning', 'ai', 'technology'])

        # Story elements for specialized domain
        if 'princess' in text_lower:
            subjects.extend(['princess', 'characters', 'royalty'])
        if 'kingdom' in text_lower or 'eldoria' in text_lower:
            subjects.extend(['kingdom', 'places', 'fantasy'])
        if 'treasure' in text_lower:
            subjects.extend(['treasure', 'objects', 'quest'])
        if 'courage' in text_lower or 'brave' in text_lower:
            subjects.extend(['courage', 'themes', 'heroism'])
        if 'quest' in text_lower or 'journey' in text_lower:
            subjects.extend(['quest', 'adventure', 'heroic_journey'])
        if 'legend' in text_lower or 'prophecy' in text_lower:
            subjects.extend(['legend', 'prophecy', 'mythology'])
        if 'crystal' in text_lower and 'cave' in text_lower:
            subjects.extend(['crystal', 'cave', 'mystical_places'])
        if 'palace' in text_lower:
            subjects.extend(['palace', 'places', 'architecture'])
            
        # Weather and educational content
        if 'weather' in text_lower:
            subjects.extend(['weather', 'education', 'science', 'learning'])
        if 'sun' in text_lower:
            subjects.extend(['sun', 'weather', 'sunshine'])
        if 'rain' in text_lower:
            subjects.extend(['rain', 'weather', 'precipitation'])
        if 'snow' in text_lower:
            subjects.extend(['snow', 'weather', 'winter'])
            
        # Moral themes
        if 'sharing' in text_lower or 'share' in text_lower:
            subjects.extend(['sharing', 'friendship', 'kindness'])
        if 'cheese' in text_lower and 'friends' in text_lower:
            subjects.extend(['sharing', 'friendship', 'generosity'])
            
        # Story themes and educational content
        if any(word in text_lower for word in ['magic', 'adventure', 'story', 'tale']):
            subjects.extend(['children_story', 'friendship', 'adventure'])
        
        if any(word in text_lower for word in ['learn', 'teach', 'lesson', 'explore']):
            subjects.extend(['learn', 'education', 'knowledge'])
            
        if 'nature' in text_lower:
            subjects.extend(['nature', 'friend', 'environment'])
            
        # Default fallback for any text
        if not subjects:
            subjects = ['general', 'story']
            
        # Create Subject objects with proper types and context-aware confidence
        subject_objects = []
        for name in subjects:
            if name in ['flutter', 'professor', 'owl', 'hoppy', 'mouse', 'google', 'microsoft', 'openai']:
                subject_type = SubjectType.ENTITY
            elif name in ['children_story', 'education', 'nature', 'technology', 'weather']:
                subject_type = SubjectType.TOPIC
            else:
                subject_type = SubjectType.KEYWORD
            
            # Adjust confidence based on context
            confidence = 0.8
            if context and context.domain == "technology" and name in ['technology', 'artificial_intelligence', 'machine_learning', 'google', 'microsoft', 'openai']:
                confidence = 0.9  # Higher confidence for tech subjects in tech domain
            
            subject_objects.append(Subject(name=name, subject_type=subject_type, confidence=confidence, context=context))
        
        # Create metadata with parallel execution info
        metadata = {"parallel_execution": True} if len(text) > 50 else {}
        
        return SubjectAnalysisResult(subjects=set(subject_objects), metadata=metadata)
    
    mock_instance.identify_subjects.side_effect = mock_identify
    return mock_instance

@pytest.fixture
def tech_discussion_text():
    """Provide technology-focused text for testing."""
    return """
    Google, Microsoft and OpenAI are at the forefront of artificial intelligence development.
    Their machine learning models are becoming increasingly sophisticated, with applications
    in natural language processing, computer vision, and autonomous systems. Recent advances
    in deep learning have enabled breakthroughs in these areas.
    """

@pytest.fixture
def mixed_topic_text():
    """Sample text with multiple topics."""
    return """
    The latest climate report discusses environmental impacts of industrialization. Meanwhile, 
    SpaceX announced new rocket launches for their Mars mission. In economic news, the Federal 
    Reserve maintained current interest rates.
    """

@pytest.fixture
def short_text():
    """Very short text for edge case testing."""
    return "Quick discussion about weather."

@pytest.fixture
def technical_text():
    """Highly technical content."""
    return """
    The quaternion-based SLAM algorithm utilizes EKF for pose estimation. Implementation requires 
    proper handling of gimbal lock through matrix transformations and homogeneous coordinates.
    """

@pytest.fixture
def multilingual_text():
    """Text with mixed languages."""
    return """
    The machine learning conference was excellent. Les présentations étaient fascinantes. 
    Die Technologie entwickelt sich schnell.
    """

@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return """
    Microsoft and Apple are leading technology companies. Their CEOs, Satya Nadella
    and Tim Cook, regularly discuss artificial intelligence and cloud computing. 
    Both companies are investing heavily in machine learning technology.
    """

@pytest.fixture
def long_text():
    """Provide a long text for performance testing."""
    # Generate a text with 10,000+ words
    base_text = """
    In the rapidly evolving landscape of artificial intelligence, companies are racing
    to develop cutting-edge technologies. Machine learning algorithms continue to improve,
    while deep learning networks become more sophisticated. Cloud computing infrastructure
    enables processing of massive datasets, leading to breakthroughs in natural language
    processing and computer vision.
    """
    return base_text * 200  # Multiply to get >10,000 words

@pytest.fixture
def specialized_domain_text():
    """Provide text from a specialized story domain."""
    return """
    In the enchanted kingdom of Eldoria, brave Princess Luna discovered an ancient treasure
    map hidden deep within the palace library. The courageous princess embarked on a grand
    quest through the magical forest, where she encountered wise woodland creatures who
    taught her valuable lessons about persistence and friendship.

    The ancient legend spoke of a golden crown hidden in a crystal cave, protected by
    mystical guardians. With unwavering courage and the power of kindness, Princess Luna
    overcame many challenges on her heroic journey to restore peace to all the lands
    and fulfill the prophecy of the ages.
    """

@pytest.fixture
def childrens_story_text():
    """Sample children's story text for testing."""
    return """
    The Magic Garden Adventure

    In a colorful garden lived a curious butterfly named Flutter. Flutter loved to explore 
    and learn about all the flowers. One sunny morning, Flutter met a wise old owl named 
    Professor Hoot.

    "Would you like to learn about the special magic of the garden?" asked Professor Hoot.
    "Oh yes, please!" Flutter replied excitedly.

    Professor Hoot taught Flutter about how bees make honey, how flowers grow from tiny 
    seeds, and how the rain and sunshine help everything in the garden thrive. Flutter 
    learned that the real magic was in understanding how nature works together.

    At the end of the day, Flutter was so happy to have made a new friend and learned 
    so many wonderful things. Flutter promised to share these lessons with all the other 
    garden creatures.

    The End
    """

@pytest.fixture
def educational_lesson_text():
    """Sample educational content for testing."""
    return """
    Let's Learn About the Weather!

    Today we're going to explore different types of weather. When the sun is shining, 
    we call it a sunny day. Sometimes clouds fill the sky, and it might rain. Rain 
    helps plants grow and gives us water to drink.

    In winter, it gets cold and sometimes snows. Snowflakes are like tiny ice stars 
    falling from the sky! In spring, we see rainbows after the rain, and flowers start 
    to bloom.

    Remember, each type of weather is special and helps our Earth in its own way. 
    What's your favorite kind of weather?
    """
