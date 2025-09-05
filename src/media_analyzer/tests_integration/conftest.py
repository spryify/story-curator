"""Audio analysis integration test fixtures."""

import asyncio
import pytest
import pytest_asyncio
import sys
import warnings
from pathlib import Path
from ..tests_unit.utils.audio import create_wav_file

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def create_story_audio_file(tmp_path: Path, story_text: str, filename: str = "story.wav") -> Path:
    """Create an audio file using the existing utility with story text.
    
    Args:
        tmp_path: Temporary directory path
        story_text: Text content to convert to speech
        filename: Output filename
        
    Returns:
        Path to the created audio file
    """
    return create_wav_file(
        text=story_text,
        output_path=tmp_path / filename,
        voice="Samantha",  # Child-friendly voice
        rate=160,          # Slightly slower rate for clarity
        sample_rate=16000,
        channels=1
    )


@pytest.fixture
def children_story_texts():
    """Sample children's story texts for audio generation."""
    return {
        "magic_garden": """
            The Magic Garden Adventure. In a colorful garden lived a curious butterfly named Flutter. 
            Flutter loved to explore and learn about all the flowers. One sunny morning, Flutter met 
            a wise old owl named Professor Hoot. Would you like to learn about the special magic of 
            the garden, asked Professor Hoot. Oh yes, please, Flutter replied excitedly.
        """,
        
        "weather_lesson": """
            Let's Learn About the Weather! Today we're going to explore different types of weather. 
            When the sun is shining, we call it a sunny day. Sometimes clouds fill the sky, and it 
            might rain. Rain helps plants grow and gives us water to drink. In winter, it gets cold 
            and sometimes snows. Snowflakes are like tiny ice stars falling from the sky!
        """,

        "sharing_story": """
            The Tale of Two Friends. Once upon a time, there were two little mice named Hoppy and Squeaky. 
            They found a big piece of cheese in the garden. Hoppy wanted to share it with all their 
            friends, but Squeaky wanted to keep it all. Let's share it, said Hoppy. Sharing makes 
            everything more fun and brings friends together.
        """,
        
        "nature_adventure": """
            Exploring the Forest. The little rabbit hopped through the green forest, discovering 
            beautiful flowers and tall trees. The sun filtered through the leaves, creating dancing 
            shadows on the forest floor. Birds sang cheerful songs while butterflies danced from 
            flower to flower. Nature is full of wonderful surprises for those who take time to explore.
        """
    }


# Subject identification test fixtures

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
def multilingual_text():
    """Text with mixed languages."""
    return """
    The machine learning conference was excellent. Les présentations étaient fascinantes. 
    Die Technologie entwickelt sich schnell.
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
def educational_content_texts():
    """Educational content texts for testing learning-focused audio."""
    return {
        "counting_lesson": """
            Let's Count Together! One butterfly, two flowers, three buzzing bees. Four little frogs 
            by the pond, five colorful birds in the tree. Counting is fun when we practice every day. 
            Can you count along with me? Let's try again from the beginning.
        """,
        
        "colors_lesson": """
            Learning About Colors. Red roses in the garden, yellow sunshine in the sky. Blue water 
            in the pond, green grass all around. Orange carrots for the rabbits, purple flowers 
            so bright. Colors make our world beautiful and help us learn about everything we see.
        """,
        
        "kindness_lesson": """
            Being Kind to Others. When we help our friends, we feel happy inside. Sharing toys, 
            saying please and thank you, and helping when someone falls down. These are all ways 
            to show kindness. Remember, being kind makes everyone feel special and loved.
        """
    }


@pytest.fixture
def story_audio_creator():
    """Factory fixture for creating story audio files."""
    return create_story_audio_file


@pytest_asyncio.fixture(autouse=True)
async def cleanup_resources():
    """Automatically cleanup resources after each test."""
    yield
    
    # Force garbage collection to cleanup any lingering resources
    import gc
    gc.collect()
    
    # Small delay to allow SSL connections to close
    try:
        await asyncio.sleep(0.05)
    except Exception:
        pass
