"""Audio error models."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ProcessingError:
    """Represents an error that occurred during processing."""
    error_code: str
    message: str
    details: Dict
