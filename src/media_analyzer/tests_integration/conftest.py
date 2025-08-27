"""Audio analysis integration test fixtures."""

import pytest
import sys
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
            and sometimes snows.
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
