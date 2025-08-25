"""Test fixtures for subject identification."""
import pytest
from typing import Dict, Any

@pytest.fixture
def tech_discussion_text():
    """Sample text about technology."""
    return """
    Artificial intelligence and machine learning are transforming industries. Companies like Google 
    and Microsoft are investing heavily in AI research. The development of neural networks has led 
    to breakthroughs in natural language processing and computer vision.
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
def mock_models():
    """Mock subject identification models."""
    class MockModel:
        def __init__(self, name: str):
            self.name = name
            
        def process(self, text: str) -> Dict[str, Any]:
            if self.name == "lda":
                return {
                    "results": [
                        {"name": "technology", "score": 0.8},
                        {"name": "science", "score": 0.6}
                    ],
                    "metadata": {"model": "lda"}
                }
            elif self.name == "ner":
                return {
                    "results": [
                        {"name": "Google", "score": 1.0},
                        {"name": "Microsoft", "score": 1.0}
                    ],
                    "metadata": {"model": "spacy"}
                }
            else:  # keyword
                return {
                    "results": [
                        {"name": "artificial intelligence", "score": 0.9},
                        {"name": "machine learning", "score": 0.85}
                    ],
                    "metadata": {"model": "rake"}
                }
    
    return {
        "lda": MockModel("lda"),
        "ner": MockModel("ner"),
        "keyword": MockModel("keyword")
    }
