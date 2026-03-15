class ExecutionServiceError(Exception):
    """Base error for execution-service failures."""


class UnsupportedTaskKindError(ExecutionServiceError):
    """Raised when a task kind is not part of the supported catalog."""


class InvalidTaskTransitionError(ExecutionServiceError):
    """Raised when a task status change is not allowed."""


class ActiveTaskConflictError(ExecutionServiceError):
    """Raised when a conflicting non-terminal task already exists for a target."""


class UnsupportedTaskCancellationError(ExecutionServiceError):
    """Raised when task cancellation is not supported for the current state."""
