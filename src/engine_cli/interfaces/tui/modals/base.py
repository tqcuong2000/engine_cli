from collections.abc import Sequence

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, Static


class ModalAction(Static):
    """Focusable static control used for modal footer actions."""

    can_focus = True

    def __init__(
        self,
        label: str,
        *,
        action_id: str,
        classes: str = "modal-action",
        disabled: bool = False,
    ) -> None:
        super().__init__(label, id=action_id, classes=classes)
        self.disabled = disabled
        self._sync_disabled_state()

    def set_disabled(self, disabled: bool) -> None:
        """Update the disabled state and matching CSS class."""
        self.disabled = disabled
        self._sync_disabled_state()

    def _sync_disabled_state(self) -> None:
        self.set_class(self.disabled, "is-disabled")


class ModalFrameScreen(ModalScreen[object | None]):
    """Reusable modal shell with a title, body slot, and footer actions."""

    BINDINGS = [Binding("escape", "cancel_modal", "Close", show=False)]
    DEFAULT_CSS = """
    ModalFrameScreen {
        align: center middle;
    }
    """
    KEEP_OPEN = object()

    def __init__(
        self,
        title: str,
        *,
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__()
        self.modal_title = title
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.confirm_action = ModalAction(confirm_label, action_id="modal-confirm")
        self.cancel_action = ModalAction(cancel_label, action_id="modal-cancel")

    def compose(self) -> ComposeResult:
        with Container(id="modal-backdrop", classes="modal-backdrop"):
            with Vertical(classes="modal-frame"):
                with Container(classes="modal-title-container"):
                    yield Static(self.modal_title, classes="modal-title")
                    yield Static("Esc", id="modal-close", classes="modal-close-btn")
                yield from self.compose_body()
                with Container(classes="modal-actions"):
                    yield self.cancel_action
                    yield self.confirm_action

    def compose_body(self) -> ComposeResult:
        """Return the modal content widget."""
        yield Static("", classes="modal-body")

    def on_mount(self) -> None:
        """Focus the first interactive control when the modal mounts."""
        focus_targets = self.focus_targets()
        if focus_targets:
            self.set_focus(focus_targets[0])

    def on_click(self, event: events.Click) -> None:
        """Handle clicks on the backdrop and modal action controls."""
        widget = event.widget
        if widget is None or widget.id is None:
            return
        if widget.id == "modal-backdrop":
            event.stop()
            self._dismiss_if_current(self.cancel_result())
            return
        if widget.id in {"modal-close", "modal-cancel", "modal-confirm"}:
            event.stop()
            self._activate_control(widget.id)

    def on_key(self, event: events.Key) -> None:
        """Provide modal-local keyboard navigation for inputs and action statics."""
        if event.key == "up":
            event.stop()
            self._advance_focus(-1)
        elif event.key == "down":
            event.stop()
            self._advance_focus(1)
        elif event.key == "enter" and isinstance(self.app.focused, ModalAction):
            event.stop()
            focused_id = self.app.focused.id
            if focused_id is not None:
                self._activate_control(focused_id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Advance focus when the user submits a text input."""
        event.stop()
        self._advance_focus(1)

    def action_cancel_modal(self) -> None:
        """Dismiss the modal through the shared cancel path."""
        self._dismiss_if_current(self.cancel_result())

    def confirm_result(self) -> object | None:
        """Return the modal result for confirmation."""
        return True

    def cancel_result(self) -> object | None:
        """Return the modal result for cancellation."""
        return None

    def _dismiss_if_current(self, result: object | None) -> None:
        """Dismiss the modal only if it is still the current screen."""
        if self.is_current:
            self.dismiss(result)

    def focus_targets(self) -> Sequence[Widget]:
        """Return the default focus order for modal inputs and actions."""
        targets: list[Widget] = [*self.query(Input), *self.query(ModalAction)]
        return [
            target
            for target in targets
            if not (isinstance(target, ModalAction) and target.disabled)
        ]

    def _advance_focus(self, step: int) -> None:
        """Move focus forward or backward through the modal control order."""
        focus_targets = list(self.focus_targets())
        if not focus_targets:
            return
        current_focus = self.app.focused
        if current_focus not in focus_targets:
            self.set_focus(focus_targets[0 if step > 0 else -1])
            return
        current_index = focus_targets.index(current_focus)
        next_index = (current_index + step) % len(focus_targets)
        self.set_focus(focus_targets[next_index])

    def _activate_control(self, control_id: str) -> None:
        """Run one of the built-in modal controls."""
        if control_id in {"modal-close", "modal-cancel"}:
            self._dismiss_if_current(self.cancel_result())
            return
        if control_id != "modal-confirm" or self.confirm_action.disabled:
            return
        result = self.confirm_result()
        if result is self.KEEP_OPEN:
            return
        self._dismiss_if_current(result)
