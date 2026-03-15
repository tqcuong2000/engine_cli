class SessionContextError(Exception):
    """Base error for invalid session-context operations."""


class InvalidModeSwitchError(SessionContextError):
    """Raised when the requested mode change is invalid for the current state."""


class UnknownAgentProfileError(SessionContextError):
    """Raised when an explicit profile selection references an unknown profile id."""


class IncompatibleAgentProfileError(SessionContextError):
    """Raised when an explicit profile selection does not match the current mode."""
