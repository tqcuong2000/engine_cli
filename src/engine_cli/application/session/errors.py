class SessionContextError(Exception):
    """Base error for invalid session-context operations."""


class InvalidModeSwitchError(SessionContextError):
    """Raised when the requested mode change is invalid for the current state."""
