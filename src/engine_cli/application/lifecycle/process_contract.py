from __future__ import annotations

from collections.abc import Callable
from typing import IO, Protocol


class ProcessLogController(Protocol):
    """Application-facing control surface for process log streaming."""

    def start(self) -> None:
        """Begin streaming process output."""
        ...

    def stop(self) -> None:
        """Request that log streaming stop."""
        ...

    def join(self, timeout: float | None = None) -> None:
        """Wait for the streamer to finish shutting down."""
        ...


class ProcessHandle(Protocol):
    """Application-facing handle for one managed server process."""

    def get_command(self) -> str:
        """Return the launch command for the managed process."""
        ...

    def get_stdout(self) -> IO[str] | None:
        """Return the process stdout stream, if available."""
        ...

    def get_log_streamer(self) -> ProcessLogController | None:
        """Return the attached log streamer, if any."""
        ...

    def set_log_streamer(self, streamer: ProcessLogController | None) -> None:
        """Attach or clear the log streamer reference."""
        ...


class ProcessManager(Protocol):
    """Boundary for starting, observing, commanding, and stopping server processes."""

    def start(self, command: str, cwd: str) -> ProcessHandle:
        """Launch a process in the specified directory and return its handle."""
        ...

    def is_running(self, handle: ProcessHandle) -> bool:
        """Return whether the process is still running."""
        ...

    def stop(self, handle: ProcessHandle, timeout: float = 2.0) -> None:
        """Stop the managed process."""
        ...

    def send_command(self, handle: ProcessHandle, command: str) -> None:
        """Write one command to the managed process stdin."""
        ...

    def create_log_streamer(
        self,
        handle: ProcessHandle,
        write_line: Callable[[str], object],
    ) -> ProcessLogController:
        """Create one log streamer attached to the process stdout."""
        ...


class NullProcessManager:
    """Fallback process manager for lifecycle construction without runtime wiring."""

    def start(self, command: str, cwd: str) -> ProcessHandle:
        raise RuntimeError("No process manager is configured for server lifecycle start.")

    def is_running(self, handle: ProcessHandle) -> bool:
        return False

    def stop(self, handle: ProcessHandle, timeout: float = 2.0) -> None:
        raise RuntimeError("No process manager is configured for server lifecycle stop.")

    def send_command(self, handle: ProcessHandle, command: str) -> None:
        raise RuntimeError("No process manager is configured for server commands.")

    def create_log_streamer(
        self,
        handle: ProcessHandle,
        write_line: Callable[[str], object],
    ) -> ProcessLogController:
        raise RuntimeError("No process manager is configured for log streaming.")
