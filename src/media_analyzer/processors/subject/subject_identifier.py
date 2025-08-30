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
from media_analyzer.processors.subject.processors.keyword_processor import KeywordProcessor
from media_analyzer.processors.subject.processors.topic_processor import TopicProcessor
from media_analyzer.processors.subject.processors.entity_processor import EntityProcessor
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
        self.keyword_processor = KeywordProcessor()
        self.topic_processor = TopicProcessor()
        self.entity_processor = EntityProcessor()
        self.max_workers = max_workers
        self.timeout_ms = timeout_ms
        self._initialize_categories()
        self._result_cache = {}  # Cache for processor results

    def _initialize_categories(self):
        """Initialize category mapping."""
        self.categories = {
            Category("TECH", "Technology & Computing"),
            Category("BIOTECH", "Biotechnology & Science"),
            Category("FINANCE", "Finance & Economics"),
            Category("BUSINESS", "Business & Industry")
        }

        # Define category keywords with scores
        self.category_keywords = {
            "TECH": {
                'artificial intelligence': 1.0, 'machine learning': 1.0,
                'deep learning': 0.9, 'neural network': 0.9,
                'cloud computing': 0.9, 'technology': 0.8,
                'software': 0.8, 'data': 0.7, 'algorithm': 0.7,
                'computing': 0.7, 'computer': 0.7, 'code': 0.6,
                'programming': 0.8, 'developer': 0.7, 'system': 0.6,
                'microsoft': 0.9, 'google': 0.9, 'amazon': 0.9,
                'apple': 0.9, 'tech': 0.8, 'digital': 0.7
            },
            "BIOTECH": {
                'crispr': 1.0, 'genome': 0.9, 'dna': 0.9,
                'genetic': 0.9, 'biology': 0.8, 'protein': 0.8,
                'cell': 0.7, 'molecular': 0.8, 'biotechnology': 1.0,
                'biotech': 0.9, 'research': 0.6, 'science': 0.7,
                'scientific': 0.7, 'laboratory': 0.7, 'experiment': 0.6,
                'clinical': 0.8, 'medical': 0.8, 'pharmaceutical': 0.9,
                'drug': 0.8, 'vaccine': 0.9, 'therapy': 0.8
            },
            "FINANCE": {
                'market': 0.8, 'stock': 0.9, 'investment': 0.9,
                'financial': 0.9, 'economy': 0.8, 'economic': 0.8,
                'bank': 0.8, 'trading': 0.8, 'investor': 0.8,
                'fund': 0.7, 'money': 0.7, 'price': 0.6,
                'revenue': 0.8, 'profit': 0.8, 'growth': 0.6,
                'market analysis': 0.9, 'stock market': 0.9,
                'wall street': 0.9, 'banking': 0.8
            },
            "BUSINESS": {
                'business': 0.8, 'company': 0.8, 'industry': 0.8,
                'corporate': 0.8, 'management': 0.7, 'strategy': 0.7,
                'startup': 0.8, 'enterprise': 0.8, 'innovation': 0.7,
                'market share': 0.8, 'competition': 0.7,
                'product': 0.6, 'service': 0.6, 'customer': 0.6,
                'partnership': 0.7, 'acquisition': 0.8, 'merger': 0.8,
                'leadership': 0.7, 'executive': 0.7
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

            # Detect languages
            languages = self._detect_languages(text)
            
            # Process with each processor
            processor_results = {}

            def run_processor(proc_name: str, processor: Any) -> Dict[str, float]:
                """Run a processor with error handling."""
                try:
                    # Optimized caching with text length consideration
                    text_length = len(text)
                    # Use smaller sample for cache key if text is very long
                    cache_text = text[:1000] if text_length > 1000 else text
                    cache_key = f"{proc_name}:{hash(cache_text)}"
                    
                    if cache_key in self._result_cache:
                        cached_result = self._result_cache[cache_key]
                        if text_length <= 1000 or proc_name != "entity":  # Full cache for short text or non-entity processors
                            return cached_result
                            
                    # Process with optimized text chunks if needed
                    if text_length > 5000 and proc_name == "entity":  # Only chunk for entity processor on long text
                        chunk_size = 2000
                        chunks = [text[i:i+chunk_size] for i in range(0, text_length, chunk_size)]
                        results = {}
                        for chunk in chunks[:3]:  # Process only first 3 chunks for speed
                            chunk_results = processor.process(chunk)
                            results.update(chunk_results)
                    else:
                        results = processor.process(text)
                        
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
                            numeric_values.append(v)
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
                    
                    max_conf = max(numeric_values) if numeric_values else 1.0
                                 
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
                "text_length": len(text),
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
