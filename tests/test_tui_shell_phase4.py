import unittest
from typing import Any, cast

from engine_cli.application import (
    ServerInstanceManager,
    SessionCoordinator,
    ServerTerminalStore,
    SessionContext,
)
from engine_cli.application import InvalidModeSwitchError
from engine_cli.domain import OperatingMode
from engine_cli.interfaces.tui.layout.body import Body
from engine_cli.interfaces.tui.layout.footer import Footer
from engine_cli.interfaces.tui.layout.header import Header
from engine_cli.interfaces.tui.layout.panel import Panel


class TestTuiShellPhase4(unittest.TestCase):
    def test_shell_widgets_share_one_session_context(self):
        session = SessionContext()
        coordinator = SessionCoordinator(session)
        terminal_store = ServerTerminalStore()
        server_manager = ServerInstanceManager()

        header = Header(session, coordinator)
        body = Body(session, terminal_store, coordinator)
        panel = Panel(session, server_manager, session_coordinator=coordinator)
        footer = Footer(session, coordinator)

        self.assertIs(header.session_context, session)
        self.assertIs(header.session_coordinator, coordinator)
        self.assertIs(body.session_context, session)
        self.assertIs(body.session_coordinator, coordinator)
        self.assertIs(body.terminal_store, terminal_store)
        self.assertIs(panel.session_context, session)
        self.assertIs(panel.session_coordinator, coordinator)
        self.assertIs(panel.server_manager, server_manager)
        self.assertIs(footer.session_context, session)
        self.assertIs(footer.session_coordinator, coordinator)

    def test_mode_change_updates_header_and_panel_contract(self):
        session = SessionContext()
        coordinator = SessionCoordinator(session)
        header = Header(session, coordinator)
        panel = Panel(session, ServerInstanceManager(), session_coordinator=coordinator)
        self.assertEqual(header.badge_text, "BASE")
        self.assertEqual(
            [tab.title for tab in panel.tabs],
            ["Context", "Servers", "Actions", "Tasks"],
        )

        session.select_server("srv-1")
        session.switch_mode(OperatingMode.SERVER)

        self.assertEqual(header.badge_text, "SERVER")
        self.assertEqual(header.title_text, "Engine // srv-1")
        self.assertEqual(
            [tab.title for tab in panel.tabs],
            ["Context", "Servers", "Actions", "Tasks"],
        )

    def test_panel_navigation_methods_do_not_leave_valid_tab_range(self):
        session = SessionContext()
        panel = Panel(session, ServerInstanceManager())

        for _ in range(20):
            panel.next_tab()
        self.assertLess(panel.active_tab_index, len(panel.tabs))

        for _ in range(20):
            panel.previous_tab()
        self.assertLess(panel.active_tab_index, len(panel.tabs))

    def test_session_widgets_refresh_on_coordinator_updates(self):
        session = SessionContext()
        coordinator = SessionCoordinator(session)
        terminal_store = ServerTerminalStore()
        server_manager = ServerInstanceManager()
        widgets = [
            Header(session, coordinator),
            Body(session, terminal_store, coordinator),
            Panel(session, server_manager, session_coordinator=coordinator),
            Footer(session, coordinator),
        ]
        refresh_calls: dict[object, list[dict[str, object]]] = {widget: [] for widget in widgets}

        for widget in widgets:
            cast(Any, widget).refresh = (
                lambda *args, _widget=widget, **kwargs: refresh_calls[_widget].append(kwargs)
            )
            widget.on_mount()

        coordinator.select_server("srv-1")
        coordinator.switch_mode(OperatingMode.SERVER)

        for widget in widgets:
            self.assertGreaterEqual(len(refresh_calls[widget]), 2)
            self.assertTrue(
                all(call == {"recompose": True} for call in refresh_calls[widget])
            )

    def test_invalid_session_change_does_not_refresh_widgets(self):
        session = SessionContext()
        coordinator = SessionCoordinator(session)
        header = Header(session, coordinator)
        refresh_calls: list[dict[str, object]] = []
        cast(Any, header).refresh = lambda *args, **kwargs: refresh_calls.append(kwargs)
        header.on_mount()

        with self.assertRaises(InvalidModeSwitchError):
            coordinator.switch_mode(OperatingMode.SERVER)

        self.assertEqual(refresh_calls, [])

    def test_session_widgets_unsubscribe_on_unmount(self):
        session = SessionContext()
        coordinator = SessionCoordinator(session)
        header = Header(session, coordinator)
        refresh_calls: list[dict[str, object]] = []
        cast(Any, header).refresh = lambda *args, **kwargs: refresh_calls.append(kwargs)
        header.on_mount()
        header.on_unmount()

        coordinator.set_agent_profile("profile-1")

        self.assertEqual(refresh_calls, [])
