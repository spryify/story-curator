"""
Keyword-based subject identification processor.
"""
import re
from typing import Dict, Set, List, Tuple
import string
from collections import Counter
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

class KeywordProcessor:
    """Processes text to extract keywords and technical terms."""
    
    def __init__(self):
        """Initialize processor with stopwords and patterns."""
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.stop_words.update([
            'would', 'could', 'should', 'said', 'says', 'say',
            'the', 'and', 'or', 'but', 'however', 'therefore', 'consequently',
            'although', 'nevertheless', 'moreover', 'furthermore'
        ])
        
        # Important compound words that shouldn't be split
        self.important_compounds = {
            'artificial intelligence': 0.9,
            'machine learning': 0.9,
            'cloud computing': 0.9,
            'technology companies': 0.8,
            'deep learning': 0.9,
            'natural language processing': 0.9,
            'computer vision': 0.9,
            'neural network': 0.9,
            'data science': 0.9,
            'quantum computing': 0.9
        }
        
        # Categories and topics with importance scores
        self.categories = {
            'technology': 0.8, 'science': 0.8, 'business': 0.7, 'finance': 0.7,
            'economic': 0.7, 'climate': 0.7, 'environment': 0.7, 'health': 0.7,
            'medical': 0.7, 'political': 0.6, 'space': 0.8, 'aerospace': 0.8,
            'research': 0.7, 'development': 0.7
        }
        
        # Compound categories that should be recognized together
        self.compound_categories = {
            'climate change': 0.8,
            'space exploration': 0.8,
            'space technology': 0.8,
            'technology companies': 0.8,
            'financial markets': 0.8,
            'market analysis': 0.8,
            'scientific research': 0.8,
            'aerospace industry': 0.8
        }
        
        # Tech keywords with importance scores
        self.tech_keywords = {
            'AI': 0.9, 'ML': 0.9, 'API': 0.8, 'SDK': 0.8,
            'REST': 0.8, 'JSON': 0.8, 'HTTP': 0.8,
            'Python': 0.9, 'JavaScript': 0.9, 'Java': 0.9,
            'Cloud': 0.8, 'Docker': 0.9, 'Kubernetes': 0.9,
            'SpaceX': 0.9, 'NASA': 0.9, 'Mars': 0.9,
            'rocket': 0.8, 'satellite': 0.8, 'orbit': 0.8
        }
        
        # Technical term patterns
        self.tech_patterns = [
            r'\b(?:[A-Z][a-z]+\s*){2,}\b',  # CamelCase phrases
            r'\b[A-Z][a-z]+(?:\d+[a-z]*)+\b',  # Version numbers
            r'\b[A-Z]{2,}(?:\s*\d*\.?\d+)?\b',  # Acronyms with optional numbers
            r'\b\w+(?:-\w+)+\b',  # Hyphenated terms
            r'\b\w+\+\+\b',  # C++, G++
            r'\b[A-Za-z]+#\b',  # C#
            r'\b[A-Za-z]+\.js\b',  # Node.js, React.js
            r'\b[A-Za-z]+\.py\b',  # Python files
        ]

    def process(self, text: str) -> Dict[str, float]:
        """Process text to extract and score keywords efficiently."""
        # Clean and prepare text
        text = self._clean_text(text)
        sentences = sent_tokenize(text)
        
        # Track all keywords and their scores
        keywords = {}
        total_words = 0
        max_freq = 0
        
        # Process sentences with positional weighting
        word_freqs = {}
        for i, sentence in enumerate(sentences):
            # Weight by position (earlier sentences more important)
            position_weight = 1.0 - (i / len(sentences)) * 0.3
            
                # Get words and filter
            words = word_tokenize(sentence.lower())
            filtered_words = self._filter_words(words)
            
            # Process ngrams first to catch important compounds
            for n in range(3, 0, -1):  # Try 3-grams down to 1-grams
                ngrams_list = list(ngrams(filtered_words, n))
                for gram in ngrams_list:
                    compound = ' '.join(gram)
                    if compound in self.important_compounds:
                        if compound not in word_freqs:
                            word_freqs[compound] = 0.0
                        freq = position_weight * 3  # Higher weight for compounds
                        word_freqs[compound] += freq
                        max_freq = max(max_freq, word_freqs[compound])
                    elif n > 1 and compound in self.compound_categories:
                        if compound not in word_freqs:
                            word_freqs[compound] = 0.0
                        freq = position_weight * 2.5  # Good weight for category compounds
                        word_freqs[compound] += freq
                        max_freq = max(max_freq, word_freqs[compound])
            
            # Then process individual words
            for word in filtered_words:
                if word not in word_freqs:
                    word_freqs[word] = 0.0
                freq = position_weight * (2 if word in self.tech_keywords else 1)
                word_freqs[word] += freq
                max_freq = max(max_freq, word_freqs[word])
            
            total_words += len(filtered_words)
            
            # Extract technical terms and important compounds first
            tech_terms = self._extract_technical_terms(sentence)
            found_terms = set()
            for term, score in tech_terms:
                found_terms.add(term.lower())
                keywords[term] = score

            # Then check for important compounds and categories
            lower_sent = sentence.lower()
            for compound in self.important_compounds.keys():
                if compound in lower_sent and compound not in found_terms:
                    keywords[compound] = self.important_compounds[compound]
                    found_terms.add(compound)

            # Then check compound categories
            for compound in self.compound_categories.keys():
                if compound in lower_sent and compound not in found_terms:
                    keywords[compound] = self.compound_categories[compound]
                    found_terms.add(compound)
        
        # Score remaining words
        if total_words > 0:
            # Sort by frequency and get top 50
            sorted_words = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)[:50]
            for word, freq in sorted_words:
                if word in self.stop_words or len(word) < 3:
                    continue
                    
                # Base score from frequency
                base_score = min(0.6, (freq / max_freq) * 0.6)  # Lower base scores
                final_score = base_score

                # Apply score boosts based on word type
                if word in self.important_compounds:
                    final_score = min(0.9, final_score + 0.3)
                elif word in self.compound_categories:
                    final_score = min(0.8, final_score + 0.2)
                elif word in self.categories:
                    final_score = min(0.7, final_score + 0.1)
                elif word in self.tech_keywords:
                    final_score = min(0.8, final_score + 0.2)
                elif len(word.split()) > 1:  # Multi-word phrases
                    final_score = min(0.6, final_score + 0.1)                # Store highest score
                if word not in keywords or final_score > keywords[word]:
                    keywords[word] = final_score
        
        # Filter and return top results
        keywords = {k: v for k, v in keywords.items() if v >= 0.3}
        return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:25])

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text efficiently."""
        # Remove URLs and emails
        text = re.sub(r'http[s]?://\S+|\S+@\S+', '', text)
        
        # Remove punctuation except hyphens in compounds
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Normalize whitespace
        return ' '.join(text.split())

    def _filter_words(self, words: List[str]) -> List[str]:
        """Filter and normalize words with improved compound handling."""
        filtered = []
        text = ' '.join(words).lower()
        original_text = text
        
        # Process compounds in order of length (longest first)
        compounds = sorted(
            list(self.important_compounds.keys()) +
            list(self.compound_categories.keys()) +
            list(self.categories.keys()),
            key=len, reverse=True
        )
        
        # Extract compounds first
        for compound in compounds:
            if compound in text:
                filtered.append(compound)
                text = text.replace(compound, ' ')
        
        # Extract tech keywords
        for keyword in sorted(self.tech_keywords.keys(), key=len, reverse=True):
            if keyword.lower() in text:
                filtered.append(keyword)
                text = text.replace(keyword.lower(), ' ')
        
        # Process remaining words
        remaining_words = text.split()
        for i, word in enumerate(remaining_words):
            if len(word) < 3 or word in self.stop_words:
                continue
                
            word = self.lemmatizer.lemmatize(word)
            if word.isalpha():
                filtered.append(word)
                
                # Look for contextual phrases
                if i < len(remaining_words) - 1:
                    next_word = remaining_words[i + 1]
                    if len(next_word) >= 3 and next_word not in self.stop_words:
                        phrase = f"{word} {next_word}"
                        if phrase in original_text:
                            filtered.append(phrase)
        
        return filtered

    def _extract_technical_terms(self, text: str) -> Set[Tuple[str, float]]:
        """Extract technical terms with optimized scoring."""
        tech_terms = set()
        
        # Check predefined tech keywords first
        for term, score in self.tech_keywords.items():
            if re.search(rf'\b{re.escape(term)}\b', text, re.IGNORECASE):
                tech_terms.add((term, score))
        
        # Extract terms using patterns
        for pattern in self.tech_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group()
                if len(term) >= 2 and not term.lower() in self.stop_words:
                    tech_terms.add((term, 0.7))
        
        return tech_terms
