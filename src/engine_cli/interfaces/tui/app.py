from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical

from engine_cli.application import InvalidModeSwitchError, SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.layout.body import Body
from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header
from engine_cli.interfaces.tui.layout.panel import Panel
from engine_cli.interfaces.tui.theme.engine_dark import ENGINE_THEME


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

    def __init__(self) -> None:
        super().__init__()
        self.session_context = SessionContext()

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
                    yield Body(self.session_context)
                with Container(classes="app-right"):
                    yield Panel(self.session_context)
            with Container(classes="app-bottom"):
                yield Footer(self.session_context)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_set_base_mode(self) -> None:
        self.session_context.switch_mode(OperatingMode.BASE)
        self._refresh_mode_aware_widgets()

    def action_set_server_mode(self) -> None:
        self._switch_with_demo_server(OperatingMode.SERVER)

    def action_set_datapack_mode(self) -> None:
        self._switch_with_demo_server(OperatingMode.DATAPACK)

    def action_previous_panel_tab(self) -> None:
        self.query_one(Panel).previous_tab()

    def action_next_panel_tab(self) -> None:
        self.query_one(Panel).next_tab()

    def _switch_with_demo_server(self, mode: OperatingMode) -> None:
        if self.session_context.active_server_instance_id is None:
            self.session_context.select_server("demo-server")
        try:
            self.session_context.switch_mode(mode)
        except InvalidModeSwitchError:
            return
        self._refresh_mode_aware_widgets()

    def _refresh_mode_aware_widgets(self) -> None:
        self.query_one(Header).refresh(recompose=True)
        self.query_one(Body).refresh(recompose=True)
        self.query_one(Panel).refresh(recompose=True)
        self.query_one(Footer).refresh(recompose=True)


def run():
    app = EngineCli()
    app.run()


if __name__ == "__main__":
    run()
