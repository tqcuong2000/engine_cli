import unittest
from unittest import mock

from engine_cli.application.lifecycle import (
    ServerInstanceLifecycleService,
    ServerRuntimeStateResolver,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState


class TestServerRuntimeStateResolver(unittest.TestCase):
    def test_overlay_overlays_running_state_when_handle_exists(self) -> None:
        lifecycle_service = ServerInstanceLifecycleService()
        lifecycle_service.get_handle = mock.Mock(return_value=object())  # type: ignore[method-assign]
        resolver = ServerRuntimeStateResolver(lifecycle_service)
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )

        overlaid = resolver.overlay(server)

        self.assertIsNot(overlaid, server)
        self.assertEqual(overlaid.lifecycle_state, ServerInstanceLifecycleState.RUNNING)
        self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.CONFIGURED)

    def test_overlay_preserves_persisted_state_without_handle(self) -> None:
        lifecycle_service = ServerInstanceLifecycleService()
        resolver = ServerRuntimeStateResolver(lifecycle_service)
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )

        overlaid = resolver.overlay(server)

        self.assertIsNot(overlaid, server)
        self.assertEqual(overlaid.lifecycle_state, ServerInstanceLifecycleState.CONFIGURED)
        self.assertEqual(server.lifecycle_state, ServerInstanceLifecycleState.CONFIGURED)
