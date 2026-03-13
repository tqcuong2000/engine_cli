import unittest

from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.app import EngineCli


class TestApp(unittest.TestCase):
    def test_app_init(self):
        app = EngineCli()
        self.assertEqual(app.title, "EngineCli")

    def test_app_bindings_include_mode_and_panel_controls(self):
        app = EngineCli()
        binding_keys = {binding[0] for binding in app.BINDINGS}
        self.assertTrue({"b", "s", "p", "[", "]"}.issubset(binding_keys))

    def test_base_mode_action_updates_session_context(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_base_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)

    def test_server_mode_action_selects_demo_server_and_switches_mode(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_server_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)
        self.assertEqual(app.session_context.active_server_instance_id, "demo-server")

    def test_datapack_mode_action_selects_demo_server_and_switches_mode(self):
        app = EngineCli()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_datapack_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.DATAPACK)
        self.assertEqual(app.session_context.active_server_instance_id, "demo-server")


if __name__ == "__main__":
    unittest.main()
