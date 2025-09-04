#!/usr/bin/env python3
"""
Script to evaluate Circle Round podcast episodes with the audio icon matcher.
Tests 5 random episode indices and analyzes the quality of icon matches.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_icon_matcher.core.pipeline import AudioIconPipeline
from audio_icon_matcher.models.results import AudioIconResult, IconMatch


class CircleRoundEvaluator:
    """Evaluates Circle Round episodes with the audio icon matcher pipeline."""
    
    def __init__(self):
        self.pipeline = AudioIconPipeline()
        self.rss_url = "https://rss.wbur.org/circleround/podcast"
        self.results = []
        
    async def evaluate_episodes(self, num_episodes: int = 5) -> List[Dict[str, Any]]:
        """Evaluate multiple random Circle Round episodes."""
        
        print(f"🎭 Starting Circle Round Episode Evaluation")
        print(f"📡 RSS Feed: {self.rss_url}")
        print(f"🎯 Testing {num_episodes} random episodes")
        print("=" * 60)
        
        # Generate random episode indices (0-20 for recent episodes)
        episode_indices = random.sample(range(0, 21), num_episodes)
        print(f"📊 Selected episode indices: {episode_indices}")
        print()
        
        evaluation_results = []
        
        for i, episode_index in enumerate(episode_indices, 1):
            print(f"🎪 Processing Episode {i}/{num_episodes} (Index: {episode_index})")
            print("-" * 40)
            
            try:
                # Process the episode
                start_time = time.time()
                result = await self.pipeline.process_async(
                    self.rss_url,
                    max_icons=12,  # Get more icons for better evaluation
                    confidence_threshold=0.15,  # Lower threshold to see more matches
                    episode_index=episode_index
                )
                processing_time = time.time() - start_time
                
                # Evaluate the result
                evaluation = self._evaluate_result(result, episode_index, processing_time)
                evaluation_results.append(evaluation)
                
                # Display results
                self._display_episode_result(evaluation)
                
            except Exception as e:
                print(f"❌ Error processing episode {episode_index}: {e}")
                evaluation_results.append({
                    'episode_index': episode_index,
                    'success': False,
                    'error': str(e),
                    'processing_time': 0
                })
            
            print()
        
        # Display summary
        await self._display_summary(evaluation_results)
        
        return evaluation_results
    
    def _evaluate_result(self, result: AudioIconResult, episode_index: int, processing_time: float) -> Dict[str, Any]:
        """Evaluate the quality of a single episode result."""
        
        if not result.success:
            return {
                'episode_index': episode_index,
                'success': False,
                'error': getattr(result, 'error', 'Unknown error'),
                'processing_time': processing_time
            }
        
        # Extract episode metadata
        episode_title = result.metadata.get('episode_title', 'Unknown')
        show_name = result.metadata.get('show_name', 'Unknown')
        
        # Analyze transcription quality
        transcription = result.transcription or ""
        transcription_length = len(transcription)
        transcription_confidence = getattr(result, 'transcription_confidence', 0.0)
        
        # Analyze icon matches
        icon_matches = result.icon_matches or []
        num_matches = len(icon_matches)
        
        # Calculate confidence statistics
        if icon_matches:
            confidences = [match.confidence for match in icon_matches]
            avg_confidence = statistics.mean(confidences)
            max_confidence = max(confidences)
            min_confidence = min(confidences)
        else:
            avg_confidence = max_confidence = min_confidence = 0.0
        
        # Analyze content relevance
        content_analysis = self._analyze_content_relevance(transcription, icon_matches)
        
        # Analyze subject extraction
        subjects = result.subjects or {}
        subject_types = list(subjects.keys()) if isinstance(subjects, dict) else []
        num_subjects = len(subject_types)
        
        return {
            'episode_index': episode_index,
            'success': True,
            'processing_time': processing_time,
            'episode_metadata': {
                'title': episode_title,
                'show_name': show_name,
            },
            'transcription_analysis': {
                'length': transcription_length,
                'confidence': transcription_confidence,
                'word_count': len(transcription.split()) if transcription else 0,
                'has_story_elements': self._has_story_elements(transcription)
            },
            'icon_analysis': {
                'num_matches': num_matches,
                'avg_confidence': avg_confidence,
                'max_confidence': max_confidence,
                'min_confidence': min_confidence,
                'confidence_distribution': self._categorize_confidences(icon_matches)
            },
            'subject_analysis': {
                'num_subject_types': num_subjects,
                'subject_types': subject_types,
                'total_subjects': sum(len(subj_list) if isinstance(subj_list, list) else 1 
                                    for subj_list in subjects.values()) if isinstance(subjects, dict) else 0
            },
            'content_relevance': content_analysis,
            'icon_matches': [
                {
                    'name': match.icon.name,
                    'confidence': match.confidence,
                    'match_reason': match.match_reason,
                    'category': getattr(match.icon, 'category', 'Unknown'),
                    'tags': getattr(match.icon, 'tags', [])
                }
                for match in icon_matches[:8]  # Top 8 matches for analysis
            ]
        }
    
    def _analyze_content_relevance(self, transcription: str, icon_matches: List[IconMatch]) -> Dict[str, Any]:
        """Analyze how well the icons match the transcribed content."""
        
        if not transcription or not icon_matches:
            return {
                'story_themed_icons': 0,
                'character_icons': 0,
                'educational_icons': 0,
                'general_relevance_score': 0.0
            }
        
        transcription_lower = transcription.lower()
        
        # Count different types of relevant icons
        story_themed = 0
        character_icons = 0
        educational_icons = 0
        
        # Story theme keywords
        story_themes = [
            'adventure', 'fairy', 'magic', 'forest', 'castle', 'princess', 'prince',
            'dragon', 'treasure', 'quest', 'journey', 'tale', 'legend'
        ]
        
        # Character keywords
        character_terms = [
            'animal', 'cat', 'dog', 'bird', 'rabbit', 'bear', 'lion', 'elephant',
            'person', 'child', 'family', 'friend', 'monster', 'creature'
        ]
        
        # Educational keywords
        educational_terms = [
            'learn', 'school', 'teach', 'science', 'math', 'read', 'book',
            'color', 'number', 'letter', 'count', 'alphabet'
        ]
        
        for match in icon_matches:
            icon_name = match.icon.name.lower()
            icon_tags = [tag.lower() for tag in (getattr(match.icon, 'tags', []) or [])]
            all_icon_terms = [icon_name] + icon_tags
            
            # Check for story themes
            if any(theme in term for theme in story_themes for term in all_icon_terms):
                story_themed += 1
            
            # Check for characters
            if any(char in term for char in character_terms for term in all_icon_terms):
                character_icons += 1
            
            # Check for educational content
            if any(edu in term for edu in educational_terms for term in all_icon_terms):
                educational_icons += 1
        
        # Calculate general relevance score
        total_matches = len(icon_matches)
        relevant_matches = story_themed + character_icons + educational_icons
        relevance_score = relevant_matches / total_matches if total_matches > 0 else 0.0
        
        return {
            'story_themed_icons': story_themed,
            'character_icons': character_icons,
            'educational_icons': educational_icons,
            'general_relevance_score': relevance_score,
            'total_analyzed': total_matches
        }
    
    def _has_story_elements(self, transcription: str) -> bool:
        """Check if transcription contains typical story elements."""
        if not transcription:
            return False
            
        story_indicators = [
            'once upon a time', 'long ago', 'there was', 'there were',
            'in a faraway', 'in a distant', 'story', 'tale', 'adventure',
            'character', 'hero', 'villain', 'journey', 'quest'
        ]
        
        transcription_lower = transcription.lower()
        return any(indicator in transcription_lower for indicator in story_indicators)
    
    def _categorize_confidences(self, icon_matches: List[IconMatch]) -> Dict[str, int]:
        """Categorize confidence scores into ranges."""
        if not icon_matches:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        high = sum(1 for match in icon_matches if match.confidence >= 0.7)
        medium = sum(1 for match in icon_matches if 0.4 <= match.confidence < 0.7)
        low = sum(1 for match in icon_matches if match.confidence < 0.4)
        
        return {'high': high, 'medium': medium, 'low': low}
    
    def _display_episode_result(self, evaluation: Dict[str, Any]):
        """Display results for a single episode."""
        
        if not evaluation['success']:
            print(f"❌ Failed: {evaluation['error']}")
            return
        
        meta = evaluation['episode_metadata']
        trans = evaluation['transcription_analysis']
        icons = evaluation['icon_analysis']
        subjects = evaluation['subject_analysis']
        relevance = evaluation['content_relevance']
        
        print(f"📺 Episode: {meta['title']}")
        print(f"🏠 Show: {meta['show_name']}")
        print(f"⏱️  Processing Time: {evaluation['processing_time']:.2f}s")
        print()
        
        print(f"📝 Transcription:")
        print(f"   • Length: {trans['length']} chars ({trans['word_count']} words)")
        print(f"   • Confidence: {trans['confidence']:.2f}")
        print(f"   • Story Elements: {'✅' if trans['has_story_elements'] else '❌'}")
        print()
        
        print(f"🎯 Subject Extraction:")
        print(f"   • Subject Types: {subjects['num_subject_types']} ({', '.join(subjects['subject_types'][:5])}{'...' if len(subjects['subject_types']) > 5 else ''})")
        print(f"   • Total Subjects: {subjects['total_subjects']}")
        print()
        
        print(f"🎨 Icon Matches ({icons['num_matches']} total):")
        print(f"   • Avg Confidence: {icons['avg_confidence']:.3f}")
        print(f"   • Range: {icons['min_confidence']:.3f} - {icons['max_confidence']:.3f}")
        conf_dist = icons['confidence_distribution']
        print(f"   • Distribution: High({conf_dist['high']}) Med({conf_dist['medium']}) Low({conf_dist['low']})")
        print()
        
        print(f"🎭 Content Relevance:")
        print(f"   • Story Icons: {relevance['story_themed_icons']}")
        print(f"   • Character Icons: {relevance['character_icons']}")
        print(f"   • Educational Icons: {relevance['educational_icons']}")
        print(f"   • Relevance Score: {relevance['general_relevance_score']:.2f}")
        print()
        
        print(f"🏆 Top Icon Matches:")
        for i, match in enumerate(evaluation['icon_matches'][:5], 1):
            tags_str = ', '.join(match['tags'][:3]) if match['tags'] else 'No tags'
            print(f"   {i}. {match['name']} ({match['confidence']:.3f}) - {tags_str}")
            print(f"      Reason: {match['match_reason'][:60]}{'...' if len(match['match_reason']) > 60 else ''}")
    
    async def _display_summary(self, results: List[Dict[str, Any]]):
        """Display overall evaluation summary."""
        
        print("🎭 CIRCLE ROUND EVALUATION SUMMARY")
        print("=" * 60)
        
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        print(f"📊 Overall Statistics:")
        print(f"   • Total Episodes: {len(results)}")
        print(f"   • Successful: {len(successful_results)}")
        print(f"   • Failed: {len(failed_results)}")
        print(f"   • Success Rate: {len(successful_results)/len(results)*100:.1f}%")
        
        if successful_results:
            # Processing time statistics
            processing_times = [r['processing_time'] for r in successful_results]
            avg_time = statistics.mean(processing_times)
            
            print(f"   • Avg Processing Time: {avg_time:.2f}s")
            print(f"   • Time Range: {min(processing_times):.2f}s - {max(processing_times):.2f}s")
            print()
            
            # Icon matching statistics
            icon_counts = [r['icon_analysis']['num_matches'] for r in successful_results]
            avg_icons = statistics.mean(icon_counts) if icon_counts else 0
            
            avg_confidences = []
            for r in successful_results:
                if r['icon_analysis']['num_matches'] > 0:
                    avg_confidences.append(r['icon_analysis']['avg_confidence'])
            
            overall_avg_confidence = statistics.mean(avg_confidences) if avg_confidences else 0
            
            print(f"🎨 Icon Matching Performance:")
            print(f"   • Avg Icons per Episode: {avg_icons:.1f}")
            print(f"   • Overall Avg Confidence: {overall_avg_confidence:.3f}")
            print()
            
            # Content relevance statistics
            relevance_scores = [r['content_relevance']['general_relevance_score'] for r in successful_results]
            avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0
            
            total_story_icons = sum(r['content_relevance']['story_themed_icons'] for r in successful_results)
            total_character_icons = sum(r['content_relevance']['character_icons'] for r in successful_results)
            total_educational_icons = sum(r['content_relevance']['educational_icons'] for r in successful_results)
            
            print(f"🎭 Content Analysis:")
            print(f"   • Avg Relevance Score: {avg_relevance:.3f}")
            print(f"   • Total Story Icons: {total_story_icons}")
            print(f"   • Total Character Icons: {total_character_icons}")
            print(f"   • Total Educational Icons: {total_educational_icons}")
            print()
            
            # Quality assessment
            high_quality_episodes = len([r for r in successful_results 
                                       if r['icon_analysis']['avg_confidence'] > 0.5 
                                       and r['content_relevance']['general_relevance_score'] > 0.3])
            
            print(f"🏆 Quality Assessment:")
            print(f"   • High Quality Results: {high_quality_episodes}/{len(successful_results)} ({high_quality_episodes/len(successful_results)*100:.1f}%)")
            print(f"   • Episodes with Story Elements: {sum(1 for r in successful_results if r['transcription_analysis']['has_story_elements'])}")
            print()
            
            # Best performing episode
            if successful_results:
                best_episode = max(successful_results, 
                                 key=lambda x: x['icon_analysis']['avg_confidence'] * x['content_relevance']['general_relevance_score'])
                
                print(f"🥇 Best Performing Episode:")
                print(f"   • Title: {best_episode['episode_metadata']['title']}")
                print(f"   • Index: {best_episode['episode_index']}")
                print(f"   • Avg Confidence: {best_episode['icon_analysis']['avg_confidence']:.3f}")
                print(f"   • Relevance Score: {best_episode['content_relevance']['general_relevance_score']:.3f}")
        
        if failed_results:
            print(f"❌ Failed Episodes:")
            for result in failed_results:
                print(f"   • Index {result['episode_index']}: {result['error']}")
        
        print()
        
        # Save detailed results
        await self._save_results(results)
    
    async def _save_results(self, results: List[Dict[str, Any]]):
        """Save detailed results to a JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(__file__).parent / f"circle_round_evaluation_{timestamp}.json"
        
        output_data = {
            'evaluation_info': {
                'timestamp': datetime.now().isoformat(),
                'rss_url': self.rss_url,
                'total_episodes': len(results),
                'successful_episodes': len([r for r in results if r['success']])
            },
            'episodes': results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed results saved to: {output_file}")
    
    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self.pipeline, 'cleanup'):
            await self.pipeline.cleanup()


async def main():
    """Main evaluation function."""
    print("🎭 Circle Round Audio Icon Matcher Evaluation")
    print("=" * 60)
    
    evaluator = CircleRoundEvaluator()
    
    try:
        # Check if the RSS feed is accessible
        if not evaluator.pipeline.validate_podcast_url(evaluator.rss_url):
            print(f"❌ Cannot access RSS feed: {evaluator.rss_url}")
            return
        
        print("✅ RSS feed accessible")
        print()
        
        # Run the evaluation
        results = await evaluator.evaluate_episodes(num_episodes=5)
        
        print("🎉 Evaluation complete!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await evaluator.cleanup()


if __name__ == "__main__":
    # Set random seed for reproducible episode selection
    random.seed(42)
    asyncio.run(main())
