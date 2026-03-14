import tempfile
from pathlib import Path
import unittest

from engine_cli.application import ServerInstanceManager, SessionContext
from engine_cli.interfaces.tui.components import PanelTabDefinition, TabbedPanelFrame
from engine_cli.interfaces.tui.modals import AddServerModalScreen, ConfirmModalScreen
from engine_cli.interfaces.tui.panel.context import PanelViewContext
from engine_cli.interfaces.tui.panel.context_panel import ContextPanelView
from engine_cli.interfaces.tui.panel.servers_panel import ServersPanelView


class _FakeTabbedPanel(TabbedPanelFrame):
    @property
    def tabs(self) -> tuple[PanelTabDefinition, ...]:
        return (
            PanelTabDefinition("one", "One", ContextPanelView),
            PanelTabDefinition("two", "Two", ContextPanelView),
        )


class TestTuiPrimitives(unittest.TestCase):
    def test_tabbed_panel_frame_cycles_and_preserves_valid_index(self):
        context = PanelViewContext(
            session_context=SessionContext(),
            server_manager=ServerInstanceManager(),
        )
        panel = _FakeTabbedPanel(context)

        self.assertEqual(panel.active_tab.title, "One")
        panel.next_tab()
        self.assertEqual(panel.active_tab.title, "Two")
        panel.active_tab_index = 99
        panel._ensure_valid_index()
        self.assertEqual(panel.active_tab_index, 0)

    def test_confirm_modal_screen_returns_expected_default_results(self):
        modal = ConfirmModalScreen("Remove", "Remove server?")

        self.assertTrue(modal.confirm_result())
        self.assertIsNone(modal.cancel_result())

    def test_add_server_modal_exposes_add_confirmation_label(self):
        modal = AddServerModalScreen(ServerInstanceManager())

        self.assertEqual(modal.confirm_label, "Add")

    def test_add_server_modal_disables_submit_for_invalid_server_root(self):
        modal = AddServerModalScreen(ServerInstanceManager())
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            modal.set_form_values(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )

            self.assertFalse(modal.can_submit)

    def test_add_server_modal_populates_command_from_detected_root_jar(self):
        manager = ServerInstanceManager()
        modal = AddServerModalScreen(manager)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "server.properties").write_text("motd=Lobby\n", encoding="utf-8")
            (root / "fabric.jar").write_text("", encoding="utf-8")
            modal.set_form_values(name="Lobby", location=str(root), command="")

            modal.populate_command_from_location()

            self.assertEqual(
                modal.command_value,
                "java -Xms2G -Xmx2G -Xmn512m -jar fabric.jar --nogui",
            )

    def test_add_server_modal_create_server_uses_manager_import(self):
        manager = ServerInstanceManager()
        modal = AddServerModalScreen(manager)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs").mkdir()
            (root / "versions" / "1.21.11").mkdir(parents=True)
            (root / "server.properties").write_text("motd=Lobby\n", encoding="utf-8")
            (root / "logs" / "latest.log").write_text(
                "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
                encoding="utf-8",
            )
            (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
                "",
                encoding="utf-8",
            )
            modal.set_form_values(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )

            server = modal.create_server()

            self.assertEqual(server.name, "Lobby")
            self.assertEqual(len(manager.list_servers()), 1)

    def test_servers_panel_view_exposes_server_entry_data(self):
        manager = ServerInstanceManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs").mkdir()
            (root / "versions" / "1.21.11").mkdir(parents=True)
            (root / "server.properties").write_text("motd=Lobby\n", encoding="utf-8")
            (root / "logs" / "latest.log").write_text(
                "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
                encoding="utf-8",
            )
            (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
                "",
                encoding="utf-8",
            )
            server = manager.import_server(
                name="Lobby",
                location=str(root),
                command="java -jar fabric.jar --nogui",
            )
            session = SessionContext(active_server_instance_id=server.server_instance_id)
            view = ServersPanelView(
                PanelViewContext(
                    session_context=session,
                    server_manager=manager,
                )
            )

            entries = view.server_entries()

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["server_instance_id"], server.server_instance_id)
            self.assertIn("Lobby", entries[0]["label"])
