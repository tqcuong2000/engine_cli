from collections import deque
from dataclasses import dataclass
import re
from threading import Lock


TIMESTAMP_PATTERN = re.compile(r"^\[(?P<timestamp>\d{2}:\d{2}:\d{2})\]")
LEVEL_PATTERN = re.compile(r"\[(?:[^\]]*?/)?(?P<level>[A-Z]+)\]:")


@dataclass(frozen=True)
class TerminalLogLine:
    """One terminal line with lightweight parsed metadata."""

    raw: str
    timestamp: str | None = None
    level: str | None = None


class ServerTerminalBuffer:
    """Thread-safe in-memory ring buffer for one server terminal stream."""

    def __init__(self, max_lines: int = 1000) -> None:
        self.max_lines = max_lines
        self._lines: deque[TerminalLogLine] = deque(maxlen=max_lines)
        self._lock = Lock()
        self._revision = 0

    @property
    def revision(self) -> int:
        """Return the current buffer revision for change detection."""
        with self._lock:
            return self._revision

    def append(self, raw_line: str) -> TerminalLogLine:
        """Parse and append one line to the buffer."""
        line = parse_terminal_log_line(raw_line)
        with self._lock:
            self._lines.append(line)
            self._revision += 1
        return line

    def snapshot(self) -> list[TerminalLogLine]:
        """Return a stable copy of the current buffered lines."""
        with self._lock:
            return list(self._lines)

    def clear(self) -> None:
        """Remove all buffered lines and advance the revision."""
        with self._lock:
            self._lines.clear()
            self._revision += 1

    def __len__(self) -> int:
        with self._lock:
            return len(self._lines)


class ServerTerminalStore:
    """Session-scoped registry of per-server terminal buffers."""

    def __init__(self, default_max_lines: int = 1000) -> None:
        self.default_max_lines = default_max_lines
        self._buffers: dict[str, ServerTerminalBuffer] = {}
        self._lock = Lock()

    def get_buffer(self, server_instance_id: str) -> ServerTerminalBuffer:
        """Return a stable buffer for the given server identifier."""
        with self._lock:
            buffer = self._buffers.get(server_instance_id)
            if buffer is None:
                buffer = ServerTerminalBuffer(max_lines=self.default_max_lines)
                self._buffers[server_instance_id] = buffer
            return buffer


def parse_terminal_log_line(raw_line: str) -> TerminalLogLine:
    """Extract lightweight timestamp and level metadata when obvious."""
    normalized = raw_line.rstrip("\r\n")
    timestamp_match = TIMESTAMP_PATTERN.search(normalized)
    level_match = LEVEL_PATTERN.search(normalized)
    return TerminalLogLine(
        raw=normalized,
        timestamp=timestamp_match.group("timestamp") if timestamp_match else None,
        level=level_match.group("level") if level_match else None,
    )
