from textual.app import ComposeResult
from textual.widgets import Footer as TextualFooter


class Footer(TextualFooter):
    """
    A custom Footer widget for the Engine CLI application.
    Inherits from the standard Textual Footer to provide key binding displays.
    """

    def compose(self) -> ComposeResult:
        return super().compose()
