"""Custom exceptions for the icon curator."""


class IconCuratorError(Exception):
    """Base exception for all icon curator errors."""
    pass


class ScrapingError(IconCuratorError):
    """Raised when there's an error scraping icons from a website."""
    pass


class ValidationError(IconCuratorError):
    """Raised when input validation fails."""
    pass


class DatabaseError(IconCuratorError):
    """Raised when database operations fail."""
    pass


class ProcessingError(IconCuratorError):
    """Raised when icon processing fails."""
    pass


class NetworkError(IconCuratorError):
    """Raised when network requests fail."""
    pass
