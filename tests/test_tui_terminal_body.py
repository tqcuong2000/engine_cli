import unittest

from engine_cli.application import ServerTerminalStore, SessionContext
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.body.terminal import TerminalBody


class TestTerminalBody(unittest.TestCase):
    def test_terminal_body_renders_buffered_lines_for_active_server(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        store = ServerTerminalStore()
        body = TerminalBody(session, store)

        buffer = store.get_buffer("srv-1")
        buffer.append("[22:38:09] [Server thread/INFO]: ready")

        body.refresh_logs()

        self.assertIn("ready", body.rendered_text)

    def test_terminal_body_resets_when_active_server_changes(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        store = ServerTerminalStore()
        first_buffer = store.get_buffer("srv-1")
        first_buffer.append("first server line")
        second_buffer = store.get_buffer("srv-2")
        second_buffer.append("second server line")
        body = TerminalBody(session, store)

        body.refresh_logs()
        session.select_server("srv-2")
        body.refresh_logs()

        self.assertIn("second server line", body.rendered_text)
        self.assertNotIn("first server line", body.rendered_text)
