class ServerInstanceManagerError(Exception):
    """Base error for server instance management failures."""


class ServerInspectionError(ServerInstanceManagerError):
    """Raised when a candidate server root cannot be inspected for import."""


class ServerInstanceNotFoundError(ServerInstanceManagerError):
    """Raised when a server instance cannot be found in the catalog."""
