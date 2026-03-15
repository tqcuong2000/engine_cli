import unittest

from engine_cli.application import (
    AgentProfileSelectionService,
    IncompatibleAgentProfileError,
    SessionContext,
    UnknownAgentProfileError,
)
from engine_cli.config import ResolvedSettings
from engine_cli.domain import OperatingMode


class TestAgentProfileSelectionService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AgentProfileSelectionService()
        self.settings = ResolvedSettings.from_mapping(
            {
                "default_agent_profiles": {
                    "base": "base-default",
                    "server": "server-default",
                    "datapack": "datapack-default",
                },
                "agent_profiles": [
                    {
                        "agent_profile_id": "base-default",
                        "name": "Base Assistant",
                        "mode": "base",
                        "agent_kind": "system_assistant",
                    },
                    {
                        "agent_profile_id": "base-alt",
                        "name": "Base Alternate",
                        "mode": "base",
                        "agent_kind": "system_assistant",
                    },
                    {
                        "agent_profile_id": "server-default",
                        "name": "Server Ops",
                        "mode": "server",
                        "agent_kind": "server_ops",
                    },
                    {
                        "agent_profile_id": "datapack-default",
                        "name": "Datapack Dev",
                        "mode": "datapack",
                        "agent_kind": "datapack_dev",
                    },
                ],
            }
        )

    def test_resolve_effective_profile_id_uses_mode_default_when_unset(self) -> None:
        session_context = SessionContext()

        profile_id = self.service.resolve_effective_profile_id(
            session_context=session_context,
            settings=self.settings,
        )

        self.assertEqual(profile_id, "base-default")

    def test_resolve_effective_profile_id_keeps_compatible_selected_profile(self) -> None:
        session_context = SessionContext()
        session_context.set_agent_profile("base-alt")

        profile_id = self.service.resolve_effective_profile_id(
            session_context=session_context,
            settings=self.settings,
        )

        self.assertEqual(profile_id, "base-alt")

    def test_resolve_effective_profile_id_replaces_incompatible_profile_on_mode_change(
        self,
    ) -> None:
        session_context = SessionContext()
        session_context.select_server("srv-1")
        session_context.set_agent_profile("base-default")
        session_context.switch_mode(OperatingMode.SERVER)

        profile_id = self.service.resolve_effective_profile_id(
            session_context=session_context,
            settings=self.settings,
        )

        self.assertEqual(profile_id, "server-default")

    def test_select_profile_updates_session_for_compatible_profile(self) -> None:
        session_context = SessionContext()

        selected_profile_id = self.service.select_profile(
            session_context=session_context,
            settings=self.settings,
            agent_profile_id="base-alt",
        )

        self.assertEqual(selected_profile_id, "base-alt")
        self.assertEqual(session_context.active_agent_profile_id, "base-alt")

    def test_select_profile_rejects_unknown_profile(self) -> None:
        session_context = SessionContext()

        with self.assertRaises(UnknownAgentProfileError):
            self.service.select_profile(
                session_context=session_context,
                settings=self.settings,
                agent_profile_id="missing",
            )

    def test_select_profile_rejects_incompatible_profile(self) -> None:
        session_context = SessionContext()

        with self.assertRaises(IncompatibleAgentProfileError):
            self.service.select_profile(
                session_context=session_context,
                settings=self.settings,
                agent_profile_id="server-default",
            )
