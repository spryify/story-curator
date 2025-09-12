#!/usr/bin/env python3
"""
Circle Round Evaluation Comparison Script

This script compares two Circle Round evaluation results to demonstrate
the impact of database expansion on system performance and accuracy.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""
    timestamp: str
    total_episodes: int
    success_rate: float
    avg_processing_time: float
    avg_confidence: float
    avg_relevance: float
    story_themed_percentage: float
    character_percentage: float
    educational_percentage: float
    total_icons_matched: int
    icon_categories: Dict[str, int]
    high_quality_episodes: int


def load_evaluation_data(filepath: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load evaluation and analysis data from JSON files."""
    eval_file = filepath
    analysis_file = filepath.parent / f"icon_accuracy_analysis_{filepath.stem.split('_')[-2]}_{filepath.stem.split('_')[-1]}.json"
    
    with open(eval_file, 'r') as f:
        eval_data = json.load(f)
    
    try:
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Analysis file not found: {analysis_file}")
        analysis_data = {}
    
    return eval_data, analysis_data


def extract_metrics(eval_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> EvaluationMetrics:
    """Extract key metrics from evaluation and analysis data."""
    eval_info = eval_data.get('evaluation_info', {})
    
    # Calculate total icons matched
    total_icons = sum(
        episode.get('icon_analysis', {}).get('num_matches', 0)
        for episode in eval_data.get('episodes', [])
    )
    
    # Calculate average relevance from episodes
    relevance_scores = [
        episode.get('content_relevance', {}).get('general_relevance_score', 0)
        for episode in eval_data.get('episodes', [])
    ]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
    
    # Calculate average confidence from episodes
    confidence_scores = [
        episode.get('icon_analysis', {}).get('avg_confidence', 0)
        for episode in eval_data.get('episodes', [])
    ]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Calculate processing time
    processing_times = [
        episode.get('processing_time', 0)
        for episode in eval_data.get('episodes', [])
    ]
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Get analysis metrics if available
    overall_metrics = analysis_data.get('overall_metrics', {})
    relevance_analysis = analysis_data.get('relevance_analysis', {})
    
    return EvaluationMetrics(
        timestamp=eval_info.get('timestamp', ''),
        total_episodes=eval_info.get('total_episodes', 0),
        success_rate=overall_metrics.get('success_rate', 100.0),
        avg_processing_time=overall_metrics.get('avg_processing_time', avg_processing_time),
        avg_confidence=overall_metrics.get('avg_confidence', avg_confidence),
        avg_relevance=overall_metrics.get('avg_relevance', avg_relevance),
        story_themed_percentage=relevance_analysis.get('story_themed_percentage', 0),
        character_percentage=relevance_analysis.get('character_percentage', 0),
        educational_percentage=relevance_analysis.get('educational_percentage', 0),
        total_icons_matched=total_icons,
        icon_categories=relevance_analysis.get('icon_categories', {}),
        high_quality_episodes=overall_metrics.get('high_quality_episodes', 0)
    )


def calculate_grade(metrics: EvaluationMetrics) -> Tuple[str, str, str]:
    """Calculate overall grade based on metrics."""
    # Relevance score (most important)
    relevance_score = metrics.avg_relevance * 100
    
    # Confidence score
    confidence_score = metrics.avg_confidence * 100
    
    # Story content score (combination of story-themed and character percentages)
    story_content_score = metrics.story_themed_percentage + (metrics.character_percentage * 0.5)
    
    # Overall score calculation
    overall_score = (
        relevance_score * 0.5 +  # 50% weight on relevance
        confidence_score * 0.3 +  # 30% weight on confidence
        story_content_score * 0.2  # 20% weight on story content
    )
    
    # Grade assignment
    if overall_score >= 85:
        grade = "A"
        description = "Excellent"
        recommendation = "READY for production use"
    elif overall_score >= 70:
        grade = "B"
        description = "Good"
        recommendation = "READY for production use with children's content"
    elif overall_score >= 55:
        grade = "C"
        description = "Fair"
        recommendation = "Needs improvement before production use"
    elif overall_score >= 40:
        grade = "D"
        description = "Poor"
        recommendation = "Significant improvements needed"
    else:
        grade = "F"
        description = "Failing"
        recommendation = "Major overhaul required"
    
    return grade, description, recommendation


def print_comparison_report(before: EvaluationMetrics, after: EvaluationMetrics):
    """Print a comprehensive comparison report."""
    print("=" * 80)
    print("CIRCLE ROUND AUDIO ICON MATCHER - EVALUATION COMPARISON REPORT")
    print("=" * 80)
    print()
    
    # Timeline
    before_date = datetime.fromisoformat(before.timestamp.replace('Z', '+00:00'))
    after_date = datetime.fromisoformat(after.timestamp.replace('Z', '+00:00'))
    
    print(f"📅 EVALUATION TIMELINE")
    print(f"   Before: {before_date.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"   After:  {after_date.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"   Duration: {(after_date - before_date).days} day(s)")
    print()
    
    # Grades
    before_grade, before_desc, before_rec = calculate_grade(before)
    after_grade, after_desc, after_rec = calculate_grade(after)
    
    print(f"🎯 OVERALL GRADE IMPROVEMENT")
    print(f"   Before: {before_grade} ({before_desc})")
    print(f"   After:  {after_grade} ({after_desc})")
    
    if after_grade > before_grade:
        print(f"   ✅ IMPROVED by {ord(before_grade) - ord(after_grade)} grade level(s)")
    elif after_grade == before_grade:
        print(f"   ➡️  MAINTAINED grade level")
    else:
        print(f"   ❌ DECLINED by {ord(after_grade) - ord(before_grade)} grade level(s)")
    print()
    
    # Key Metrics Comparison
    print(f"📊 KEY METRICS COMPARISON")
    print(f"   Metric                      Before      After       Change")
    print(f"   {'-' * 55}")
    
    def format_change(before_val, after_val, is_percentage=False, decimals=1):
        change = after_val - before_val
        change_pct = (change / before_val * 100) if before_val > 0 else 0
        
        if is_percentage:
            return f"{after_val:.{decimals}f}%      {change:+.{decimals}f}% ({change_pct:+.1f}%)"
        else:
            return f"{after_val:.{decimals}f}       {change:+.{decimals}f} ({change_pct:+.1f}%)"
    
    print(f"   Success Rate (%)            {before.success_rate:.1f}%       {after.success_rate:.1f}%       {format_change(before.success_rate, after.success_rate, True)}")
    print(f"   Avg Confidence              {before.avg_confidence:.3f}     {after.avg_confidence:.3f}     {format_change(before.avg_confidence, after.avg_confidence, False, 3)}")
    print(f"   Avg Relevance               {before.avg_relevance:.3f}     {after.avg_relevance:.3f}     {format_change(before.avg_relevance, after.avg_relevance, False, 3)}")
    print(f"   Story-Themed Icons (%)      {before.story_themed_percentage:.1f}%       {after.story_themed_percentage:.1f}%       {format_change(before.story_themed_percentage, after.story_themed_percentage, True)}")
    print(f"   Character Icons (%)         {before.character_percentage:.1f}%       {after.character_percentage:.1f}%       {format_change(before.character_percentage, after.character_percentage, True)}")
    print(f"   Educational Icons (%)       {before.educational_percentage:.1f}%       {after.educational_percentage:.1f}%       {format_change(before.educational_percentage, after.educational_percentage, True)}")
    print(f"   Total Icons Matched         {before.total_icons_matched}           {after.total_icons_matched}           {after.total_icons_matched - before.total_icons_matched:+d} ({((after.total_icons_matched - before.total_icons_matched) / before.total_icons_matched * 100):+.1f}%)")
    print(f"   High Quality Episodes       {before.high_quality_episodes}           {after.high_quality_episodes}           {after.high_quality_episodes - before.high_quality_episodes:+d}")
    print()
    
    # Processing Performance
    print(f"⚡ PROCESSING PERFORMANCE")
    time_change = after.avg_processing_time - before.avg_processing_time
    time_change_pct = (time_change / before.avg_processing_time * 100) if before.avg_processing_time > 0 else 0
    print(f"   Average Processing Time: {before.avg_processing_time:.2f}s → {after.avg_processing_time:.2f}s ({time_change:+.2f}s, {time_change_pct:+.1f}%)")
    
    if time_change > 0:
        print(f"   ⚠️  Processing time increased - likely due to larger database")
    else:
        print(f"   ✅ Processing time improved")
    print()
    
    # Icon Categories Analysis
    print(f"🏷️  ICON CATEGORY DISTRIBUTION")
    all_categories = set(before.icon_categories.keys()) | set(after.icon_categories.keys())
    
    print(f"   Category        Before    After     Change")
    print(f"   {'-' * 40}")
    
    for category in sorted(all_categories):
        before_count = before.icon_categories.get(category, 0)
        after_count = after.icon_categories.get(category, 0)
        change = after_count - before_count
        
        print(f"   {category:<15} {before_count:>6}    {after_count:>5}     {change:+5d}")
    print()
    
    # Recommendations
    print(f"📋 SYSTEM STATUS")
    print(f"   Before: {before_rec}")
    print(f"   After:  {after_rec}")
    print()
    
    # Key Insights
    print(f"🔍 KEY INSIGHTS")
    
    relevance_improvement = (after.avg_relevance - before.avg_relevance) / before.avg_relevance * 100
    story_improvement = after.story_themed_percentage - before.story_themed_percentage
    
    if relevance_improvement > 0:
        print(f"   ✅ Content relevance improved by {relevance_improvement:.1f}%")
    else:
        print(f"   ❌ Content relevance declined by {abs(relevance_improvement):.1f}%")
    
    if story_improvement > 0:
        print(f"   ✅ Story-themed icon coverage increased by {story_improvement:.1f} percentage points")
    else:
        print(f"   ❌ Story-themed icon coverage decreased by {abs(story_improvement):.1f} percentage points")
    
    if after.total_icons_matched > before.total_icons_matched:
        match_improvement = ((after.total_icons_matched - before.total_icons_matched) / before.total_icons_matched) * 100
        print(f"   ✅ Total icon matches increased by {match_improvement:.1f}%")
    
    if after.high_quality_episodes > before.high_quality_episodes:
        quality_improvement = after.high_quality_episodes - before.high_quality_episodes
        print(f"   ✅ High-quality episodes increased by {quality_improvement}")
    
    print()
    print("=" * 80)


def main():
    """Main function to run the comparison."""
    if len(sys.argv) != 3:
        print("Usage: python compare_evaluations.py <before_file> <after_file>")
        print("Example: python compare_evaluations.py circle_round_evaluation_20250903_165332.json circle_round_evaluation_20250904_114541.json")
        sys.exit(1)
    
    before_file = Path(sys.argv[1])
    after_file = Path(sys.argv[2])
    
    if not before_file.exists():
        print(f"Error: Before file not found: {before_file}")
        sys.exit(1)
    
    if not after_file.exists():
        print(f"Error: After file not found: {after_file}")
        sys.exit(1)
    
    # Load data
    before_eval, before_analysis = load_evaluation_data(before_file)
    after_eval, after_analysis = load_evaluation_data(after_file)
    
    # Extract metrics
    before_metrics = extract_metrics(before_eval, before_analysis)
    after_metrics = extract_metrics(after_eval, after_analysis)
    
    # Print comparison report
    print_comparison_report(before_metrics, after_metrics)


if __name__ == "__main__":
    main()
