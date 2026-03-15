from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input

from engine_cli.application import (
    ServerInspectionError,
    ServerInspectionResult,
    ServerInstanceManager,
)
from engine_cli.domain import ServerInstance
from engine_cli.interfaces.tui.modals.base import ModalFrameScreen


class AddServerModalScreen(ModalFrameScreen):
    """Modal workflow for importing one local Minecraft server."""

    def __init__(self, server_manager: ServerInstanceManager) -> None:
        super().__init__("Add Server", confirm_label="Add")
        self.server_manager = server_manager
        self.name_input = Input(placeholder="Server name", id="server-name-input")
        self.location_input = Input(
            placeholder="Server root path",
            id="server-location-input",
        )
        self.command_input = Input(
            placeholder="Start command",
            id="server-command-input",
        )
        self._name_value = ""
        self._location_value = ""
        self._command_value = ""
        self._can_submit = False
        self._command_autofilled = False
        self.inspection_result: ServerInspectionResult | None = None

    def compose_body(self) -> ComposeResult:
        with Vertical(classes="modal-body"):
            yield self.name_input
            yield self.location_input
            yield self.command_input

    def on_mount(self) -> None:
        """Restore any pre-seeded values and synchronize submit state."""
        if self._name_value:
            self.name_input.value = self._name_value
        if self._location_value:
            self.location_input.value = self._location_value
        if self._command_value:
            self.command_input.value = self._command_value
        self._sync_submit_state()
        super().on_mount()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Track current values and update validation as the form changes."""
        if event.input is self.name_input:
            self._name_value = event.value.strip()
        elif event.input is self.location_input:
            self._location_value = event.value.strip()
            self.inspection_result = None
            if self._command_autofilled:
                self._command_value = ""
                self._command_autofilled = False
                if self.is_mounted:
                    self.command_input.value = ""
        elif event.input is self.command_input:
            self._command_value = event.value.strip()
            if self._command_value:
                self._command_autofilled = False
        self._sync_submit_state()

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Populate the command field lazily when it gains focus."""
        if event.widget is self.command_input:
            self.populate_command_from_location()

    def inspect_server(self) -> ServerInspectionResult:
        """Inspect the current location input without updating the UI."""
        inspection = self.server_manager.inspect_server(self.location_value)
        self.inspection_result = inspection
        return inspection

    def confirm_result(self) -> object | None:
        """Create a server only when the current form state is valid."""
        if not self.can_submit:
            return self.KEEP_OPEN
        try:
            return self.create_server()
        except ServerInspectionError:
            self._sync_submit_state()
            return self.KEEP_OPEN

    def create_server(self) -> ServerInstance:
        """Create a server from current form values, inspecting internally first."""
        if self.inspection_result is None:
            self.inspect_server()
        return self.server_manager.import_server(
            name=self.name_value,
            location=self.location_value,
            command=self.command_value,
        )

    @property
    def name_value(self) -> str:
        """Return the current server name value in a test-friendly way."""
        if self.is_mounted:
            return self.name_input.value.strip()
        return self._name_value

    @property
    def location_value(self) -> str:
        """Return the current server path value in a test-friendly way."""
        if self.is_mounted:
            return self.location_input.value.strip()
        return self._location_value

    @property
    def command_value(self) -> str:
        """Return the current server command value in a test-friendly way."""
        if self.is_mounted:
            return self.command_input.value.strip()
        return self._command_value

    @property
    def can_submit(self) -> bool:
        """Return whether the current modal state is valid for import."""
        return self._can_submit

    def set_form_values(self, *, name: str, location: str, command: str) -> None:
        """Set modal form values without requiring a mounted Textual app."""
        self._name_value = name.strip()
        self._location_value = location.strip()
        self._command_value = command.strip()
        self._command_autofilled = False
        if self.is_mounted:
            self.name_input.value = self._name_value
            self.location_input.value = self._location_value
            self.command_input.value = self._command_value
        self._sync_submit_state()

    def populate_command_from_location(self) -> None:
        """Fill the command field with a default jar launch command when possible."""
        if self.command_value:
            return
        suggested_command = self.server_manager.suggest_start_command(self.location_value)
        if suggested_command is None:
            return
        self._command_autofilled = True
        self._command_value = suggested_command
        if self.is_mounted:
            self.command_input.value = suggested_command
        self._sync_submit_state()

    def _sync_submit_state(self) -> None:
        """Recompute inspection state and whether the Add action should be enabled."""
        self.inspection_result = None
        if self.location_value:
            try:
                self.inspection_result = self.server_manager.inspect_server(self.location_value)
            except ServerInspectionError:
                self.inspection_result = None
        self._can_submit = bool(
            self.name_value
            and self.location_value
            and self.command_value
            and self.inspection_result is not None
        )
        if self.is_mounted:
            self.confirm_action.set_disabled(not self._can_submit)
