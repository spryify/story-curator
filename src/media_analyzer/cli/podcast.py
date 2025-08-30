"""Command line interface for podcast analysis operations."""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Literal, Dict, Any

import click
from rich.console import Console
from rich import print as rprint

from media_analyzer.processors.podcast.analyzer import PodcastAnalyzer
from media_analyzer.models.podcast import AnalysisOptions
from media_analyzer.core.exceptions import ValidationError

console = Console()

def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]Error:[/red] {message}")

def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]{message}[/green]")

def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[yellow]Warning:[/yellow] {message}")

@click.group()
def cli():
    """Podcast analysis tools - Analyze podcast episodes from streaming platforms."""
    pass

@cli.command()
@click.argument('url', type=str)
@click.option('--language', '-l', default='en', help='Language of the podcast (default: en)')
@click.option('--max-duration', '-d', default=180, type=int, help='Maximum episode duration in minutes (default: 180)')
@click.option('--segment-length', '-s', default=300, type=int, help='Audio processing segment length in seconds (default: 300)')
@click.option('--confidence-threshold', '-c', default=0.5, type=float, help='Minimum confidence for subject extraction (default: 0.5)')
@click.option('--skip-subjects', is_flag=True, help='Skip subject extraction (faster processing)')
@click.option('--output', '-o', type=click.Path(), help='Output file for the analysis results')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format (text or json)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed processing information')
def analyze(url: str, language: str, max_duration: int, segment_length: int, confidence_threshold: float, 
           skip_subjects: bool, output: Optional[str], format: Literal['text', 'json'], verbose: bool):
    """
    Analyze a podcast episode from a streaming platform URL.
    
    Supported platforms:
  - RSS feeds (*.xml, *.rss, or URLs containing 'rss' or 'feed')
  - Direct audio URLs
  
  Examples:
      # Analyze from RSS feed
      media-analyzer podcast analyze "https://example.com/podcast.rss" --verbose
      
      # Quick analysis without subject extraction  
      media-analyzer podcast analyze "https://feeds.megaphone.fm/example" --skip-subjects
      
      # Save results to file
      media-analyzer podcast analyze "https://example.com/feed.xml" --output results.json --format json
    """
    try:
        # Validate inputs
        if confidence_threshold < 0 or confidence_threshold > 1:
            print_error("Confidence threshold must be between 0 and 1")
            sys.exit(1)
        
        if max_duration <= 0:
            print_error("Maximum duration must be positive")
            sys.exit(1)
        
        if segment_length <= 0:
            print_error("Segment length must be positive") 
            sys.exit(1)
        
        # Create analysis options
        options = AnalysisOptions(
            language=language,
            transcription_service="whisper",
            subject_extraction=not skip_subjects,
            icon_matching=False,  # Not implemented yet
            max_duration_minutes=max_duration,
            segment_length_seconds=segment_length,
            confidence_threshold=confidence_threshold
        )
        
        # Run async analysis
        result = asyncio.run(_analyze_episode(url, options, verbose))
        
        if not result.success:
            print_error(f"Analysis failed: {result.error_message}")
            sys.exit(1)
        
        # Prepare output data
        if format == 'json':
            output_data: Dict[str, Any] = {
                "episode": {
                    "title": result.episode.title,
                    "show_name": result.episode.show_name,
                    "platform": result.episode.platform,
                    "duration_seconds": result.episode.duration_seconds,
                    "publication_date": result.episode.publication_date.isoformat() if result.episode.publication_date else None,
                    "description": result.episode.description,
                    "url": result.episode.url
                },
                "transcription": {
                    "text": result.transcription.text,
                    "language": result.transcription.language,
                    "confidence": result.transcription.confidence,
                    "duration": result.transcription.metadata.get("duration", 0)
                },
                "subjects": [
                    {
                        "name": subject.name,
                        "type": subject.subject_type.value,
                        "confidence": subject.confidence
                    }
                    for subject in result.subjects
                ],
                "processing_metadata": result.processing_metadata
            }
        else:  # text format
            duration_mins = result.episode.duration_seconds // 60
            duration_secs = result.episode.duration_seconds % 60
            
            output_text = [
                "🎙️ [bold]Podcast Analysis Result[/bold]",
                "",
                "[bold blue]Episode Information:[/bold blue]",
                f"• Title: {result.episode.title}",
                f"• Show: {result.episode.show_name}",
                f"• Platform: {result.episode.platform.upper()}",
                f"• Duration: {duration_mins:02d}:{duration_secs:02d}",
                f"• Published: {result.episode.publication_date.strftime('%Y-%m-%d') if result.episode.publication_date else 'Unknown'}",
                "",
                "[bold green]Transcription:[/bold green]",
                result.transcription.text[:500] + ("..." if len(result.transcription.text) > 500 else ""),
                "",
                f"[bold yellow]Transcription Quality:[/bold yellow]",
                f"• Language: {result.transcription.language}",
                f"• Confidence: {result.transcription.confidence:.2%}",
                f"• Processing Time: {result.transcription.metadata.get('duration', 0):.1f}s",
            ]
            
            if result.subjects:
                output_text.extend([
                    "",
                    f"[bold magenta]Identified Subjects ({len(result.subjects)}):[/bold magenta]"
                ])
                for subject in sorted(result.subjects, key=lambda s: s.confidence, reverse=True)[:10]:
                    output_text.append(f"• {subject.name} ({subject.subject_type.value}, {subject.confidence:.2%})")
                
                if len(result.subjects) > 10:
                    output_text.append(f"  ... and {len(result.subjects) - 10} more")
            
            # Add processing metadata if verbose
            if verbose:
                output_text.extend([
                    "",
                    "[bold dim]Processing Details:[/bold dim]",
                    f"• Connector: {result.processing_metadata.get('connector_used', 'unknown')}",
                    f"• Transcription: {result.processing_metadata.get('transcription_service', 'unknown')}",
                    f"• Subject Extraction: {'enabled' if result.processing_metadata.get('subject_extraction_enabled') else 'disabled'}"
                ])
        
        # Output handling
        if output:
            # Save to file
            output_path = Path(output)
            with output_path.open('w', encoding='utf-8') as f:
                if format == 'json':
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                else:
                    # Write plain text version
                    f.write("Podcast Analysis Result\n\n")
                    f.write(f"Episode: {result.episode.title}\n")
                    f.write(f"Show: {result.episode.show_name}\n")
                    f.write(f"Platform: {result.episode.platform}\n")
                    f.write(f"Duration: {duration_mins:02d}:{duration_secs:02d}\n\n")
                    f.write("Transcription:\n")
                    f.write(f"{result.transcription.text}\n\n")
                    f.write(f"Language: {result.transcription.language}\n")
                    f.write(f"Confidence: {result.transcription.confidence:.2%}\n\n")
                    if result.subjects:
                        f.write(f"Subjects ({len(result.subjects)}):\n")
                        for subject in result.subjects:
                            f.write(f"- {subject.name} ({subject.subject_type.value}, {subject.confidence:.2%})\n")
            
            print_success(f"Results saved to: {output}")
        else:
            # Print to console
            if format == 'json':
                console.print_json(data=output_data)
            else:
                # Print with rich formatting
                console.print("\n".join(output_text))
        
        print_success("\n✨ Analysis complete!")
        
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print_warning("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Processing failed: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)

@cli.command()
@click.argument('url', type=str)
def metadata(url: str):
    """
    Extract metadata from a podcast episode without full analysis.
    
    This is a quick way to get episode information without transcription.
    """
    try:
        result = asyncio.run(_get_metadata(url))
        
        duration_mins = result.duration_seconds // 60
        duration_secs = result.duration_seconds % 60
        
        console.print("\n🎙️ [bold]Podcast Episode Metadata[/bold]")
        console.print(f"[bold blue]Title:[/bold blue] {result.title}")
        console.print(f"[bold blue]Show:[/bold blue] {result.show_name}")
        console.print(f"[bold blue]Platform:[/bold blue] {result.platform.upper()}")
        console.print(f"[bold blue]Duration:[/bold blue] {duration_mins:02d}:{duration_secs:02d}")
        if result.publication_date:
            console.print(f"[bold blue]Published:[/bold blue] {result.publication_date.strftime('%Y-%m-%d %H:%M')}")
        if result.author:
            console.print(f"[bold blue]Author:[/bold blue] {result.author}")
        console.print(f"[bold blue]URL:[/bold blue] {result.url}")
        
        if result.description:
            console.print(f"\n[bold green]Description:[/bold green]")
            console.print(result.description[:300] + ("..." if len(result.description) > 300 else ""))
        
        print_success("\n✨ Metadata extraction complete!")
        
    except Exception as e:
        print_error(f"Failed to extract metadata: {e}")
        sys.exit(1)

async def _analyze_episode(url: str, options: AnalysisOptions, verbose: bool):
    """Run podcast episode analysis."""
    analyzer = PodcastAnalyzer()
    
    try:
        with console.status("[bold blue]Initializing podcast analysis...") as status:
            if verbose:
                status.update("[bold blue]Extracting episode metadata...")
            
            result = await analyzer.analyze_episode(url, options)
            
            if verbose:
                status.update("[bold blue]Analysis complete!")
        
        return result
    
    finally:
        await analyzer.cleanup()

async def _get_metadata(url: str):
    """Extract metadata only."""
    analyzer = PodcastAnalyzer()
    
    try:
        return await analyzer.get_episode_metadata(url)
    finally:
        await analyzer.cleanup()

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main()
