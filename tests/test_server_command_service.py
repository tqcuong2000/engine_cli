import unittest

from engine_cli.application import (
    ServerCommandError,
    ServerCommandService,
    ServerInstanceLifecycleService,
    ServerTerminalStore,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.infrastructure.process.managed_process import ManagedProcessHandle


class _StubProcessManager:
    def __init__(self) -> None:
        self.commands: list[tuple[ManagedProcessHandle, str]] = []

    def send_command(self, handle: ManagedProcessHandle, command: str) -> None:
        self.commands.append((handle, command))


class TestServerCommandService(unittest.TestCase):
    def test_send_rejects_empty_command(self):
        lifecycle = ServerInstanceLifecycleService()
        service = ServerCommandService(lifecycle, ServerTerminalStore())
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.RUNNING,
        )

        with self.assertRaises(ServerCommandError):
            service.send(server, "   ")

    def test_send_rejects_when_server_is_not_running(self):
        lifecycle = ServerInstanceLifecycleService()
        service = ServerCommandService(lifecycle, ServerTerminalStore())
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.STOPPED,
        )

        with self.assertRaises(ServerCommandError):
            service.send(server, "list")

    def test_send_writes_to_process_manager_and_echoes_command(self):
        lifecycle = ServerInstanceLifecycleService()
        process_manager = _StubProcessManager()
        lifecycle.process_manager = process_manager
        terminal_store = ServerTerminalStore()
        service = ServerCommandService(lifecycle, terminal_store)
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar --nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.RUNNING,
        )
        handle = ManagedProcessHandle(process=object(), command=server.command)  # type: ignore[arg-type]
        lifecycle._handles[server.server_instance_id] = handle

        service.send(server, "say hello")

        self.assertEqual(process_manager.commands, [(handle, "say hello")])
        terminal_lines = terminal_store.get_buffer(server.server_instance_id).snapshot()
        self.assertEqual(terminal_lines[-1].raw, "> say hello")
