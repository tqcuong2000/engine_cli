from dataclasses import dataclass
import subprocess


@dataclass
class ManagedProcessHandle:
    """Runtime-only handle for a managed subprocess."""

    process: subprocess.Popen[str]
    command: str
