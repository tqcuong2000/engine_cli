import unittest

from engine_cli.application import ServerInstanceManager, SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.layout.panel import Panel
from engine_cli.interfaces.tui.panel.tabs import get_panel_tabs


class TestTuiPanelPhase2(unittest.TestCase):
    def test_panel_cycles_tabs_forward_and_backward(self):
        session = SessionContext()
        panel = Panel(session, ServerInstanceManager())

        self.assertEqual(panel.active_tab.title, "Context")

        panel.next_tab()
        self.assertEqual(panel.active_tab.title, "Servers")

        panel.previous_tab()
        self.assertEqual(panel.active_tab.title, "Context")

    def test_panel_tab_set_changes_with_mode(self):
        session = SessionContext()
        base_panel = Panel(session, ServerInstanceManager())
        self.assertEqual(
            [tab.title for tab in base_panel.tabs],
            ["Context", "Servers", "Actions", "Tasks"],
        )

        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        server_panel = Panel(session, ServerInstanceManager())
        self.assertEqual(
            [tab.title for tab in server_panel.tabs],
            ["Context", "Servers", "Actions", "Tasks"],
        )

    def test_panel_resets_invalid_tab_after_mode_switch(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        panel = Panel(session, ServerInstanceManager())
        panel.active_tab_index = 99

        session.switch_mode(OperatingMode.BASE)
        panel._ensure_valid_index()

        self.assertEqual(panel.active_tab_index, 0)
        self.assertEqual(panel.active_tab.title, "Context")

    def test_get_panel_tabs_for_datapack_matches_server_shape(self):
        self.assertEqual(
            [tab.title for tab in get_panel_tabs(OperatingMode.DATAPACK)],
            ["Context", "Servers", "Actions", "Tasks"],
        )
