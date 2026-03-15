from threading import Event, Thread
from collections.abc import Callable
from typing import IO


class ProcessLogStreamer:
    """Read process output on a background thread and append it to a buffer."""

    def __init__(self, stream: IO[str], write_line: Callable[[str], object]) -> None:
        self.stream = stream
        self.write_line = write_line
        self._stop_event = Event()
        self._thread = Thread(target=self._run, daemon=True)

    @property
    def is_running(self) -> bool:
        """Return whether the background reader thread is alive."""
        return self._thread.is_alive()

    def start(self) -> None:
        """Start the background reader once."""
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self) -> None:
        """Request that the reader exits as soon as the stream unblocks."""
        self._stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        """Wait for the reader thread to exit."""
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            line = self.stream.readline()
            if line == "":
                return
            self.write_line(line)
