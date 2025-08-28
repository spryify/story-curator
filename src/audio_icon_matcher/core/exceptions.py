"""Exception classes for audio icon matcher."""


class AudioIconError(Exception):
    """Base exception for audio icon matcher errors."""
    pass


class AudioIconValidationError(AudioIconError):
    """Raised when input validation fails."""
    pass


class AudioIconProcessingError(AudioIconError):
    """Raised when audio processing fails."""
    pass


class IconMatchingError(AudioIconError):
    """Raised when icon matching fails."""
    pass


class SubjectIdentificationError(AudioIconError):
    """Raised when subject identification fails."""
    pass
