import unittest

from engine_cli.domain import OperatingMode
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.interfaces.tui.app import EngineCli


class TestApp(unittest.TestCase):
    def test_app_init(self):
        app = EngineCli()
        self.assertEqual(app.title, "EngineCli")
        self.assertIsNotNone(app.terminal_store)
        self.assertIsNotNone(app.server_manager)

    def test_app_bindings_include_mode_and_panel_controls(self):
        app = EngineCli()
        binding_keys = {binding[0] for binding in app.BINDINGS}
        self.assertTrue({"b", "s", "p", "[", "]"}.issubset(binding_keys))

    def test_base_mode_action_updates_session_context(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_base_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)

    def test_server_mode_action_requires_selected_server(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_server_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertIsNone(app.session_context.active_server_instance_id)

    def test_datapack_mode_action_requires_selected_server(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_datapack_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertIsNone(app.session_context.active_server_instance_id)

    def test_server_mode_action_switches_with_real_selected_server(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")

        app.action_set_server_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)

    def test_server_selection_updates_session_context(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)

        app._handle_server_select("srv-1")

        self.assertEqual(app.session_context.active_server_instance_id, "srv-1")
        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)

    def test_start_server_uses_repository_backed_instance(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        captured: list[ServerInstance] = []
        app.lifecycle_service.start = lambda instance: captured.append(instance) or None

        app._handle_start_server()

        self.assertEqual(captured, [server])
        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)

    def test_start_server_validates_draft_server_before_start(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.DRAFT,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        called_with: list[ServerInstance] = []
        app.lifecycle_service.start = lambda instance: called_with.append(instance) or None

        app._handle_start_server()

        self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.CONFIGURED)
        self.assertEqual(called_with, [server])


if __name__ == "__main__":
    unittest.main()
