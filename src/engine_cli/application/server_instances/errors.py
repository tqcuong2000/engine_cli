class ServerInstanceManagerError(Exception):
    """Base error for server instance management failures."""


class ServerInstanceNotFoundError(ServerInstanceManagerError):
    """Raised when a server instance cannot be found in the catalog."""
