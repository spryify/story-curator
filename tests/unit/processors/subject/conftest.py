"""Test fixtures for subject identification."""
import pytest
from typing import Dict, Any
from media_analyzer.processors.subject.subject_identifier import SubjectIdentifier
from media_analyzer.models.subject.identification import Context

@pytest.fixture
def subject_identifier():
    """Create a SubjectIdentifier instance for testing."""
    return SubjectIdentifier()

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
    """Provide text from a specialized domain."""
    return """
    The CRISPR-Cas9 system enables precise genome editing through targeted DNA
    cleavage. This revolutionary technique has applications in genetic engineering,
    biotechnology, and medical research. The guide RNA sequence determines the
    specificity of the nuclease activity.
    """
