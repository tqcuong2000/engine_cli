class ServerInstanceValidationError(Exception):
    """Raised when a server instance cannot satisfy its validation contract."""


class ServerInstanceLifecycleError(Exception):
    """Raised when a server lifecycle transition cannot be completed."""


class AgentRuntimeValidationError(Exception):
    """Raised when an agent runtime cannot satisfy its validation contract."""


class AgentRuntimeLifecycleError(Exception):
    """Raised when an agent runtime lifecycle transition cannot be completed."""
