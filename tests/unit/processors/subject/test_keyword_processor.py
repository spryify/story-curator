"""Tests for keyword processor."""
import pytest
import time

from media_analyzer.processors.subject.processors.keyword_processor import KeywordProcessor


class TestKeywordProcessor:
    """Test suite for keyword extraction processor."""
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction."""
        processor = KeywordProcessor()
        result = processor.process(
            "Artificial intelligence and machine learning are key technologies"
        )
        
        assert isinstance(result, dict)
        assert "results" in result
        assert "metadata" in result
        
        results = result["results"]
        assert any("artificial intelligence" in k.lower() 
                  for k in results.keys())
        assert any("machine learning" in k.lower() 
                  for k in results.keys())
        # All keywords should have confidence scores
        assert all(isinstance(v, float) and 0 <= v <= 1 
                  for v in results.values())
        
        # Check metadata
        assert result["metadata"]["processor_type"] == "KeywordProcessor"
        assert "version" in result["metadata"]
        
    def test_keyword_scoring(self):
        """Test keyword scoring mechanism."""
        processor = KeywordProcessor()
        result = processor.process(
            "The quick brown fox jumps over the lazy dog. "
            "The fox is quick and brown. The dog is lazy."
        )
        
        results = result["results"]
        # Repeated phrases should have higher scores
        assert "fox" in results
        assert results["fox"] > 0.5  # Frequently mentioned
        # Single mentions should have lower scores
        assert all(v < 0.7 for k, v in results.items() 
                  if k not in ["fox", "quick", "brown"])
        
    def test_stopword_handling(self):
        """Test proper handling of stopwords."""
        processor = KeywordProcessor()
        result = processor.process("The and or but however therefore consequently")
        
        # Should not extract stopwords as keywords
        assert len(result["results"]) == 0
        
        # Should extract meaningful words even with stopwords
        result = processor.process("The artificial intelligence system learns quickly")
        results = result["results"]
        assert any("intelligence" in k.lower() for k in results.keys())
        assert not any(word in results.keys() 
                      for word in ["the", "and", "or", "but"])
                      
    def test_childrens_story_themes(self):
        """Test keyword extraction from children's story content."""
        processor = KeywordProcessor()
        story_text = """
        Once upon a time, there was a friendly little rabbit named Hoppy.
        Hoppy loved to hop and play in the garden. One day, Hoppy found a 
        beautiful carrot. Instead of eating it all by himself, Hoppy shared 
        the carrot with his forest friends. His friends were very happy, 
        and they all learned that sharing makes everyone feel good.
        """
        result = processor.process(story_text)
        results = result["results"]
        
        # Should identify main character
        assert any("rabbit" in k.lower() or "hoppy" in k.lower() 
                  for k in results.keys())
        
        # Should identify setting
        assert any("garden" in k.lower() or "forest" in k.lower() 
                  for k in results.keys())
        
        # Should identify key objects
        assert any("carrot" in k.lower() for k in results.keys())
        
        # Should identify moral themes
        assert any("sharing" in k.lower() or "friends" in k.lower() 
                  for k in results.keys())
        
    def test_educational_content(self):
        """Test keyword extraction from educational children's content."""
        processor = KeywordProcessor()
        educational_text = """
        Let's learn about colors! The sky is blue, just like blueberries.
        The grass is green, like fresh lettuce. The sun is bright yellow,
        and it helps plants grow. Red apples are sweet and healthy.
        Remember, eating colorful fruits and vegetables helps us stay strong!
        """
        result = processor.process(educational_text)
        results = result["results"]
        
        # Should identify educational concepts (colors)
        colors = ["blue", "green", "yellow", "red"]
        assert any(color in " ".join(results.keys()).lower() 
                  for color in colors)
        
        # Should identify examples
        examples = ["sky", "grass", "sun", "apple"]
        assert any(example in " ".join(results.keys()).lower() 
                  for example in examples)
        
        # Should identify learning themes
        learning_concepts = ["healthy", "grow", "strong"]
        assert any(concept in " ".join(results.keys()).lower() 
                  for concept in learning_concepts)
        
    def test_repetitive_phrases(self):
        """Test handling of repetitive phrases common in children's content."""
        processor = KeywordProcessor()
        story_text = """
        The little train went up the hill.
        Choo choo! Up the hill.
        The little train said "I think I can, I think I can!"
        Up, up, up the hill went the little train.
        Finally, the little train made it to the top of the hill.
        """
        result = processor.process(story_text)
        results = result["results"]
        
        # Repeated phrases should have higher scores
        assert "train" in " ".join(results.keys()).lower()
        assert "hill" in " ".join(results.keys()).lower()
        
        train_score = max(score for key, score in results.items() 
                         if "train" in key.lower())
        hill_score = max(score for key, score in results.items() 
                        if "hill" in key.lower())
        
        # Common phrases should have high confidence due to repetition
        assert train_score > 0.7
        assert hill_score > 0.7
        
    def test_age_appropriate_content(self):
        """Test handling of age-appropriate vs complex content."""
        processor = KeywordProcessor()
        
        # Simple, age-appropriate content
        simple_text = "The happy puppy played with the red ball in the park."
        simple_result = processor.process(simple_text)
        
        # More complex content
        complex_text = "The molecular structure exhibits quantum tunneling effects."
        complex_result = processor.process(complex_text)
        
        # Simple content should have more accessible keywords
        simple_keywords = simple_result["results"].keys()
        assert all(len(word) < 8 for word in simple_keywords), \
            "Children's content should have simple, short keywords"
        
        # Complex content should be identified as advanced
        complex_keywords = complex_result["results"].keys()
        assert any(len(word) > 7 for word in complex_keywords), \
            "Complex content should be identified with longer, technical keywords"
