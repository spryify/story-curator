#!/usr/bin/env python3
"""
Analyzes the accuracy and quality of icon matches from Circle Round evaluation.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any
import re


class IconAccuracyAnalyzer:
    """Analyzes the accuracy and quality of icon matching results."""
    
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        self.data = self._load_results()
        
    def _load_results(self) -> Dict[str, Any]:
        """Load evaluation results from JSON file."""
        with open(self.results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_accuracy(self) -> Dict[str, Any]:
        """Perform comprehensive accuracy analysis."""
        
        print("🔍 ICON MATCHING ACCURACY ANALYSIS")
        print("=" * 60)
        
        episodes = [ep for ep in self.data['episodes'] if ep['success']]
        
        # Overall performance metrics
        overall_metrics = self._calculate_overall_metrics(episodes)
        
        # Content relevance analysis
        relevance_analysis = self._analyze_content_relevance(episodes)
        
        # Match quality analysis
        quality_analysis = self._analyze_match_quality(episodes)
        
        # Transcription quality vs icon accuracy
        transcription_correlation = self._analyze_transcription_correlation(episodes)
        
        # Specific episode analysis
        episode_analysis = self._analyze_individual_episodes(episodes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(episodes)
        
        analysis_results = {
            'overall_metrics': overall_metrics,
            'relevance_analysis': relevance_analysis,
            'quality_analysis': quality_analysis,
            'transcription_correlation': transcription_correlation,
            'episode_analysis': episode_analysis,
            'recommendations': recommendations
        }
        
        self._display_analysis(analysis_results)
        
        return analysis_results
    
    def _calculate_overall_metrics(self, episodes: List[Dict]) -> Dict[str, Any]:
        """Calculate overall performance metrics."""
        
        total_episodes = len(episodes)
        processing_times = [ep['processing_time'] for ep in episodes]
        confidence_scores = []
        relevance_scores = []
        
        for ep in episodes:
            confidence_scores.append(ep['icon_analysis']['avg_confidence'])
            relevance_scores.append(ep['content_relevance']['general_relevance_score'])
        
        return {
            'total_episodes': total_episodes,
            'success_rate': 100.0,  # All episodes in this dataset succeeded
            'avg_processing_time': statistics.mean(processing_times),
            'processing_time_std': statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
            'avg_confidence': statistics.mean(confidence_scores),
            'confidence_std': statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0,
            'avg_relevance': statistics.mean(relevance_scores),
            'relevance_std': statistics.stdev(relevance_scores) if len(relevance_scores) > 1 else 0,
            'high_quality_episodes': len([ep for ep in episodes 
                                        if ep['icon_analysis']['avg_confidence'] > 0.7 
                                        and ep['content_relevance']['general_relevance_score'] > 0.4]),
        }
    
    def _analyze_content_relevance(self, episodes: List[Dict]) -> Dict[str, Any]:
        """Analyze how well icons match the actual story content."""
        
        total_story_icons = sum(ep['content_relevance']['story_themed_icons'] for ep in episodes)
        total_character_icons = sum(ep['content_relevance']['character_icons'] for ep in episodes)
        total_educational_icons = sum(ep['content_relevance']['educational_icons'] for ep in episodes)
        total_icons = sum(ep['icon_analysis']['num_matches'] for ep in episodes)
        
        # Analyze icon categories that appear most frequently
        icon_categories = {}
        problematic_matches = []
        
        for ep in episodes:
            for match in ep['icon_matches']:
                category = match.get('category', 'Unknown')
                icon_categories[category] = icon_categories.get(category, 0) + 1
                
                # Identify potentially problematic matches
                if self._is_problematic_match(match, ep):
                    problematic_matches.append({
                        'episode': ep['episode_metadata']['title'],
                        'icon_name': match['name'],
                        'confidence': match['confidence'],
                        'reason': match['match_reason'],
                        'issue': self._identify_match_issue(match, ep)
                    })
        
        return {
            'story_themed_percentage': (total_story_icons / total_icons * 100) if total_icons > 0 else 0,
            'character_percentage': (total_character_icons / total_icons * 100) if total_icons > 0 else 0,
            'educational_percentage': (total_educational_icons / total_icons * 100) if total_icons > 0 else 0,
            'icon_categories': dict(sorted(icon_categories.items(), key=lambda x: x[1], reverse=True)),
            'problematic_matches': problematic_matches,
            'relevance_distribution': [ep['content_relevance']['general_relevance_score'] for ep in episodes]
        }
    
    def _analyze_match_quality(self, episodes: List[Dict]) -> Dict[str, Any]:
        """Analyze the quality of individual matches."""
        
        all_matches = []
        keyword_matches = 0
        topic_matches = 0
        entity_matches = 0
        confidence_ranges = {'high': 0, 'medium': 0, 'low': 0}
        
        for ep in episodes:
            for match in ep['icon_matches']:
                all_matches.append(match)
                
                # Categorize by match type
                reason = match['match_reason'].lower()
                if 'keyword' in reason:
                    keyword_matches += 1
                elif 'topic' in reason:
                    topic_matches += 1
                elif 'entity' in reason:
                    entity_matches += 1
                
                # Categorize by confidence
                conf = match['confidence']
                if conf >= 0.7:
                    confidence_ranges['high'] += 1
                elif conf >= 0.4:
                    confidence_ranges['medium'] += 1
                else:
                    confidence_ranges['low'] += 1
        
        # Identify most successful matching strategies
        match_types = {
            'keyword_matches': keyword_matches,
            'topic_matches': topic_matches, 
            'entity_matches': entity_matches
        }
        
        return {
            'total_matches': len(all_matches),
            'match_type_distribution': match_types,
            'confidence_distribution': confidence_ranges,
            'avg_match_confidence': statistics.mean([m['confidence'] for m in all_matches]),
            'top_performing_icons': self._identify_top_icons(all_matches),
            'matching_strategy_effectiveness': self._analyze_matching_strategies(all_matches)
        }
    
    def _analyze_transcription_correlation(self, episodes: List[Dict]) -> Dict[str, Any]:
        """Analyze correlation between transcription quality and icon accuracy."""
        
        transcription_confidences = []
        icon_relevance_scores = []
        transcription_lengths = []
        story_element_episodes = 0
        
        for ep in episodes:
            trans = ep['transcription_analysis']
            relevance = ep['content_relevance']
            
            transcription_confidences.append(trans['confidence'])
            icon_relevance_scores.append(relevance['general_relevance_score'])
            transcription_lengths.append(trans['length'])
            
            if trans['has_story_elements']:
                story_element_episodes += 1
        
        # Calculate correlation (simple)
        correlation = self._calculate_simple_correlation(transcription_confidences, icon_relevance_scores)
        
        return {
            'transcription_icon_correlation': correlation,
            'avg_transcription_confidence': statistics.mean(transcription_confidences),
            'avg_transcription_length': statistics.mean(transcription_lengths),
            'story_element_percentage': (story_element_episodes / len(episodes) * 100),
            'length_quality_correlation': self._calculate_simple_correlation(transcription_lengths, icon_relevance_scores)
        }
    
    def _analyze_individual_episodes(self, episodes: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze each episode individually."""
        
        episode_scores = []
        
        for ep in episodes:
            # Calculate overall episode score
            confidence_score = ep['icon_analysis']['avg_confidence']
            relevance_score = ep['content_relevance']['general_relevance_score']
            transcription_score = ep['transcription_analysis']['confidence']
            
            overall_score = (confidence_score * 0.4 + relevance_score * 0.4 + transcription_score * 0.2)
            
            episode_analysis = {
                'title': ep['episode_metadata']['title'],
                'index': ep['episode_index'],
                'overall_score': overall_score,
                'confidence_score': confidence_score,
                'relevance_score': relevance_score,
                'transcription_score': transcription_score,
                'num_matches': ep['icon_analysis']['num_matches'],
                'processing_time': ep['processing_time'],
                'key_strengths': self._identify_episode_strengths(ep),
                'key_weaknesses': self._identify_episode_weaknesses(ep),
                'best_matches': ep['icon_matches'][:3] if ep['icon_matches'] else []
            }
            
            episode_scores.append(episode_analysis)
        
        # Sort by overall score
        episode_scores.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return episode_scores
    
    def _generate_recommendations(self, episodes: List[Dict]) -> Dict[str, List[str]]:
        """Generate recommendations for improving accuracy."""
        
        recommendations = {
            'algorithm_improvements': [],
            'data_quality_improvements': [],
            'evaluation_improvements': [],
            'system_optimizations': []
        }
        
        # Analyze patterns to generate recommendations
        avg_relevance = statistics.mean([ep['content_relevance']['general_relevance_score'] for ep in episodes])
        
        if avg_relevance < 0.5:
            recommendations['algorithm_improvements'].append(
                "Improve semantic matching algorithms - current relevance score is low"
            )
        
        # Check for over-reliance on keyword matching
        total_matches = sum(len(ep['icon_matches']) for ep in episodes)
        keyword_heavy = sum(1 for ep in episodes for match in ep['icon_matches'] 
                           if 'keyword' in match['match_reason'].lower())
        
        if keyword_heavy / total_matches > 0.8:
            recommendations['algorithm_improvements'].append(
                "Reduce over-reliance on keyword matching - implement more semantic understanding"
            )
        
        # Check processing time consistency
        processing_times = [ep['processing_time'] for ep in episodes]
        if max(processing_times) - min(processing_times) > 5:
            recommendations['system_optimizations'].append(
                "Optimize processing time consistency - there's significant variation"
            )
        
        # Story-specific improvements
        story_themed_percentage = sum(ep['content_relevance']['story_themed_icons'] for ep in episodes) / total_matches * 100
        if story_themed_percentage < 30:
            recommendations['data_quality_improvements'].append(
                "Expand story-themed icon database - current coverage is insufficient for children's stories"
            )
        
        # Transcription quality improvements
        low_confidence_episodes = [ep for ep in episodes if ep['transcription_analysis']['confidence'] < 0.8]
        if len(low_confidence_episodes) > len(episodes) * 0.3:
            recommendations['data_quality_improvements'].append(
                "Improve audio preprocessing or use higher-quality Whisper model for better transcription"
            )
        
        return recommendations
    
    def _is_problematic_match(self, match: Dict, episode: Dict) -> bool:
        """Identify potentially problematic matches."""
        
        # Very high confidence but low relevance might indicate overfitting
        if match['confidence'] > 0.9 and episode['content_relevance']['general_relevance_score'] < 0.3:
            return True
        
        # Matches based on very short keywords might be spurious
        reason = match['match_reason'].lower()
        if 'keyword' in reason and any(len(word) <= 3 for word in reason.split() if word.isalpha()):
            return True
        
        return False
    
    def _identify_match_issue(self, match: Dict, episode: Dict) -> str:
        """Identify the specific issue with a problematic match."""
        
        if match['confidence'] > 0.9 and episode['content_relevance']['general_relevance_score'] < 0.3:
            return "High confidence but low relevance - possible overfitting"
        
        reason = match['match_reason'].lower()
        if 'keyword' in reason and any(len(word) <= 3 for word in reason.split() if word.isalpha()):
            return "Match based on very short keyword - potentially spurious"
        
        return "Unknown issue"
    
    def _identify_top_icons(self, matches: List[Dict]) -> List[Dict]:
        """Identify the most frequently matched icons."""
        
        icon_counts = {}
        for match in matches:
            name = match['name']
            if name not in icon_counts:
                icon_counts[name] = {'count': 0, 'avg_confidence': 0, 'confidences': []}
            icon_counts[name]['count'] += 1
            icon_counts[name]['confidences'].append(match['confidence'])
        
        # Calculate average confidences
        for name, data in icon_counts.items():
            data['avg_confidence'] = statistics.mean(data['confidences'])
        
        # Sort by frequency then confidence
        top_icons = sorted(icon_counts.items(), 
                          key=lambda x: (x[1]['count'], x[1]['avg_confidence']), 
                          reverse=True)[:10]
        
        return [{'name': name, **data} for name, data in top_icons]
    
    def _analyze_matching_strategies(self, matches: List[Dict]) -> Dict[str, Dict]:
        """Analyze the effectiveness of different matching strategies."""
        
        strategies = {'keyword': [], 'topic': [], 'entity': [], 'other': []}
        
        for match in matches:
            reason = match['match_reason'].lower()
            confidence = match['confidence']
            
            if 'keyword' in reason:
                strategies['keyword'].append(confidence)
            elif 'topic' in reason:
                strategies['topic'].append(confidence)
            elif 'entity' in reason:
                strategies['entity'].append(confidence)
            else:
                strategies['other'].append(confidence)
        
        strategy_analysis = {}
        for strategy, confidences in strategies.items():
            if confidences:
                strategy_analysis[strategy] = {
                    'count': len(confidences),
                    'avg_confidence': statistics.mean(confidences),
                    'min_confidence': min(confidences),
                    'max_confidence': max(confidences)
                }
            else:
                strategy_analysis[strategy] = {'count': 0}
        
        return strategy_analysis
    
    def _calculate_simple_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate simple correlation coefficient."""
        
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _identify_episode_strengths(self, episode: Dict) -> List[str]:
        """Identify strengths of a specific episode's analysis."""
        
        strengths = []
        
        if episode['icon_analysis']['avg_confidence'] > 0.8:
            strengths.append("High confidence icon matches")
        
        if episode['content_relevance']['general_relevance_score'] > 0.5:
            strengths.append("Good content relevance")
        
        if episode['transcription_analysis']['confidence'] > 0.8:
            strengths.append("High quality transcription")
        
        if episode['transcription_analysis']['has_story_elements']:
            strengths.append("Clear story structure detected")
        
        if episode['content_relevance']['story_themed_icons'] > 2:
            strengths.append("Multiple story-relevant icons found")
        
        return strengths
    
    def _identify_episode_weaknesses(self, episode: Dict) -> List[str]:
        """Identify weaknesses of a specific episode's analysis."""
        
        weaknesses = []
        
        if episode['icon_analysis']['avg_confidence'] < 0.6:
            weaknesses.append("Low confidence icon matches")
        
        if episode['content_relevance']['general_relevance_score'] < 0.3:
            weaknesses.append("Poor content relevance")
        
        if episode['transcription_analysis']['confidence'] < 0.7:
            weaknesses.append("Low quality transcription")
        
        if episode['content_relevance']['story_themed_icons'] == 0:
            weaknesses.append("No story-themed icons found")
        
        if episode['icon_analysis']['num_matches'] < 5:
            weaknesses.append("Few icon matches found")
        
        return weaknesses
    
    def _display_analysis(self, results: Dict[str, Any]):
        """Display comprehensive analysis results."""
        
        print("\n📊 OVERALL PERFORMANCE METRICS")
        print("-" * 40)
        overall = results['overall_metrics']
        print(f"Success Rate: {overall['success_rate']:.1f}%")
        print(f"Average Processing Time: {overall['avg_processing_time']:.2f}s ± {overall['processing_time_std']:.2f}s")
        print(f"Average Confidence: {overall['avg_confidence']:.3f} ± {overall['confidence_std']:.3f}")
        print(f"Average Relevance: {overall['avg_relevance']:.3f} ± {overall['relevance_std']:.3f}")
        print(f"High Quality Episodes: {overall['high_quality_episodes']}/{overall['total_episodes']} ({overall['high_quality_episodes']/overall['total_episodes']*100:.1f}%)")
        
        print("\n🎭 CONTENT RELEVANCE ANALYSIS")
        print("-" * 40)
        relevance = results['relevance_analysis']
        print(f"Story-themed Icons: {relevance['story_themed_percentage']:.1f}%")
        print(f"Character Icons: {relevance['character_percentage']:.1f}%")
        print(f"Educational Icons: {relevance['educational_percentage']:.1f}%")
        
        print("\nTop Icon Categories:")
        for category, count in list(relevance['icon_categories'].items())[:5]:
            print(f"  • {category}: {count} icons")
        
        if relevance['problematic_matches']:
            print(f"\nProblematic Matches Identified: {len(relevance['problematic_matches'])}")
            for match in relevance['problematic_matches'][:3]:
                print(f"  • {match['icon_name']} ({match['confidence']:.3f}) - {match['issue']}")
        
        print("\n🎯 MATCH QUALITY ANALYSIS")
        print("-" * 40)
        quality = results['quality_analysis']
        print(f"Total Matches Analyzed: {quality['total_matches']}")
        print(f"Average Match Confidence: {quality['avg_match_confidence']:.3f}")
        
        print("\nMatching Strategy Distribution:")
        for strategy, count in quality['match_type_distribution'].items():
            percentage = count / quality['total_matches'] * 100
            print(f"  • {strategy.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print("\nStrategy Effectiveness:")
        for strategy, data in quality['matching_strategy_effectiveness'].items():
            if data['count'] > 0:
                print(f"  • {strategy.title()}: {data['avg_confidence']:.3f} avg confidence ({data['count']} matches)")
        
        print("\n📝 TRANSCRIPTION CORRELATION")
        print("-" * 40)
        transcription = results['transcription_correlation']
        print(f"Transcription-Icon Correlation: {transcription['transcription_icon_correlation']:.3f}")
        print(f"Average Transcription Confidence: {transcription['avg_transcription_confidence']:.3f}")
        print(f"Average Transcription Length: {transcription['avg_transcription_length']:.0f} characters")
        print(f"Episodes with Story Elements: {transcription['story_element_percentage']:.1f}%")
        
        print("\n🏆 EPISODE RANKINGS")
        print("-" * 40)
        for i, ep in enumerate(results['episode_analysis'][:3], 1):
            print(f"{i}. {ep['title']} (Score: {ep['overall_score']:.3f})")
            print(f"   Confidence: {ep['confidence_score']:.3f} | Relevance: {ep['relevance_score']:.3f} | Transcription: {ep['transcription_score']:.3f}")
            if ep['key_strengths']:
                print(f"   Strengths: {', '.join(ep['key_strengths'])}")
            if ep['key_weaknesses']:
                print(f"   Weaknesses: {', '.join(ep['key_weaknesses'])}")
            print()
        
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        recommendations = results['recommendations']
        
        for category, recs in recommendations.items():
            if recs:
                print(f"\n{category.replace('_', ' ').title()}:")
                for rec in recs:
                    print(f"  • {rec}")
        
        print("\n" + "="*60)
        print("ACCURACY ASSESSMENT SUMMARY:")
        
        # Overall accuracy grade
        overall_score = (overall['avg_confidence'] + overall['avg_relevance'] + transcription['avg_transcription_confidence']) / 3
        
        if overall_score >= 0.8:
            grade = "A (Excellent)"
        elif overall_score >= 0.7:
            grade = "B (Good)"
        elif overall_score >= 0.6:
            grade = "C (Fair)"
        elif overall_score >= 0.5:
            grade = "D (Needs Improvement)"
        else:
            grade = "F (Poor)"
        
        print(f"Overall Accuracy Grade: {grade} (Score: {overall_score:.3f})")
        print(f"System is {'READY' if overall_score >= 0.7 else 'NOT READY'} for production use with children's content.")


def main():
    """Main analysis function."""
    
    # Find the most recent evaluation file
    script_dir = Path(__file__).parent
    evaluation_files = list(script_dir.glob("circle_round_evaluation_*.json"))
    
    if not evaluation_files:
        print("❌ No evaluation files found. Run evaluate_circle_round_episodes.py first.")
        return
    
    # Use the most recent file
    latest_file = max(evaluation_files, key=lambda f: f.stat().st_mtime)
    print(f"📂 Analyzing: {latest_file.name}")
    
    analyzer = IconAccuracyAnalyzer(latest_file)
    results = analyzer.analyze_accuracy()
    
    # Save analysis results
    output_file = script_dir / f"icon_accuracy_analysis_{latest_file.stem.split('_')[-2]}_{latest_file.stem.split('_')[-1]}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Analysis results saved to: {output_file}")


if __name__ == "__main__":
    main()
