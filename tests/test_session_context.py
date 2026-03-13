import unittest

from engine_cli.application import InvalidModeSwitchError, SessionContext
from engine_cli.domain import OperatingMode


class TestSessionContext(unittest.TestCase):
    def test_default_state(self):
        context = SessionContext()
        self.assertEqual(context.mode, OperatingMode.BASE)
        self.assertIsNone(context.active_server_instance_id)
        self.assertIsNone(context.active_agent_profile_id)

    def test_valid_switch_to_server_mode_with_selected_server(self):
        context = SessionContext()
        context.select_server("srv-1")
        context.switch_mode(OperatingMode.SERVER)
        self.assertEqual(context.mode, OperatingMode.SERVER)

    def test_valid_switch_to_datapack_mode_with_selected_server(self):
        context = SessionContext()
        context.select_server("srv-1")
        context.switch_mode(OperatingMode.DATAPACK)
        self.assertEqual(context.mode, OperatingMode.DATAPACK)

    def test_invalid_switch_to_server_mode_without_selected_server(self):
        context = SessionContext()
        with self.assertRaises(InvalidModeSwitchError):
            context.switch_mode(OperatingMode.SERVER)

    def test_invalid_switch_to_datapack_mode_without_selected_server(self):
        context = SessionContext()
        with self.assertRaises(InvalidModeSwitchError):
            context.switch_mode(OperatingMode.DATAPACK)

    def test_clearing_server_selection_from_server_mode_falls_back_to_base(self):
        context = SessionContext()
        context.select_server("srv-1")
        context.switch_mode(OperatingMode.SERVER)
        context.clear_server_selection()
        self.assertEqual(context.mode, OperatingMode.BASE)
        self.assertIsNone(context.active_server_instance_id)

    def test_clearing_server_selection_from_datapack_mode_falls_back_to_base(self):
        context = SessionContext()
        context.select_server("srv-1")
        context.switch_mode(OperatingMode.DATAPACK)
        context.clear_server_selection()
        self.assertEqual(context.mode, OperatingMode.BASE)
        self.assertIsNone(context.active_server_instance_id)

    def test_set_agent_profile(self):
        context = SessionContext()
        context.set_agent_profile("profile-1")
        self.assertEqual(context.active_agent_profile_id, "profile-1")
