from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from engine_cli.application import ServerTerminalStore, SessionContext, TerminalLogLine


class TerminalBody(Widget):
    """Terminal workspace used by server mode."""

    def __init__(
        self,
        session_context: SessionContext,
        terminal_store: ServerTerminalStore,
        refresh_interval: float = 0.2,
    ) -> None:
        super().__init__()
        self.session_context = session_context
        self.terminal_store = terminal_store
        self.refresh_interval = refresh_interval
        self._current_renderable = Text()
        self._log_surface = Static(self._current_renderable, classes="terminal-log")
        self._active_server_id: str | None = None
        self._last_buffer_revision = -1
        self._last_rendered_count = 0
        self._rendered_lines: list[TerminalLogLine] = []

    def compose(self) -> ComposeResult:
        with Container(classes="workspace terminal-workspace"):
            yield Static("Live Server Terminal", classes="workspace-title")
            with VerticalScroll(classes="terminal-output"):
                yield self._log_surface

    def on_mount(self) -> None:
        """Start periodic refresh for the active terminal buffer."""
        self.set_interval(self.refresh_interval, self.refresh_logs)

    def refresh_logs(self) -> None:
        """Synchronize the log surface with the active server buffer."""
        active_server_id = self.session_context.active_server_instance_id
        if active_server_id is None:
            self._reset_render_state(active_server_id)
            self._set_renderable(Text())
            return

        buffer = self.terminal_store.get_buffer(active_server_id)
        snapshot = buffer.snapshot()
        revision = buffer.revision
        if active_server_id != self._active_server_id:
            self._reset_render_state(active_server_id)
            self._rendered_lines = snapshot
        elif revision != self._last_buffer_revision:
            if (
                len(snapshot) < self._last_rendered_count
                or (
                    len(snapshot) == buffer.max_lines
                    and len(snapshot) == self._last_rendered_count
                )
            ):
                self._rendered_lines = snapshot
            else:
                self._rendered_lines.extend(snapshot[self._last_rendered_count :])

        self._last_rendered_count = len(self._rendered_lines)
        self._last_buffer_revision = revision
        self._set_renderable(self._render_lines(self._rendered_lines))

    def _reset_render_state(self, active_server_id: str | None) -> None:
        """Reset local render bookkeeping for a buffer switch or clear."""
        self._active_server_id = active_server_id
        self._last_buffer_revision = -1
        self._last_rendered_count = 0
        self._rendered_lines = []

    def _render_lines(self, lines: list[TerminalLogLine]) -> Text:
        """Render buffered lines with lightweight emphasis from parsed metadata."""
        rendered = Text()
        for index, line in enumerate(lines):
            if index:
                rendered.append("\n")
            rendered.append(line.raw, style=self._style_for_line(line))
        return rendered

    def _style_for_line(self, line: TerminalLogLine) -> str:
        """Choose a simple whole-line style based on log level."""
        if line.level in {"ERROR", "FATAL"}:
            return "bold red"
        if line.level == "WARN":
            return "yellow"
        if line.level == "INFO":
            return "cyan"
        return "white"

    @property
    def rendered_text(self) -> str:
        """Expose the current rendered plain text for lightweight tests."""
        return self._current_renderable.plain

    def _set_renderable(self, renderable: Text) -> None:
        """Persist the current renderable and push it to the mounted surface."""
        self._current_renderable = renderable
        if self.is_mounted:
            self._log_surface.update(renderable)
