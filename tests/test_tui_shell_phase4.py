import unittest

from engine_cli.application import SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.layout.body import Body
from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header
from engine_cli.interfaces.tui.layout.panel import Panel


class TestTuiShellPhase4(unittest.TestCase):
    def test_shell_widgets_share_one_session_context(self):
        session = SessionContext()

        header = Header(session)
        body = Body(session)
        panel = Panel(session)
        footer = Footer(session)

        self.assertIs(header.session_context, session)
        self.assertIs(body.session_context, session)
        self.assertIs(panel.session_context, session)
        self.assertIs(footer.session_context, session)

    def test_mode_change_updates_header_and_panel_contract(self):
        session = SessionContext()
        header = Header(session)
        panel = Panel(session)
        self.assertEqual(header.badge_text, "BASE")
        self.assertEqual([tab.title for tab in panel.tabs], ["Context", "Actions", "Tasks"])

        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)

        self.assertEqual(header.badge_text, "SERVER")
        self.assertEqual(header.title_text, "Engine // srv-1")
        self.assertEqual(
            [tab.title for tab in panel.tabs],
            ["Context", "Actions", "Tasks"],
        )

    def test_panel_navigation_methods_do_not_leave_valid_tab_range(self):
        session = SessionContext()
        panel = Panel(session)

        for _ in range(20):
            panel.next_tab()
        self.assertLess(panel.active_tab_index, len(panel.tabs))

        for _ in range(20):
            panel.previous_tab()
        self.assertLess(panel.active_tab_index, len(panel.tabs))
