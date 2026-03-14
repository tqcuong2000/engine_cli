from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from engine_cli.interfaces.tui.modals.base import ModalFrameScreen


class ConfirmModalScreen(ModalFrameScreen):
    """Simple reusable confirmation modal."""

    def __init__(
        self,
        title: str,
        message: str,
        *,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__(
            title,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
        )
        self.message = message

    def compose_body(self) -> ComposeResult:
        with Vertical(classes="modal-body"):
            yield Static(self.message, classes="modal-message")
