from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Button, Static
from typing import TypedDict

from engine_cli.interfaces.tui.panel.context import PanelViewContext


class ServerEntry(TypedDict):
    server_instance_id: str
    name: str
    label: str
    is_active: bool
    status_marker: str


class ServersPanelView(Widget):
    """Panel tab for browsing and selecting managed server instances."""

    def __init__(self, panel_context: PanelViewContext) -> None:
        super().__init__()
        self.panel_context = panel_context

    def compose(self) -> ComposeResult:
        entries = self.server_entries()
        active_server = self.panel_context.server_manager.get_server(
            self.panel_context.session_context.active_server_instance_id or ""
        )
        has_selection = active_server is not None
        is_running = self._is_running(active_server)
        summary_text = (
            f"Servers ({len(entries)})" if entries else "Servers (0) / No servers found."
        )

        with Container(classes="panel-view"):
            with Container(classes="server-list"):
                yield Static(summary_text, classes="panel-value")
                for entry in entries:
                    entry_classes = "server-entry is-active" if entry["is_active"] else "server-entry"
                    with Container(classes=entry_classes):
                        yield Button(
                            entry["name"],
                            id=f"server-select-{entry['server_instance_id']}",
                            classes="server-label",
                        )
                        yield Static(entry["status_marker"], classes="server-online-marker")

            with Container(classes="panel-bottom"):
                with Container(classes="action-entry"):
                    yield Button("Add server", id="server-add", classes="action-label")
                    yield Button(
                        "Edit",
                        id="server-edit",
                        classes="action-label",
                        disabled=not has_selection,
                    )
                with Container(classes="action-entry"):
                    yield Button(
                        "Details",
                        id="server-details",
                        classes="action-label",
                        disabled=not has_selection,
                    )
                    yield Button(
                        "Stop" if is_running else "Start",
                        id="action-stop-server" if is_running else "action-start-server",
                        classes="action-label",
                        disabled=not has_selection,
                    )

    def server_entries(self) -> list[ServerEntry]:
        """Return pure server-entry data for rendering and tests."""
        entries: list[ServerEntry] = []
        for server in self.panel_context.server_manager.list_servers():
            is_active = (
                server.server_instance_id
                == self.panel_context.session_context.active_server_instance_id
            )
            entries.append(
                {
                    "server_instance_id": server.server_instance_id,
                    "name": server.name,
                    "label": (
                        f"{server.name} "
                        f"[{server.server_distribution} {server.minecraft_version}]"
                    ),
                    "is_active": is_active,
                    "status_marker": "o" if self._is_running(server) else "-",
                }
            )
        return entries

    def _is_running(self, server: object) -> bool:
        """Return whether a server is currently in the running state."""
        lifecycle_state = getattr(server, "lifecycle_state", None)
        return bool(lifecycle_state is not None and lifecycle_state.value == "running")
