import tempfile
from pathlib import Path
import unittest

from engine_cli.application import ServerTerminalStore, SessionContext
from engine_cli.application.composition import create_app_runtime
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.app import EngineCli
from engine_cli.interfaces.tui.body.conversation import ConversationBody
from engine_cli.interfaces.tui.body.terminal import TerminalBody
from engine_cli.interfaces.tui.footer.prompt_footer import PromptFooter
from engine_cli.interfaces.tui.footer.terminal_footer import TerminalFooter
from engine_cli.interfaces.tui.layout.body import Body
from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header


class TestTuiShellPhase1(unittest.TestCase):
    def test_app_has_session_context_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = EngineCli(create_app_runtime(app_root=Path(temp_dir)))
            self.assertEqual(app.session_context.mode, OperatingMode.BASE)
            self.assertIsNone(app.session_context.active_server_instance_id)
            self.assertEqual(
                app.session_context.active_agent_profile_id,
                "base-default",
            )

    def test_body_renders_conversation_in_base_mode(self):
        session = SessionContext()
        body = Body(session, ServerTerminalStore())
        child = next(iter(body.compose()))
        self.assertIsInstance(child, ConversationBody)

    def test_body_renders_terminal_in_server_mode(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        body = Body(session, ServerTerminalStore())
        child = next(iter(body.compose()))
        self.assertIsInstance(child, TerminalBody)

    def test_body_renders_conversation_in_datapack_mode(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.DATAPACK)
        body = Body(session, ServerTerminalStore())
        child = next(iter(body.compose()))
        self.assertIsInstance(child, ConversationBody)

    def test_footer_renders_prompt_footer_in_chat_modes(self):
        session = SessionContext()
        footer = Footer(session)
        child = next(iter(footer.compose()))
        self.assertIsInstance(child, PromptFooter)

        session.select_server("srv-1")
        session.switch_mode(OperatingMode.DATAPACK)
        footer = Footer(session)
        child = next(iter(footer.compose()))
        self.assertIsInstance(child, PromptFooter)

    def test_footer_renders_terminal_footer_in_server_mode(self):
        session = SessionContext()
        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)
        footer = Footer(session)
        child = next(iter(footer.compose()))
        self.assertIsInstance(child, TerminalFooter)

    def test_header_reflects_mode_and_context(self):
        session = SessionContext()
        header = Header(session)
        self.assertEqual(header.badge_text, "BASE")
        self.assertEqual(header.title_text, "Engine // No server selected")
        self.assertEqual(header.context_text, "profile: default-profile")

        session.select_server("srv-1")
        session.set_agent_profile("profile-1")
        session.switch_mode(OperatingMode.SERVER)
        header = Header(session)
        self.assertEqual(header.badge_text, "SERVER")
        self.assertEqual(header.title_text, "Engine // srv-1")
        self.assertEqual(header.context_text, "profile: profile-1")
