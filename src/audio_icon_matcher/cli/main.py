"""CLI commands for audio-to-icon pipeline."""

import click
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.pipeline import AudioIconPipeline
from ..core.exceptions import AudioIconValidationError, AudioIconProcessingError


@click.group(name="audio-icon-matcher")
def audio_icon_matcher_commands():
    """Audio-icon matcher commands."""
    pass


@audio_icon_matcher_commands.command("find-icons")
@click.argument("audio_source", type=str)
@click.option("--max-icons", type=int, default=10, help="Maximum number of icons to return")
@click.option("--confidence-threshold", type=float, default=0.3, help="Minimum confidence threshold")
@click.option("--output-format", type=click.Choice(["json", "table", "summary"]), default="table", help="Output format")
@click.option("--output-file", type=click.Path(path_type=Path), help="Output file (if not specified, prints to stdout)")
def find_matching_icons(audio_source, max_icons, confidence_threshold, output_format, output_file):
    """Find matching icons for audio source (local file or podcast URL).
    
    AUDIO_SOURCE can be:
    - Path to local audio file (WAV, MP3, M4A)
    - Podcast episode URL (RSS feed or direct audio link)
    """
    try:
        pipeline = AudioIconPipeline()
        
        # Determine source type and validate
        if audio_source.startswith(('http://', 'https://')):
            # Podcast URL validation
            if not pipeline.validate_podcast_url(audio_source):
                raise AudioIconValidationError(f"Invalid or unsupported podcast URL: {audio_source}")
            click.echo(f"Finding icons for podcast episode: {audio_source}")
        else:
            # Local file validation
            audio_path = Path(audio_source)
            if not audio_path.exists():
                raise AudioIconValidationError(f"Audio file not found: {audio_source}")
            if not pipeline.validate_audio_file(audio_source):
                raise AudioIconValidationError(f"Unsupported audio format: {audio_source}")
            click.echo(f"Finding icons for audio file: {audio_source}")
        
        # Process the audio source using unified pipeline
        result = pipeline.process(
            audio_source,
            max_icons=max_icons,
            confidence_threshold=confidence_threshold
        )
        
        # Format and output results
        _output_results(result, output_format, output_file)
            
    except AudioIconValidationError as e:
        click.echo(f"❌ Validation Error: {e}", err=True)
        sys.exit(1)
    except AudioIconProcessingError as e:
        click.echo(f"❌ Processing Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


def _output_results(result, output_format: str, output_file: Optional[Path] = None):
    """Handle result formatting and output to file or stdout.
    
    Args:
        result: AudioIconResult to format and output
        output_format: Format type ("json", "table", "summary")
        output_file: Optional file path to write to
    """
    # Format output based on type
    if output_format == "json":
        output_data = _format_json_output(result)
    elif output_format == "table":
        output_data = _format_table_output(result)
    elif output_format == "summary":
        output_data = _format_summary_output(result)
    else:
        output_data = _format_table_output(result)  # Default fallback
    
    # Output results
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_data)
        click.echo(f"✅ Results written to {output_file}")
    else:
        click.echo(output_data)


@audio_icon_matcher_commands.command("validate")
@click.argument("audio_source", type=str)
def validate_audio_source(audio_source):
    """Validate audio source (local file or podcast URL).
    
    AUDIO_SOURCE can be:
    - Path to local audio file (WAV, MP3, M4A)
    - Podcast episode URL (RSS feed or direct audio link)
    """
    try:
        pipeline = AudioIconPipeline()
        
        if audio_source.startswith(('http://', 'https://')):
            # Validate podcast URL
            is_valid = pipeline.validate_podcast_url(audio_source)
            source_type = "podcast URL"
        else:
            # Validate local file
            is_valid = pipeline.validate_audio_file(audio_source)
            source_type = "audio file"
        
        if is_valid:
            click.echo(f"✅ Valid {source_type}: {audio_source}")
        else:
            click.echo(f"❌ Invalid {source_type}: {audio_source}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Validation error: {e}", err=True)
        sys.exit(1)


