"""Tests for keyword processor."""
import pytest
import time

from media_analyzer.processors.subject.extractors.keyword_extractor import KeywordExtractor


class TestKeywordExtractor:
    """Test suite for keyword extraction processor."""
    
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction."""
        processor = KeywordExtractor()
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
        assert result["metadata"]["processor_type"] == "KeywordExtractor"
        assert "version" in result["metadata"]
        
    def test_keyword_scoring(self):
        """Test keyword scoring mechanism."""
        processor = KeywordExtractor()
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
        processor = KeywordExtractor()
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
        processor = KeywordExtractor()
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
        processor = KeywordExtractor()
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
        processor = KeywordExtractor()
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
        
        # Common phrases should have higher confidence due to repetition
        assert train_score > 0.5  # Adjust threshold based on actual implementation
        assert hill_score > 0.5
        
    def test_age_appropriate_content(self):
        """Test handling of age-appropriate vs complex content."""
        processor = KeywordExtractor()
        
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


class TestEnhancedNLPFunctionality:
    """Test suite for enhanced NLP functionality in KeywordExtractor."""
    
    def test_compound_phrase_detection(self):
        """Test dynamic compound phrase detection using spaCy."""
        processor = KeywordExtractor()
        
        # Text with clear compound phrases
        text = """
        The brave knight rode through the enchanted forest.
        The magical princess lived in the ancient castle.
        The wise wizard cast powerful spells.
        """
        
        result = processor.process(text)
        keywords = result["results"].keys()
        
        # Should detect compound phrases
        compound_phrases = [k for k in keywords if len(k.split()) > 1]
        assert len(compound_phrases) > 0, "Should detect compound phrases"
        
        # Look for expected compound phrases
        keywords_lower = [k.lower() for k in keywords]
        expected_compounds = ["brave knight", "enchanted forest", "magical princess", "ancient castle"]
        
        found_compounds = []
        for expected in expected_compounds:
            if any(expected in k for k in keywords_lower):
                found_compounds.append(expected)
        
        assert len(found_compounds) > 0, f"Should find some compound phrases from {expected_compounds}"
    
    def test_pos_tagging_filtering(self):
        """Test that POS tagging properly filters for meaningful words."""
        processor = KeywordExtractor()
        
        # Text with various parts of speech
        text = """
        The beautiful red car quickly drove through the busy street.
        She was very happy and excited about the wonderful opportunity.
        """
        
        result = processor.process(text)
        keywords = [k.lower() for k in result["results"].keys()]
        
        # Should include meaningful nouns and adjectives
        meaningful_words = ["car", "street", "opportunity", "beautiful", "red", "busy", "happy", "excited", "wonderful"]
        found_meaningful = [word for word in meaningful_words if any(word in k for k in keywords)]
        
        assert len(found_meaningful) > 0, "Should extract meaningful nouns and adjectives"
        
        # Should filter out stopwords and function words
        filtered_words = ["the", "was", "very", "and", "about", "through"]
        found_filtered = [word for word in filtered_words if any(word == k for k in keywords)]
        
        # Most stopwords should be filtered out (allow some flexibility)
        assert len(found_filtered) <= len(filtered_words) // 2, "Should filter out most stopwords"
    
    def test_nlp_library_integration(self):
        """Test integration with NLTK, spaCy, and sklearn libraries."""
        processor = KeywordExtractor()
        
        # Test text that benefits from NLP processing
        text = """
        Natural language processing enables computers to understand human language.
        Machine learning algorithms improve through training data.
        Deep learning neural networks recognize patterns automatically.
        """
        
        result = processor.process(text)
        
        # Should extract technical terms and phrases
        keywords_lower = [k.lower() for k in result["results"].keys()]
        
        # Technical terms that should be extracted
        expected_terms = [
            "natural language processing", "machine learning", "deep learning",
            "neural networks", "algorithms", "training data", "patterns"
        ]
        
        found_terms = []
        for term in expected_terms:
            if any(term in k or any(word in k for word in term.split()) for k in keywords_lower):
                found_terms.append(term)
        
        assert len(found_terms) >= 3, f"Should extract technical terms, found: {found_terms}"
    
    def test_confidence_scoring_with_nlp(self):
        """Test that NLP-enhanced confidence scoring works properly."""
        processor = KeywordExtractor()
        
        # Text with repeated important terms
        text = """
        The princess was a kind princess. The princess helped everyone.
        The king trusted the princess completely. The princess was wise.
        """
        
        result = processor.process(text)
        results = result["results"]
        
        # "princess" should have high confidence due to frequency
        princess_confidence = max(
            (score for key, score in results.items() if "princess" in key.lower()),
            default=0
        )
        
        assert princess_confidence > 0.7, "Frequently mentioned terms should have high confidence"
        
        # All confidence scores should be valid
        assert all(0 <= score <= 1 for score in results.values())
    
    def test_dynamic_compound_detection_vs_hardcoded(self):
        """Test that dynamic compound detection works without hardcoded phrases."""
        processor = KeywordExtractor()
        
        # Text with domain-specific compounds not in hardcoded lists
        text = """
        The quantum computer processed the complex algorithms.
        The space station orbited the distant planet.
        The solar panels generated renewable energy.
        """
        
        result = processor.process(text)
        keywords_lower = [k.lower() for k in result["results"].keys()]
        
        # Should dynamically detect domain-specific compounds
        potential_compounds = [k for k in keywords_lower if len(k.split()) > 1]
        
        # Look for science/tech compounds that wouldn't be hardcoded
        science_compounds = [
            "quantum computer", "space station", "solar panels", 
            "renewable energy", "complex algorithms", "distant planet"
        ]
        
        found_science = []
        for compound in science_compounds:
            if any(compound in k for k in keywords_lower):
                found_science.append(compound)
        
        # Should find some domain-specific compounds dynamically
        assert len(found_science) > 0 or len(potential_compounds) > 0, \
            "Should detect domain-specific compounds without hardcoding"
