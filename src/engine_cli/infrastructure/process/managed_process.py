from dataclasses import dataclass
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine_cli.infrastructure.process.log_streamer import ProcessLogStreamer


@dataclass
class ManagedProcessHandle:
    """Runtime-only handle for a managed subprocess."""

    process: subprocess.Popen[str]
    command: str
    log_streamer: "ProcessLogStreamer | None" = None
