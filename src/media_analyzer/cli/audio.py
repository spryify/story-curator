"""
Command line interface for audio analysis operations.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich import print as rprint

from media_analyzer.core.analyzer import Analyzer
from media_analyzer.core.exceptions import ValidationError

console = Console()

def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]Error:[/red] {message}")

def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]{message}[/green]")

@click.group()
def cli():
    """Audio analysis tools - Process and analyze audio files."""
    pass

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--language', '-l', default='en', help='Language of the audio (e.g., en, es, fr)')
@click.option('--summary-length', '-s', default=1000, type=int, help='Maximum length of the summary')
@click.option('--output', '-o', type=click.Path(), help='Output file for the transcription')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed processing information')
def transcribe(file: str, language: str, summary_length: int, output: Optional[str], verbose: bool):
    """
    Transcribe an audio file and generate a summary.
    
    Example:
        media-analyzer audio transcribe speech.wav --language en --summary-length 500
    """
    try:
        # Initialize analyzer
        analyzer = Analyzer()
        
        with console.status("[bold blue]Processing audio file...") as status:
            # Process the file
            options = {
                "language": language,
                "max_summary_length": summary_length
            }
            
            if verbose:
                status.update("[bold blue]Analyzing audio content...")
            
            result = analyzer.process_file(file, options)
            
            if verbose:
                status.update("[bold blue]Generating output...")
            
            # Create output text
            output_text = [
                "📝 [bold]Transcription Result[/bold]",
                "",
                "[bold blue]Full Transcription:[/bold blue]",
                result.full_text,
                "",
                "[bold green]Summary:[/bold green]",
                result.summary,
                "",
                "[bold yellow]Metadata:[/bold yellow]",
                f"• Confidence: {result.confidence:.2%}",
                f"• Duration: {result.metadata['duration']:.2f} seconds",
                f"• Processing Time: {result.metadata['processing_time']:.2f} seconds",
                f"• Language: {result.metadata['language']}",
                f"• Sample Rate: {result.metadata['sample_rate']} Hz",
                f"• Channels: {result.metadata['channels']}"
            ]
            
            # Output handling
            if output:
                # Save to file
                output_path = Path(output)
                with output_path.open('w', encoding='utf-8') as f:
                    # Write plain text version
                    f.write(f"Transcription Result\n\n")
                    f.write(f"Full Transcription:\n{result.full_text}\n\n")
                    f.write(f"Summary:\n{result.summary}\n\n")
                    f.write("Metadata:\n")
                    f.write(f"Confidence: {result.confidence:.2%}\n")
                    f.write(f"Duration: {result.metadata['duration']:.2f} seconds\n")
                    f.write(f"Processing Time: {result.metadata['processing_time']:.2f} seconds\n")
                    f.write(f"Language: {result.metadata['language']}\n")
                    f.write(f"Sample Rate: {result.metadata['sample_rate']} Hz\n")
                    f.write(f"Channels: {result.metadata['channels']}\n")
                print_success(f"Results saved to: {output}")
            else:
                # Print to console with rich formatting
                console.print("\n".join(output_text))
            
            print_success("\n✨ Analysis complete!")
            
    except ValidationError as e:
        print_error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Processing failed: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)

if __name__ == '__main__':
    cli()
