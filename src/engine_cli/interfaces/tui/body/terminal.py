from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.widgets import Static


class TerminalBody(Widget):
    """Terminal workspace used by server mode."""

    def compose(self) -> ComposeResult:
        with Container(classes="workspace terminal-workspace"):
            yield Static("Live Server Terminal", classes="workspace-title")
            yield Static(
                "Runtime output and command feedback will stream here.",
                classes="workspace-subtitle",
            )
            with Vertical(classes="terminal-output"):
                yield Static("[system] terminal attached to selected server", classes="terminal-line")
                yield Static("[info] live output not wired yet", classes="terminal-line")
                yield Static("[hint] use this area for logs, status, and command echo", classes="terminal-line")
