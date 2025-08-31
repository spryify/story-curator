# ADR-004: Command Line Interface Architecture

## Status
Accepted

## Context
The Story Curator requires a robust, user-friendly command-line interface that supports both simple and complex operations while maintaining extensibility for future features.

## Decision
We will implement a modular CLI architecture using Click and Rich libraries with the following structure:

1. **CLI Organization**
```
cli/
├── audio.py     # Audio processing commands
├── podcast.py   # Podcast analysis commands (see ADR-010)
└── README.md    # CLI documentation
```

2. **Core Principles**
   - Command grouping by media type
   - Consistent command structure
   - Rich terminal output
   - Progressive verbosity levels
   - Comprehensive error handling

3. **Command Structure**
```python
@click.group()
def cli():
    """Root command group."""
    pass

@cli.command()
@click.argument('file')
@click.option('--language', '-l', default='en')
def transcribe(file, language):
    """Command implementation."""
    pass
```

4. **User Experience Features**
   - Progress indicators for long operations
   - Color-coded output for status and errors
   - Detailed help messages
   - File output options
   - Verbose mode for debugging

## Consequences

### Positive
- Consistent user experience
- Easy to extend with new commands
- Rich terminal output improves usability
- Clear error messages aid troubleshooting
- Modular organization supports maintenance

### Negative
- Additional dependencies (Click, Rich)
- Learning curve for command structure
- Need to maintain consistent patterns

## Implementation Notes

1. **Command Definition**
   ```python
   @click.command()
   @click.argument('file', type=click.Path(exists=True))
   @click.option('--language', '-l', default='en')
   @click.option('--verbose', '-v', is_flag=True)
   def transcribe(file, language, verbose):
       """Command implementation with error handling."""
       try:
           result = process_file(file, language)
           if verbose:
               show_detailed_output(result)
           else:
               show_summary(result)
       except Exception as e:
           handle_error(e, verbose)
   ```

## Implementation Examples

### Audio Processing Commands
```python
@cli.group()
def audio():
    """Audio processing commands."""
    pass

@audio.command()
@click.argument('file')
@click.option('--language', '-l', default='en')
def transcribe(file, language):
    """Transcribe audio file to text."""
    try:
        with console.status("[bold blue]Processing audio..."):
            result = analyzer.transcribe(file, language)
        console.print(f"[green]Success:[/green] {result.text}")
    except Exception as e:
        handle_error(e, verbose)
```

### Podcast Analysis Commands (see [ADR-010](ADR-010-podcast-analysis-architecture.md))
```python
@cli.group()
def podcast():
    """Podcast analysis commands."""
    pass

@podcast.command()
@click.argument('url')
@click.option('--language', default='en')
@click.option('--max-duration', default=180)
@click.option('--confidence-threshold', default=0.5)
@click.option('--output', '-o', type=click.Path())
def analyze(url, language, max_duration, confidence_threshold, output):
    """Analyze podcast episode from RSS feed or direct URL."""
    try:
        options = AnalysisOptions(
            language=language,
            max_duration_minutes=max_duration,
            confidence_threshold=confidence_threshold
        )
        with console.status("[bold blue]Analyzing episode..."):
            result = analyzer.analyze_episode(url, options)
        
        if output:
            save_results(result, output)
        else:
            display_results(result)
    except Exception as e:
        handle_error(e, verbose)
```

### Common Patterns

1. **Rich Output Formatting**
   ```python
   def display_results(result):
       table = Table(title="Analysis Results")
       table.add_column("Subject", style="cyan")
       table.add_column("Confidence", style="green")
       
       for subject in result.subjects:
           table.add_row(subject.name, f"{subject.confidence:.2f}")
       
       console.print(table)
```

## References
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [ADR-010: Podcast Analysis Architecture](ADR-010-podcast-analysis-architecture.md) - Podcast CLI commands
- [Project CLI Documentation](../cli/README.md)