@audio_icon_matcher_commands.command("formats")
def list_supported_formats():
    """List supported audio formats and sources."""
    try:
        pipeline = AudioIconPipeline()
        formats = pipeline.get_supported_formats()
        
        click.echo("SUPPORTED AUDIO FORMATS")
        click.echo("=" * 40)
        click.echo("Local audio files:")
        for fmt in sorted(formats):
            click.echo(f"  • .{fmt}")
        
        click.echo("\nSUPPORTED PODCAST SOURCES")
        click.echo("=" * 40)
        click.echo("  • RSS/XML podcast feeds")
        click.echo("  • Direct audio episode URLs")
        click.echo("  • Most major podcast platforms")
            
    except Exception as e:
        click.echo(f"❌ Error getting formats: {e}", err=True)
        sys.exit(1)


def _format_json_output(result) -> str:
    """Format result as JSON."""
    # Convert to JSON-serializable format
    output_data = {
        "success": result.success,
        "transcription": result.transcription,
        "transcription_confidence": result.transcription_confidence,
        "subjects": result.subjects,
        "processing_time": result.processing_time,
        "metadata": result.metadata,
        "icon_matches": [
            {
                "icon_name": match.icon.name,
                "icon_url": match.icon.url,
                "icon_category": getattr(match.icon, 'category', None),
                "icon_tags": getattr(match.icon, 'tags', []),
                "confidence": match.confidence,
                "match_reason": match.match_reason,
                "subjects_matched": match.subjects_matched
            }
            for match in result.icon_matches
        ]
    }
    
    if not result.success:
        output_data["error"] = result.error
    
    return json.dumps(output_data, indent=2, ensure_ascii=False)


def _format_table_output(result) -> str:
    """Format result as a table."""
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("AUDIO TO ICON PROCESSING RESULTS")
    output_lines.append("=" * 80)
    
    # Basic information
    output_lines.append(f"Success: {'✓' if result.success else '✗'}")
    
    # Source information
    source_type = result.metadata.get('source_type', 'local_file')
    if source_type == 'podcast':
        output_lines.append(f"Source: Podcast URL")
        if 'episode_title' in result.metadata and result.metadata['episode_title']:
            output_lines.append(f"Episode: {result.metadata['episode_title']}")
        if 'show_name' in result.metadata and result.metadata['show_name']:
            output_lines.append(f"Show: {result.metadata['show_name']}")
    else:
        output_lines.append(f"Source: Local Audio File")
        if 'audio_file' in result.metadata:
            output_lines.append(f"File: {result.metadata['audio_file']}")
    
    if result.transcription:
        output_lines.append(f"Transcription: {result.transcription[:100]}{'...' if len(result.transcription) > 100 else ''}")
        output_lines.append(f"Transcription Confidence: {result.transcription_confidence:.2f}")
    output_lines.append(f"Processing Time: {result.processing_time:.2f}s")
    
    if not result.success and result.error:
        output_lines.append(f"Error: {result.error}")
        return "\n".join(output_lines)
    
    # Subjects found
    if result.subjects:
        output_lines.append("\nSUBJECTS IDENTIFIED:")
        output_lines.append("-" * 40)
        
        for subject_type, subjects_list in result.subjects.items():
            if subjects_list:
                output_lines.append(f"{subject_type.upper()}:")
                for subject in subjects_list:
                    if isinstance(subject, dict):
                        name = subject.get('name', 'Unknown')
                        conf = subject.get('confidence', 0)
                        output_lines.append(f"  • {name} (confidence: {conf:.2f})")
                    else:
                        output_lines.append(f"  • {subject}")
    
    # Icon matches
    if result.icon_matches:
        output_lines.append(f"\nICON MATCHES FOUND ({len(result.icon_matches)}):")
        output_lines.append("-" * 40)
        
        for i, match in enumerate(result.icon_matches, 1):
            output_lines.append(f"{i}. {match.icon.name}")
            output_lines.append(f"   URL: {match.icon.url}")
            if hasattr(match.icon, 'category') and match.icon.category:
                output_lines.append(f"   Category: {match.icon.category}")
            if hasattr(match.icon, 'tags') and match.icon.tags:
                output_lines.append(f"   Tags: {', '.join(match.icon.tags)}")
            output_lines.append(f"   Confidence: {match.confidence:.2f}")
            output_lines.append(f"   Match Reason: {match.match_reason}")
            output_lines.append(f"   Matched Subjects: {', '.join(match.subjects_matched)}")
            output_lines.append("")
    else:
        output_lines.append("\nNo icon matches found.")
    
    # Metadata
    if result.metadata:
        output_lines.append("METADATA:")
        output_lines.append("-" * 40)
        for key, value in result.metadata.items():
            output_lines.append(f"{key}: {value}")
    
    output_lines.append("=" * 80)
    return "\n".join(output_lines)


