from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button

from engine_cli.application import (
    AgentProfileSelectionService,
    InvalidModeSwitchError,
    ServerCommandError,
    ServerCommandService,
    ServerInstanceManager,
    ServerInstanceNotFoundError,
    ServerInstanceLifecycleService,
    ServerTerminalStore,
    SessionContext,
)
from engine_cli.config import ConfigResolver, ResolvedSettings
from engine_cli.domain import OperatingMode, ServerInstanceLifecycleState
from engine_cli.interfaces.tui.layout.body import Body
from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header
from engine_cli.interfaces.tui.layout.panel import Panel
from engine_cli.interfaces.tui.main.user_inputs import UserInputs
from engine_cli.interfaces.tui.modals import AddServerModalScreen, ConfirmModalScreen
from engine_cli.interfaces.tui.theme.engine_dark import ENGINE_THEME
from engine_cli.infrastructure.persistence import AppPaths, SqliteServerInstanceRepository


class EngineCli(App):
    """A basic Textual application template."""

    CSS_PATH = "../../resources/app.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("b", "set_base_mode", "Base mode"),
        ("s", "set_server_mode", "Server mode"),
        ("p", "set_datapack_mode", "Datapack mode"),
        ("[", "previous_panel_tab", "Prev panel"),
        ("]", "next_panel_tab", "Next panel"),
    ]

    def __init__(
        self,
        *,
        app_root: Path | None = None,
        workspace_root: Path | None = None,
    ) -> None:
        super().__init__()
        self.app_paths = AppPaths.from_root(app_root)
        self.workspace_root = (
            workspace_root.expanduser().resolve() if workspace_root is not None else None
        )
        self.settings: ResolvedSettings = ConfigResolver().resolve(
            global_config_dir=self.app_paths.config_dir,
            workspace_root=self.workspace_root,
        )
        self.session_context = SessionContext()
        self.profile_selection_service = AgentProfileSelectionService()
        self._sync_active_agent_profile()
        self.terminal_store = ServerTerminalStore()
        self.server_manager = ServerInstanceManager(
            catalog=SqliteServerInstanceRepository(self.app_paths.db_path)
        )
        self.lifecycle_service = ServerInstanceLifecycleService(
            terminal_store=self.terminal_store
        )
        self.server_command_service = ServerCommandService(
            lifecycle_service=self.lifecycle_service,
            terminal_store=self.terminal_store,
        )

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.register_theme(ENGINE_THEME)
        self.theme = "engine_dark"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(classes="app-container"):
            with Horizontal(classes="app-top"):
                with Vertical(classes="app-left"):
                    yield Header(self.session_context)
                    yield Body(self.session_context, self.terminal_store)
                with Container(classes="app-right"):
                    yield Panel(
                        self.session_context,
                        self.server_manager,
                        self.lifecycle_service,
                    )
            with Container(classes="app-bottom"):
                yield Footer(self.session_context)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_set_base_mode(self) -> None:
        self._switch_mode(OperatingMode.BASE)

    def action_set_server_mode(self) -> None:
        self._switch_mode(OperatingMode.SERVER)

    def action_set_datapack_mode(self) -> None:
        self._switch_mode(OperatingMode.DATAPACK)

    def action_previous_panel_tab(self) -> None:
        self.query_one(Panel).previous_tab()

    def action_next_panel_tab(self) -> None:
        self.query_one(Panel).next_tab()

    def _switch_mode(self, mode: OperatingMode) -> None:
        try:
            self.session_context.switch_mode(mode)
        except InvalidModeSwitchError:
            return
        self._sync_active_agent_profile()
        self._refresh_mode_aware_widgets()

    def _sync_active_agent_profile(self) -> str:
        profile_id = self.profile_selection_service.resolve_effective_profile_id(
            session_context=self.session_context,
            settings=self.settings,
        )
        self.session_context.set_agent_profile(profile_id)
        return profile_id

    def _refresh_mode_aware_widgets(self) -> None:
        self.query_one(Header).refresh(recompose=True)
        self.query_one(Body).refresh(recompose=True)
        self.query_one(Panel).refresh(recompose=True)
        self.query_one(Footer).refresh(recompose=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks in panel views and modal launchers."""
        button_id = event.button.id or ""
        if button_id == "action-start-server":
            self._handle_start_server()
        elif button_id == "action-stop-server":
            self._handle_stop_server()
        elif button_id == "server-add":
            self._open_add_server_modal()
        elif button_id.startswith("server-select-"):
            self._handle_server_select(button_id.removeprefix("server-select-"))
        elif button_id.startswith("server-remove-"):
            self._open_remove_server_modal(button_id.removeprefix("server-remove-"))

    def on_user_inputs_submitted(self, event: UserInputs.Submitted) -> None:
        """Route server-mode footer input to the server command pipeline."""
        if self.session_context.mode is not OperatingMode.SERVER:
            return
        server = self._get_active_server()
        if server is None:
            self.notify("No server selected", severity="warning")
            return
        try:
            self.server_command_service.send(server, event.value)
        except ServerCommandError as exc:
            self.notify(str(exc), severity="error")
            return
        event.input_widget.clear()

    def _handle_start_server(self) -> None:
        """Start the selected managed server."""
        server = self._get_active_server()
        if server is None:
            self.notify("No server selected", severity="warning")
            return
        try:
            self.lifecycle_service.validate(server)
            self.lifecycle_service.start(server)
            self._switch_mode(OperatingMode.SERVER)
            self.notify(f"Started {server.name}")
        except Exception as exc:
            self.notify(f"Failed to start server: {exc}", severity="error")

    def _handle_stop_server(self) -> None:
        """Stop the selected managed server."""
        server = self._get_active_server()
        if server is None:
            self.notify("No server selected", severity="warning")
            return
        try:
            self.lifecycle_service.stop(server)
            self._refresh_mode_aware_widgets()
            self.notify(f"Stopped {server.name}")
        except Exception as exc:
            self.notify(f"Failed to stop server: {exc}", severity="error")

    def _handle_server_select(self, server_instance_id: str) -> None:
        """Select a managed server from the server catalog."""
        try:
            self.server_manager.select_server(
                server_instance_id,
                self.session_context,
            )
            self._switch_mode(OperatingMode.SERVER)
        except ServerInstanceNotFoundError:
            return

    def _open_add_server_modal(self) -> None:
        """Open the add-server modal and refresh after a successful import."""
        self.push_screen(
            AddServerModalScreen(self.server_manager),
            self._handle_add_server_result,
        )

    def _handle_add_server_result(self, _result: object | None) -> None:
        """Refresh the shell after a server is added."""
        self._refresh_mode_aware_widgets()

    def _open_remove_server_modal(self, server_instance_id: str) -> None:
        """Open a confirmation modal for server removal."""
        server = self.server_manager.get_server(server_instance_id)
        if server is None:
            return
        self.push_screen(
            ConfirmModalScreen(
                "Remove Server",
                f"Remove {server.name} from this session?",
                confirm_label="Remove",
            ),
            lambda confirmed: self._handle_remove_server_result(
                server_instance_id,
                confirmed,
            ),
        )

    def _handle_remove_server_result(
        self,
        server_instance_id: str,
        confirmed: object | None,
    ) -> None:
        """Remove a server after confirmation and refresh the shell."""
        if confirmed is not True:
            return
        try:
            self.server_manager.remove_server(
                server_instance_id,
                session_context=self.session_context,
            )
        except ServerInstanceNotFoundError:
            return
        self._sync_active_agent_profile()
        self._refresh_mode_aware_widgets()

    def _get_active_server(self):
        """Return the selected server from the catalog, if any."""
        server_id = self.session_context.active_server_instance_id
        if server_id is None:
            return None
        server = self.server_manager.get_server(server_id)
        if server is None:
            return None
        if self.lifecycle_service.get_handle(server_id) is not None:
            server.lifecycle_state = ServerInstanceLifecycleState.RUNNING
        return server


def run(
    *,
    app_root: Path | None = None,
    workspace_root: Path | None = None,
) -> None:
    app = EngineCli(
        app_root=app_root,
        workspace_root=workspace_root or Path.cwd(),
    )
    app.run()


if __name__ == "__main__":
    run()
