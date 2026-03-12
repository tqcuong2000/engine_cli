from textual.app import App, ComposeResult

from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header
from engine_cli.interfaces.tui.theme.engine_dark import ENGINE_THEME


class EngineCli(App):
    """A basic Textual application template."""

    CSS_PATH = "../../resources/app.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.register_theme(ENGINE_THEME)
        self.theme = "engine_dark"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


def run():
    app = EngineCli()
    app.run()


if __name__ == "__main__":
    run()
