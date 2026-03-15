import unittest

from engine_cli.application import (
    InvalidModeSwitchError,
    SessionContext,
    SessionCoordinator,
    SessionSnapshot,
)
from engine_cli.domain import OperatingMode


class TestSessionCoordinator(unittest.TestCase):
    def test_snapshot_reflects_current_context_state(self) -> None:
        context = SessionContext()
        coordinator = SessionCoordinator(context)

        snapshot = coordinator.snapshot()

        self.assertEqual(
            snapshot,
            SessionSnapshot(
                mode=OperatingMode.BASE,
                active_server_instance_id=None,
                active_agent_profile_id=None,
            ),
        )

    def test_context_remains_plain_state_object(self) -> None:
        context = SessionContext()

        self.assertFalse(hasattr(context, "subscribe"))
        self.assertFalse(hasattr(context, "snapshot"))

    def test_switch_mode_notifies_listener_after_success(self) -> None:
        context = SessionContext()
        coordinator = SessionCoordinator(context)
        coordinator.select_server("srv-1")
        received: list[SessionSnapshot] = []
        coordinator.subscribe(received.append)

        snapshot = coordinator.switch_mode(OperatingMode.SERVER)

        self.assertEqual(snapshot.mode, OperatingMode.SERVER)
        self.assertEqual(received, [snapshot])

    def test_invalid_switch_does_not_notify_listener(self) -> None:
        coordinator = SessionCoordinator(SessionContext())
        received: list[SessionSnapshot] = []
        coordinator.subscribe(received.append)

        with self.assertRaises(InvalidModeSwitchError):
            coordinator.switch_mode(OperatingMode.SERVER)

        self.assertEqual(received, [])

    def test_clear_server_selection_notifies_base_fallback(self) -> None:
        coordinator = SessionCoordinator(SessionContext())
        coordinator.select_server("srv-1")
        coordinator.switch_mode(OperatingMode.SERVER)
        received: list[SessionSnapshot] = []
        coordinator.subscribe(received.append)

        snapshot = coordinator.clear_server_selection()

        self.assertEqual(snapshot.mode, OperatingMode.BASE)
        self.assertIsNone(snapshot.active_server_instance_id)
        self.assertEqual(received, [snapshot])

    def test_set_agent_profile_notifies_listener(self) -> None:
        coordinator = SessionCoordinator(SessionContext())
        received: list[SessionSnapshot] = []
        coordinator.subscribe(received.append)

        snapshot = coordinator.set_agent_profile("profile-1")

        self.assertEqual(snapshot.active_agent_profile_id, "profile-1")
        self.assertEqual(received, [snapshot])

    def test_unsubscribe_stops_future_notifications(self) -> None:
        coordinator = SessionCoordinator(SessionContext())
        received: list[SessionSnapshot] = []
        unsubscribe = coordinator.subscribe(received.append)

        coordinator.select_server("srv-1")
        unsubscribe()
        coordinator.set_agent_profile("profile-1")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].active_server_instance_id, "srv-1")
