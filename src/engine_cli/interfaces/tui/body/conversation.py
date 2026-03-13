from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.widgets import Static

from engine_cli.domain import OperatingMode


class ConversationBody(Widget):
    """Conversation workspace used by base and datapack modes."""

    def __init__(self, mode: OperatingMode) -> None:
        super().__init__()
        self.mode = mode

    def compose(self) -> ComposeResult:
        title = "System Conversation" if self.mode is OperatingMode.BASE else "Datapack Conversation"
        subtitle = (
            "Ask the system agent to inspect, explain, and plan tasks."
            if self.mode is OperatingMode.BASE
            else "Work with the datapack agent on generation, validation, and workflow guidance."
        )
        with Container(classes="workspace conversation-workspace"):
            yield Static(title, classes="workspace-title")
            yield Static(subtitle, classes="workspace-subtitle")
            with Vertical(classes="conversation-thread"):
                yield Static("USER", classes="message-role user-role")
                yield Static(
                    "Select a mode-aware workflow and start the conversation.",
                    classes="message-bubble user-bubble",
                )
                yield Static("AGENT", classes="message-role agent-role")
                yield Static(
                    "Conversation history will appear here once the backend is wired.",
                    classes="message-bubble agent-bubble",
                )