def _format_summary_output(result) -> str:
    """Format result as a summary."""
    output_lines = []
    
    # Summary header
    status = "SUCCESS" if result.success else "FAILED"
    source_type = result.metadata.get('source_type', 'local_file')
    source_desc = "PODCAST" if source_type == 'podcast' else "LOCAL FILE"
    output_lines.append(f"AUDIO-TO-ICON PROCESSING {status} ({source_desc})")
    output_lines.append("=" * 50)
    
    if not result.success:
        output_lines.append(f"Error: {result.error}")
        return "\n".join(output_lines)
    
    # Source information
    if source_type == 'podcast':
        if 'episode_title' in result.metadata and result.metadata['episode_title']:
            output_lines.append(f"Episode: {result.metadata['episode_title']}")
        if 'show_name' in result.metadata and result.metadata['show_name']:
            output_lines.append(f"Show: {result.metadata['show_name']}")
    
    # Key metrics
    output_lines.append(f"Processing time: {result.processing_time:.2f}s")
    if result.transcription_confidence:
        output_lines.append(f"Transcription confidence: {result.transcription_confidence:.2f}")
    
    # Subject summary
    total_subjects = sum(len(subjects_list) for subjects_list in result.subjects.values() if subjects_list)
    output_lines.append(f"Subjects found: {total_subjects}")
    
    # Icon match summary
    output_lines.append(f"Icon matches: {len(result.icon_matches)}")
    
    if result.icon_matches:
        output_lines.append("\nTop matches:")
        for i, match in enumerate(result.icon_matches[:3], 1):  # Show top 3
            output_lines.append(f"  {i}. {match.icon.name} (confidence: {match.confidence:.2f})")
    
    return "\n".join(output_lines)


@audio_icon_matcher_commands.command("info")
def show_info():
    """Show information about the audio-icon matcher."""
    click.echo("AUDIO-ICON MATCHER")
    click.echo("=" * 50)
    click.echo("Analyze audio content to find matching icons based on identified subjects")
    click.echo("and themes in audio files or podcast episodes.")
    click.echo("")
    click.echo("COMMANDS:")
    click.echo("  find-icons   Find matching icons for audio source")
    click.echo("  validate     Validate audio source without processing")
    click.echo("  formats      List supported audio formats and sources")
    click.echo("  info         Show this information")
    click.echo("")
    click.echo("FEATURES:")
    click.echo("  • Audio transcription using Whisper")
    click.echo("  • Subject identification (keywords, topics, entities)")
    click.echo("  • Intelligent icon matching with confidence scoring")
    click.echo("  • Multiple output formats (JSON, table, summary)")
    click.echo("  • Configurable confidence thresholds")
    click.echo("")
    click.echo("SUPPORTED SOURCES:")
    click.echo("  • Local files: WAV, MP3, M4A formats")
    click.echo("  • Podcast feeds: RSS/XML feeds")
    click.echo("  • Direct URLs: Direct links to audio files")
    click.echo("")
    click.echo("EXAMPLES:")
    click.echo("  # Find icons for local audio file")
    click.echo("  audio-icon-matcher find-icons my_audio.mp3")
    click.echo("")
    click.echo("  # Find icons for podcast episode")
    click.echo("  audio-icon-matcher find-icons https://podcast.example.com/episode.rss")
    click.echo("")
    click.echo("  # Get JSON output with custom threshold")
    click.echo("  audio-icon-matcher find-icons audio.wav --output-format json --confidence-threshold 0.5")
    click.echo("")
    click.echo("For detailed help with any command:")
    click.echo("  audio-icon-matcher COMMAND --help")


def main():
    """Main entry point for the CLI."""
    audio_icon_matcher_commands()


if __name__ == "__main__":
    main()
