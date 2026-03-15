from dataclasses import dataclass
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine_cli.application.lifecycle import ProcessLogController


@dataclass
class ManagedProcessHandle:
    """Runtime-only handle for a managed subprocess."""

    process: subprocess.Popen[str]
    command: str
    log_streamer: "ProcessLogController | None" = None

    def get_command(self) -> str:
        """Return the launch command for the managed process."""
        return self.command

    def get_stdout(self):
        """Expose stdout without leaking the subprocess object into application typing."""
        return self.process.stdout

    def get_log_streamer(self) -> "ProcessLogController | None":
        """Return the attached log streamer, if one exists."""
        return self.log_streamer

    def set_log_streamer(self, streamer: "ProcessLogController | None") -> None:
        """Attach or clear the log streamer reference."""
        self.log_streamer = streamer
