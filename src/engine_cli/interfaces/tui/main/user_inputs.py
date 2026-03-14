from textual.app import ComposeResult
from textual import events
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, TextArea


class UserInputs(Widget):
    class Submitted(Message):
        """Message emitted when the user submits the current input value."""

        def __init__(self, control: "UserInputs", value: str) -> None:
            super().__init__()
            self.input_widget = control
            self.value = value

    def __init__(self, placeholder: str, button_label: str) -> None:
        super().__init__()
        self.placeholder = placeholder
        self.button_label = button_label
        self.text_input = TextArea(classes="text-input", placeholder=self.placeholder)
        self.send_button = Static(self.button_label, id="user-input-submit", classes="send-btn")

    def compose(self) -> ComposeResult:
        yield self.text_input
        yield self.send_button

    def on_click(self, event: events.Click) -> None:
        """Submit the current text when the send control is clicked."""
        widget = event.widget
        if widget is self.send_button:
            event.stop()
            self.submit()

    def on_key(self, event: events.Key) -> None:
        """Treat Enter as submit while the text input is focused."""
        if event.key != "enter" or self.app.focused is not self.text_input:
            return
        event.stop()
        self.submit()

    def submit(self) -> None:
        """Post the current input value to the parent widget."""
        self.post_message(self.Submitted(self, self.value))

    @property
    def value(self) -> str:
        """Return the current text area contents."""
        return self.text_input.text

    def clear(self) -> None:
        """Clear the current text input."""
        self.text_input.load_text("")
