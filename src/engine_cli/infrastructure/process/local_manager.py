from pathlib import Path
import shlex
from collections.abc import Callable
import subprocess
from typing import cast

from engine_cli.application.lifecycle import ProcessHandle
from engine_cli.infrastructure.process.errors import ProcessCommandError
from engine_cli.infrastructure.process.log_streamer import ProcessLogStreamer
from engine_cli.infrastructure.process.managed_process import ManagedProcessHandle


class LocalProcessManager:
    """Synchronous local process adapter for the first vertical slice."""

    def start(self, command: str, cwd: str) -> ManagedProcessHandle:
        """Launch a process in the specified directory and return a handle."""
        working_directory = Path(cwd)
        process = subprocess.Popen(
            self._split_command(command),
            cwd=working_directory,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return ManagedProcessHandle(process=process, command=command)

    def is_running(self, handle: ProcessHandle) -> bool:
        """Check if the process is still running."""
        managed_handle = cast(ManagedProcessHandle, handle)
        return managed_handle.process.poll() is None

    def stop(self, handle: ProcessHandle, timeout: float = 2.0) -> None:
        """Gracefully terminate the process, falling back to kill on timeout."""
        managed_handle = cast(ManagedProcessHandle, handle)
        if not self.is_running(managed_handle):
            self._close_streams(managed_handle)
            return
        managed_handle.process.terminate()
        try:
            managed_handle.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            managed_handle.process.kill()
            managed_handle.process.wait(timeout=timeout)
        finally:
            self._close_streams(managed_handle)

    def send_command(self, handle: ProcessHandle, command: str) -> None:
        """Write one command to the managed process stdin and flush immediately."""
        managed_handle = cast(ManagedProcessHandle, handle)
        normalized_command = command.strip()
        if not normalized_command:
            raise ProcessCommandError("Server command is required.")
        stdin = managed_handle.process.stdin
        if stdin is None or stdin.closed:
            raise ProcessCommandError("Managed process stdin is not available.")
        if not self.is_running(managed_handle):
            raise ProcessCommandError("Managed process is not running.")
        stdin.write(f"{normalized_command}\n")
        stdin.flush()

    def create_log_streamer(
        self,
        handle: ProcessHandle,
        write_line: Callable[[str], object],
    ) -> ProcessLogStreamer:
        """Create one log streamer for the process stdout."""
        managed_handle = cast(ManagedProcessHandle, handle)
        stdout = managed_handle.process.stdout
        if stdout is None:
            raise ProcessCommandError("Managed process stdout is not available.")
        return ProcessLogStreamer(stdout, write_line)

    def _close_streams(self, handle: ManagedProcessHandle) -> None:
        """Ensure all process standard streams are closed."""
        for stream in (handle.process.stdin, handle.process.stdout, handle.process.stderr):
            if stream is not None and not stream.closed:
                stream.close()

    def _split_command(self, command: str) -> list[str]:
        """Parse command string into arguments using non-POSIX splitting for Windows."""
        return [part.strip('"') for part in shlex.split(command, posix=False)]
