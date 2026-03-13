class ServerInstanceValidationError(Exception):
    """Raised when a server instance cannot satisfy its validation contract."""


class ServerInstanceLifecycleError(Exception):
    """Raised when a server lifecycle transition cannot be completed."""
