from pathlib import Path
import shlex
import subprocess

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

    def is_running(self, handle: ManagedProcessHandle) -> bool:
        """Check if the process is still running."""
        return handle.process.poll() is None

    def stop(self, handle: ManagedProcessHandle, timeout: float = 2.0) -> None:
        """Gracefully terminate the process, falling back to kill on timeout."""
        if not self.is_running(handle):
            self._close_streams(handle)
            return
        handle.process.terminate()
        try:
            handle.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            handle.process.kill()
            handle.process.wait(timeout=timeout)
        finally:
            self._close_streams(handle)

    def _close_streams(self, handle: ManagedProcessHandle) -> None:
        """Ensure all process standard streams are closed."""
        for stream in (handle.process.stdin, handle.process.stdout, handle.process.stderr):
            if stream is not None and not stream.closed:
                stream.close()

    def _split_command(self, command: str) -> list[str]:
        """Parse command string into arguments using non-POSIX splitting for Windows."""
        return [part.strip('"') for part in shlex.split(command, posix=False)]
