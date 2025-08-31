"""Subject identifier implementation."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, Set, Optional, Any, List
import time
from langdetect import detect_langs
import psutil

from media_analyzer.models.subject import (
    Category,
    SubjectMetadata,
    ProcessingMetrics,
    Subject,
    Context,
    SubjectAnalysisResult,
    SubjectType
)
from media_analyzer.processors.subject.extractors.keyword_extractor import KeywordExtractor
from media_analyzer.processors.subject.extractors.topic_extractor import TopicExtractor
from media_analyzer.processors.subject.extractors.entity_extractor import EntityExtractor
from media_analyzer.processors.subject.exceptions import (
    ProcessingError,
    SubjectProcessingError,
    InvalidInputError
)

logger = logging.getLogger(__name__)


class SubjectIdentifier:
    """Identifies subjects in text using multiple processors."""

    def __init__(self, max_workers: int = 3, timeout_ms: int = 800):
        """Initialize identifier with config.
        
        Args:
            max_workers: Maximum number of parallel processors
            timeout_ms: Overall timeout in milliseconds. Default 800ms per FR-002.
        """
        self.keyword_processor = KeywordExtractor()
        self.topic_processor = TopicExtractor()
        self.entity_processor = EntityExtractor()
        self.max_workers = max_workers
        self.timeout_ms = timeout_ms
        self._initialize_categories()
        self._result_cache = {}  # Cache for processor results

    def _initialize_categories(self):
        """Initialize category mapping."""
        self.categories = {
            Category("CHARACTERS", "Story Characters"),
            Category("PLACES", "Locations & Places"),
            Category("THEMES", "Story Themes & Values"),
            Category("OBJECTS", "Important Objects"),
            Category("CULTURE", "Cultural Elements")
        }

        # Define category keywords with scores - focused on storytelling elements
        self.category_keywords = {
            "CHARACTERS": {
                'princess': 1.0, 'prince': 1.0, 'king': 1.0, 'queen': 1.0,
                'emperor': 0.9, 'empress': 0.9, 'ruler': 0.8, 'hero': 0.9,
                'heroine': 0.9, 'warrior': 0.8, 'knight': 0.8, 'dragon': 0.9,
                'fairy': 0.8, 'witch': 0.8, 'wizard': 0.8, 'giant': 0.8,
                'monster': 0.7, 'beast': 0.7, 'merchant': 0.7, 'farmer': 0.7,
                'fisherman': 0.7, 'hunter': 0.7, 'mother': 0.6, 'father': 0.6,
                'brother': 0.6, 'sister': 0.6, 'grandmother': 0.7, 'grandfather': 0.7
            },
            "PLACES": {
                'kingdom': 1.0, 'palace': 0.9, 'castle': 0.9, 'village': 0.9,
                'forest': 0.9, 'mountain': 0.8, 'river': 0.8, 'ocean': 0.8,
                'desert': 0.8, 'cave': 0.8, 'temple': 0.8, 'tower': 0.8,
                'bridge': 0.7, 'garden': 0.7, 'market': 0.7, 'inn': 0.7,
                'island': 0.8, 'valley': 0.7, 'hill': 0.6, 'lake': 0.7,
                'india': 0.9, 'china': 0.9, 'japan': 0.9, 'africa': 0.9,
                'europe': 0.8, 'asia': 0.8, 'country': 0.6, 'land': 0.6
            },
            "THEMES": {
                'love': 0.9, 'courage': 1.0, 'bravery': 1.0, 'persistence': 1.0,
                'kindness': 1.0, 'wisdom': 0.9, 'friendship': 0.9, 'loyalty': 0.9,
                'honesty': 0.9, 'justice': 0.9, 'compassion': 0.9, 'generosity': 0.9,
                'patience': 0.8, 'forgiveness': 0.8, 'sacrifice': 0.8, 'devotion': 0.9,
                'determination': 0.9, 'perseverance': 0.9, 'strength': 0.8, 'hope': 0.8,
                'faith': 0.7, 'trust': 0.7, 'respect': 0.7, 'responsibility': 0.7
            },
            "OBJECTS": {
                'sword': 0.9, 'crown': 0.9, 'ring': 0.8, 'necklace': 0.8,
                'gem': 0.8, 'jewel': 0.8, 'treasure': 0.9, 'gold': 0.8,
                'silver': 0.7, 'mirror': 0.8, 'book': 0.7, 'scroll': 0.8,
                'potion': 0.8, 'spell': 0.8, 'magic': 0.9, 'wand': 0.8,
                'staff': 0.7, 'cloak': 0.7, 'boots': 0.6, 'key': 0.7,
                'door': 0.6, 'chest': 0.7, 'box': 0.6
            },
            "CULTURE": {
                'tradition': 0.8, 'ceremony': 0.8, 'festival': 0.8, 'celebration': 0.8,
                'ritual': 0.8, 'custom': 0.7, 'legend': 0.9, 'myth': 0.9,
                'folklore': 1.0, 'tale': 0.8, 'story': 0.7, 'dance': 0.7,
                'music': 0.7, 'song': 0.7, 'prayer': 0.7, 'blessing': 0.7,
                'ancient': 0.8, 'old': 0.6, 'wise': 0.7, 'sacred': 0.8
            }
        }

    def identify_subjects(self, text: str, context: Optional[Context] = None) -> SubjectAnalysisResult:
        """
        Identify subjects in text using multiple processors.
        
        Args:
            text: Input text to analyze
            context: Optional context information
            
        Returns:
            SubjectAnalysisResult with identified subjects and metadata
        
        Raises:
            ProcessingError: If subject identification fails
            InvalidInputError: If input validation fails
        """
        start_time = time.time()
        mem_usage_start = psutil.Process().memory_info().rss / 1024 / 1024
        processor_errors = {}

        try:
            # Input validation
            if not text or not text.strip():
                raise InvalidInputError("Input text cannot be empty")
                
            if len(text) < 10:
                raise InvalidInputError("Text too short for meaningful analysis")

            # Preprocess text to focus on story content
            processed_text = self._preprocess_for_story_content(text)
            
            # Detect languages
            languages = self._detect_languages(processed_text)
            
            # Process with each processor
            processor_results = {}

            def run_processor(proc_name: str, processor: Any) -> Dict[str, float]:
                """Run a processor with error handling."""
                try:
                    # Optimized caching with text length consideration
                    text_length = len(processed_text)
                    # Use smaller sample for cache key if text is very long
                    cache_text = processed_text[:1000] if text_length > 1000 else processed_text
                    cache_key = f"{proc_name}:{hash(cache_text)}"
                    
                    if cache_key in self._result_cache:
                        return self._result_cache[cache_key]
                    
                    # For very long text, chunk processing for speed
                    if text_length <= 1000 or proc_name != "entity":  # Full cache for short text or non-entity processors
                        results = processor.process(processed_text)
                    else:
                        # Split into chunks for entity processor on long text
                        chunks = [processed_text[i:i+800] for i in range(0, len(processed_text), 800)]
                        results = {}
                        # Process only first few chunks to maintain speed
                        for chunk in chunks[:3]:  # Process only first 3 chunks for speed
                            chunk_results = processor.process(chunk)
                            results.update(chunk_results)
                    
                    self._result_cache[cache_key] = results
                    return results
                except Exception as e:
                    logger.warning(f"Processor {proc_name} failed: {str(e)}")
                    processor_errors[f"{proc_name}_error"] = str(e)
                    return {}

            # Run processors in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Use shorter timeouts for each processor and give more time for overhead
                # Optimize timeouts for maximum efficiency
                processor_timeouts = {
                    "topic": int(0.15 * self.timeout_ms),    # 15% - fastest processor
                    "keyword": int(0.30 * self.timeout_ms),  # 30% - critical for accuracy
                    "entity": int(0.25 * self.timeout_ms)    # 25% - balance speed and accuracy
                }  # Leaves 30% for language detection and result processing
                
                # Submit all processors with their timeouts
                futures = {
                    executor.submit(run_processor, "topic", self.topic_processor): ("topic", processor_timeouts["topic"]),
                    executor.submit(run_processor, "entity", self.entity_processor): ("entity", processor_timeouts["entity"]),
                    executor.submit(run_processor, "keyword", self.keyword_processor): ("keyword", processor_timeouts["keyword"])
                }

                # Process futures with optimized timeout handling
                end_time = time.monotonic() + (self.timeout_ms / 1000)
                futures_list = list(futures.items())
                
                # Sort futures by processor priority (keyword and entity first)
                futures_list.sort(key=lambda x: 0 if x[1][0] in ['keyword', 'entity'] else 1)
                
                for future, (proc_name, proc_timeout) in futures_list:
                    try:
                        # Calculate remaining time
                        remaining = end_time - time.monotonic()
                        if remaining <= 0:
                            # Cancel remaining processors if we're out of time
                            future.cancel()
                            continue
                            
                        # Use adjusted timeout for better performance
                        timeout = min(remaining, proc_timeout / 1000)
                        result = future.result(timeout=timeout)
                        
                        if result:
                            processor_results[proc_name] = result
                    except TimeoutError:
                        error_msg = f"{proc_name} processor timed out"
                        logger.warning(error_msg)
                        processor_errors[f"{proc_name}_error"] = error_msg
                        future.cancel()  # Cancel timed out processor
                    except Exception as e:
                        error_msg = f"{proc_name} processing failed: {str(e)}"
                        logger.warning(error_msg)
                        processor_errors[f"{proc_name}_error"] = error_msg
                        # Don't raise, continue processing other futures

            # Convert results to subjects
            subjects = set()
            categories = set()

            # Process each processor's results
            for proc_name, results in processor_results.items():
                # Create category
                category = Category(
                    id=proc_name.upper(),
                    name=proc_name
                )
                categories.add(category)

                # Add subjects from processor results
                if isinstance(results, dict) and "results" in results:
                    results_dict = results["results"]
                else:
                    results_dict = results

                # Add subjects with adjusted confidence
                if isinstance(results_dict, dict):
                    # First pass to find max confidence for normalization
                    numeric_values = []
                    for v in results_dict.values():
                        if isinstance(v, (int, float)):
                            numeric_values.append(float(v))
                        elif isinstance(v, str):
                            try:
                                numeric_values.append(float(v))
                            except ValueError:
                                pass  # Skip non-numeric strings
                        elif isinstance(v, dict) and 'confidence' in v:
                            try:
                                numeric_values.append(float(v['confidence']))
                            except (ValueError, TypeError):
                                pass
                    
                    # Ensure all values in numeric_values are actually numeric before calling max()
                    clean_numeric_values = []
                    for val in numeric_values:
                        if isinstance(val, (int, float)) and not isinstance(val, bool):
                            clean_numeric_values.append(float(val))
                    
                    max_conf = max(clean_numeric_values) if clean_numeric_values else 1.0
                                 
                    for name, confidence in results_dict.items():
                        # Normalize name for comparison
                        name = name.strip().lower()
                        
                        # Skip duplicate and similar subjects
                        if any(self._are_similar_subjects(s.name, name) for s in subjects):
                            continue
                            
                        # Normalize confidence against max value
                        try:
                            max_conf_float = float(max_conf)
                            if isinstance(confidence, dict) and 'confidence' in confidence:
                                conf_val = float(confidence['confidence'])
                            elif isinstance(confidence, (int, float)):
                                conf_val = float(confidence)
                            elif isinstance(confidence, str):
                                conf_val = float(confidence)
                            else:
                                conf_val = 0.5
                            norm_conf = conf_val / max_conf_float if max_conf_float > 0 else 0.5
                        except (TypeError, ValueError):
                            norm_conf = 0.5
                            
                        # Check if it's a predefined category keyword
                        found_keywords = []
                        category_confidence = 0.0
                        matching_category = None

                        # First try exact matches
                        for cat, keywords in self.category_keywords.items():
                            if name in keywords:
                                found_keywords.append(name)
                                category_confidence = keywords[name]
                                matching_category = cat
                                break

                        # If no exact match, try partial matches
                        if not found_keywords:
                            for cat, keywords in self.category_keywords.items():
                                for kw, score in keywords.items():
                                    # Try both directions and word-level matching
                                    if (kw in name) or (name in kw) or any(w in name.split() for w in kw.split()):
                                        found_keywords.append(kw)
                                        if score > category_confidence:
                                            category_confidence = score
                                            matching_category = cat

                        # Handle confidence scoring
                        if isinstance(confidence, dict) and 'confidence' in confidence:
                            conf_value = float(str(confidence['confidence']))
                        elif isinstance(confidence, (int, float)):
                            conf_value = float(confidence)
                        elif isinstance(confidence, str):
                            try:
                                conf_value = float(confidence)
                            except ValueError:
                                conf_value = 0.5
                        else:
                            conf_value = 0.5

                        # Boost confidence based on matches and context
                        if found_keywords:
                            # Boost more for exact matches, less for partial
                            conf_value = max(conf_value, category_confidence)
                            if name in found_keywords:  # Exact match
                                conf_value = min(1.0, conf_value * 1.2)
                            if context and hasattr(context, 'domain'):
                                if context.domain.upper() == matching_category:
                                    conf_value = min(1.0, conf_value * 1.1)
                            
                        conf_value = max(0.0, min(1.0, conf_value))

                        subject = Subject(
                            name=name,
                            subject_type=getattr(SubjectType, proc_name.upper()),
                            confidence=conf_value,
                            context=context
                        )
                        subjects.add(subject)

            # Calculate metrics
            processing_time = (time.time() - start_time) * 1000
            memory_usage = (psutil.Process().memory_info().rss / 1024 / 1024) - mem_usage_start
            
            # Build metadata
            metadata = {
                "processing_time_ms": processing_time,
                "memory_usage_mb": memory_usage,
                "text_length": len(processed_text),
                "original_text_length": len(text),  # Track both original and processed length
                "parallel_execution": True,
                "languages_detected": languages
            }

            # Always include errors dictionary in metadata
            metadata["errors"] = processor_errors
            
            # Filter and rank subjects
            sorted_subjects = sorted(subjects, key=lambda s: s.confidence, reverse=True)
            top_subjects = set(sorted_subjects[:20])  # Limit to top 20 subjects
            
            # Ensure we include all high-confidence subjects
            high_conf_subjects = {s for s in subjects if s.confidence >= 0.8}
            
            # Create result with merged subjects
            result = SubjectAnalysisResult(
                subjects=top_subjects.union(high_conf_subjects),
                categories=categories,
                metadata=metadata
            )            # Validate result
            if not subjects:
                logger.warning("No subjects were identified")

            return result

        except InvalidInputError:
            raise
        except TimeoutError as e:
            logger.error(f"Subject identification timed out: {str(e)}")
            raise SubjectProcessingError(f"Subject identification timed out after {self.timeout_ms}ms")
        except Exception as e:
            logger.error(f"Subject identification failed: {str(e)}")
            raise SubjectProcessingError(f"Subject identification failed: {str(e)}")

    def _detect_languages(self, text: str) -> List[str]:
        """Detect languages in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of language codes with high confidence
        """
        try:
            # Fast multilingual detection with natural splits
            detected = set()
            
            # First try natural paragraph splits
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            if not paragraphs:
                paragraphs = [text]
            
            # Add sentence splits for shorter texts
            if len(paragraphs) < 3:
                sentences = [s.strip() for s in text.replace('\n', '. ').split('.') if s.strip()]
                paragraphs.extend(s for s in sentences if len(s) > 30)  # Only add longer sentences
                
            # Take unique samples to avoid double-counting
            seen = set()
            samples = []
            for p in paragraphs:
                if p not in seen and len(p) > 30:  # Only include substantial samples
                    samples.append(p)
                    seen.add(p)
            samples = samples[:5]  # Limit samples to avoid too many API calls
                
            for sample in samples:
                try:
                    langs = detect_langs(sample.strip())
                    detected.update(str(lang.lang) for lang in langs if lang.prob > 0.01)  # Very low threshold to catch even minor language presence
                    if len(detected) >= 3:  # Exit early if we find enough languages
                        break
                except:
                    continue
                        
            return list(detected)
        except:
            return []

    def _run_processor(self, processor_name: str, processor: Any, text: str) -> Dict[str, float]:
        """Run a single processor and handle errors."""
        try:
            return processor.process(text)
        except Exception as e:
            logger.warning(f"{processor_name} processing failed: {str(e)}")
            return {}

    def _are_similar_subjects(self, name1: str, name2: str) -> bool:
        """Check if two subject names are similar or duplicates."""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Exact match
        if name1 == name2:
            return True
            
        # One is substring of the other and length difference is small
        if (name1 in name2 or name2 in name1) and abs(len(name1) - len(name2)) <= 3:
            return True
            
        # Use word-level comparison for multi-word subjects
        words1 = set(name1.split())
        words2 = set(name2.split())
        common_words = words1.intersection(words2)
        
        # If they share most words and lengths are similar
        if len(common_words) >= min(len(words1), len(words2)) * 0.8:
            return True
            
        return False

    def _preprocess_for_story_content(self, text: str) -> str:
        """Preprocess text to focus on story content and filter out podcast metadata.
        
        Args:
            text: Raw transcription text
            
        Returns:
            Processed text focusing on story content
        """
        import re
        
        # Common podcast metadata patterns to remove or de-emphasize
        metadata_patterns = [
            # Host introductions and outros
            r'hi,?\s+\w+\s+\w+\s+here\.?',
            r'i\'?m\s+\w+\s+\w+',
            r'this is \w+',
            r'welcome to \w+',
            r'thanks for listening',
            # Tour and event announcements
            r'going (?:back )?on tour',
            r'live recordings?',
            r'our (?:first|next) stop',
            r'at the \w+ center',
            r'club members are invited',
            r'post-show meet',
            # Dates and locations (when not part of story)
            r'sunday,?\s+\w+ \d+(?:st|nd|rd|th)?',
            r'in \w+, \w+(?:,\s+\w+)?',  # "in Parker, Colorado"
            # Generic podcast structure
            r'before we get to our story',
            r'exciting news',
            r'now let\'?s get to our story',
            r'our story today',
            r'let me tell you about',
            # Circle Round specific patterns
            r'circle round',
            r'wbur',
            r'rebecca sch?ie?r?'
        ]
        
        lines = text.split('.')
        filtered_lines = []
        story_started = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line contains metadata
            is_metadata = False
            line_lower = line.lower()
            
            for pattern in metadata_patterns:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    is_metadata = True
                    break
            
            # Look for story beginning indicators
            story_indicators = [
                r'once upon a time',
                r'long ago',
                r'there (?:was|were|lived)',
                r'in a (?:far|distant|magical|ancient)',
                r'many years? ago',
                r'princess \w+',
                r'king \w+',
                r'queen \w+',
                r'prince \w+',
                r'in (?:the )?(?:kingdom|land|village|forest) of',
                # Story transition phrases
                r'our story (?:begins|takes place)',
                r'let\'?s begin',
                r'the story goes'
            ]
            
            # Check if story content is starting
            for indicator in story_indicators:
                if re.search(indicator, line_lower, re.IGNORECASE):
                    story_started = True
                    break
            
            # Keep non-metadata lines, or all lines once story starts
            if not is_metadata or story_started:
                filtered_lines.append(line)
            
            # If we detect clear story content, prioritize everything after this point
            if story_started:
                # From here on, include everything (even if it matches metadata patterns)
                # as it might be part of the story context
                pass
        
        processed_text = '. '.join(filtered_lines).strip()
        
        # If we removed too much content, fall back to original
        if len(processed_text) < len(text) * 0.3:  # Less than 30% remaining
            logger.warning("Story content filtering removed too much text, using original")
            return text
            
        logger.debug(f"Story content filtering: {len(text)} -> {len(processed_text)} characters")
        return processed_text if processed_text else text
