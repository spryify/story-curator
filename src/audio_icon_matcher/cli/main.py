"""CLI commands for audio-to-icon pipeline."""

import click
import sys
import json
from pathlib import Path
from typing import Dict, Any

from ..core.pipeline import AudioIconPipeline
from ..core.exceptions import AudioIconValidationError, AudioIconProcessingError


@click.group(name="audio-icon-matcher")
def audio_icon_matcher_commands():
    """Audio-icon matcher commands."""
    pass


@audio_icon_matcher_commands.command("process")
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option("--max-icons", type=int, default=10, help="Maximum number of icons to return")
@click.option("--confidence-threshold", type=float, default=0.3, help="Minimum confidence threshold")
@click.option("--output-format", type=click.Choice(["json", "table", "summary"]), default="table", help="Output format")
@click.option("--output-file", type=click.Path(path_type=Path), help="Output file (if not specified, prints to stdout)")
def process_audio(audio_file, max_icons, confidence_threshold, output_format, output_file):
    """Process audio file to find matching icons."""
    try:
        pipeline = AudioIconPipeline()
        
        # Process the audio file
        result = pipeline.process(
            str(audio_file),
            max_icons=max_icons,
            confidence_threshold=confidence_threshold
        )
        
        # Format output
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
            click.echo(f"Results written to {output_file}")
        else:
            click.echo(output_data)
            
    except AudioIconValidationError as e:
        click.echo(f"Validation Error: {e}", err=True)
        sys.exit(1)
    except AudioIconProcessingError as e:
        click.echo(f"Processing Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
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
    output_lines.append(f"AUDIO-TO-ICON PROCESSING {status}")
    output_lines.append("=" * 50)
    
    if not result.success:
        output_lines.append(f"Error: {result.error}")
        return "\n".join(output_lines)
    
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


@audio_icon_matcher_commands.command("validate")
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
def validate_audio(audio_file):
    """Validate an audio file for processing."""
    try:
        pipeline = AudioIconPipeline()
        
        is_valid = pipeline.validate_audio_file(str(audio_file))
        
        if is_valid:
            click.echo(f"✓ {audio_file} is a valid audio file")
        else:
            click.echo(f"✗ {audio_file} is not a valid audio file")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error validating file: {e}", err=True)
        sys.exit(1)


@audio_icon_matcher_commands.command("formats")
def list_formats():
    """List supported audio formats."""
    try:
        pipeline = AudioIconPipeline()
        formats = pipeline.get_supported_formats()
        
        click.echo("Supported audio formats:")
        for fmt in sorted(formats):
            click.echo(f"  • {fmt}")
            
    except Exception as e:
        click.echo(f"Error getting formats: {e}", err=True)
        sys.exit(1)


@audio_icon_matcher_commands.command("info")
def show_info():
    """Show information about the audio-icon matcher."""
    click.echo("AUDIO-ICON MATCHER")
    click.echo("=" * 50)
    click.echo("A tool for processing audio files and finding matching icons")
    click.echo("based on the audio content and identified subjects.")
    click.echo("")
    click.echo("Features:")
    click.echo("  • Audio transcription using Whisper")
    click.echo("  • Subject identification (keywords, topics, entities)")
    click.echo("  • Icon matching with confidence scoring")
    click.echo("  • Multiple output formats (JSON, table, summary)")
    click.echo("  • Configurable confidence thresholds")
    click.echo("")
    click.echo("For help with specific commands, use:")
    click.echo("  audio-icon-matcher COMMAND --help")


def main():
    """Main entry point for the CLI."""
    audio_icon_matcher_commands()


if __name__ == "__main__":
    main()
