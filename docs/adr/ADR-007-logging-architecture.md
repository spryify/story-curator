# ADR-007: Logging Architecture

## Status
Accepted

## Context
The Story Curator needs comprehensive logging to support debugging, monitoring, and auditing of media processing operations. The logging system must be performant, configurable, and provide appropriate detail levels for different environments.

## Decision
We will implement a structured logging architecture using Python's built-in logging module with the following structure:

1. **Logger Hierarchy**
```python
# Root logger configuration
media_analyzer_logger = logging.getLogger("media_analyzer")

# Component loggers
core_logger = logging.getLogger("media_analyzer.core")
cli_logger = logging.getLogger("media_analyzer.cli")
processor_logger = logging.getLogger("media_analyzer.processors")
```

2. **Log Levels**
- ERROR: Processing failures, critical issues
- WARNING: Recoverable issues, degraded performance
- INFO: Progress updates, file processing status
- DEBUG: Detailed operation data, troubleshooting info
- TRACE: Extremely detailed debugging information

3. **Log Format**
```python
{
    "timestamp": "2025-08-24T12:34:56.789Z",
    "level": "INFO",
    "logger": "media_analyzer.processors.audio",
    "message": "Processing audio file: example.wav",
    "context": {
        "file_path": "/path/to/example.wav",
        "duration": "124.5s",
        "format": "wav"
    }
}
```

4. **Configuration Options**
- Log level by component
- Output destinations (file, console, syslog)
- Rotation policies
- Format customization
- Environment-specific defaults

## Consequences

### Positive
- Consistent logging across components
- Easy debugging and troubleshooting
- Performance monitoring capability
- Audit trail for processing
- Configurable detail levels

### Negative
- Disk space usage for logs
- Need to manage log rotation
- Performance overhead
- Risk of sensitive data logging

## Implementation Notes

1. **Logger Configuration**
   ```python
   def setup_logging(config_path: str = None) -> None:
       """Configure logging system."""
       config = {
           "version": 1,
           "disable_existing_loggers": False,
           "formatters": {
               "json": {
                   "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                   "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s"
               },
               "console": {
                   "format": "[%(levelname)s] %(name)s: %(message)s"
               }
           },
           "handlers": {
               "console": {
                   "class": "logging.StreamHandler",
                   "formatter": "console",
                   "level": "INFO"
               },
               "file": {
                   "class": "logging.handlers.RotatingFileHandler",
                   "formatter": "json",
                   "filename": "media_analyzer.log",
                   "maxBytes": 10485760,  # 10MB
                   "backupCount": 5
               }
           },
           "loggers": {
               "media_analyzer": {
                   "level": "INFO",
                   "handlers": ["console", "file"],
                   "propagate": False
               }
           }
       }
       logging.config.dictConfig(config)
   ```

2. **Context Manager for Operation Logging**
   ```python
   @contextmanager
   def log_operation(logger: logging.Logger, operation: str, **context):
       """Context manager for logging operations with timing."""
       start_time = time.time()
       logger.info(f"Starting {operation}", extra={"context": context})
       try:
           yield
           duration = time.time() - start_time
           logger.info(
               f"Completed {operation}",
               extra={
                   "context": {**context, "duration": duration}
               }
           )
       except Exception as e:
           logger.error(
               f"Failed {operation}",
               extra={
                   "context": {**context, "error": str(e)}
               },
               exc_info=True
           )
           raise
   ```

3. **Usage Example**
   ```python
   def process_audio(file_path: str) -> None:
       logger = logging.getLogger(__name__)
       with log_operation(logger, "audio_processing", file_path=file_path):
           # Process audio file
           result = analyze_audio(file_path)
           logger.debug("Analysis result", extra={"context": result})
   ```

## References
- Python logging documentation
- Twelve-Factor App logging principles
- ELK Stack best practices
- [Project Error Handling](ADR-003-error-handling.md)
