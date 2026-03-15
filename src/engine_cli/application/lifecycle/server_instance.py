from dataclasses import replace
from time import monotonic, sleep

from engine_cli.application.execution import ExecutionService
from engine_cli.application.lifecycle.errors import (
    ServerInstanceLifecycleError,
    ServerInstanceValidationError,
)
from engine_cli.application.lifecycle.process_contract import (
    NullProcessManager,
    ProcessHandle,
    ProcessManager,
)
from engine_cli.application.server_instances import (
    InMemoryServerCatalog,
    ServerInstanceRepository,
)
from engine_cli.application.terminal import ServerTerminalStore
from engine_cli.domain import (
    ServerInstance,
    ServerInstanceLifecycleState,
    TaskRun,
    TaskStatus,
    TaskTargetType,
)


class ServerInstanceLifecycleService:
    """Orchestrates server state transitions and manages process lifecycles."""

    def __init__(
        self,
        execution_service: ExecutionService | None = None,
        process_manager: ProcessManager | None = None,
        server_catalog: ServerInstanceRepository | None = None,
        terminal_store: ServerTerminalStore | None = None,
        observation_timeout: float = 1.0,
        poll_interval: float = 0.05,
    ) -> None:
        """Initialize the service with execution and process management dependencies."""
        self.execution_service = execution_service or ExecutionService()
        self.process_manager = process_manager or NullProcessManager()
        self.server_catalog = server_catalog or InMemoryServerCatalog()
        self.terminal_store = terminal_store or ServerTerminalStore()
        self.observation_timeout = observation_timeout
        self.poll_interval = poll_interval
        self._handles: dict[str, ProcessHandle] = {}

    def validate(self, server: ServerInstance) -> ServerInstance:
        """Verify server inputs and transition from DRAFT to CONFIGURED if valid."""
        if not server.location:
            raise ServerInstanceValidationError("Server location is required.")
        if not server.command.strip():
            raise ServerInstanceValidationError("Server command is required.")
        if server.lifecycle_state not in (
            ServerInstanceLifecycleState.DRAFT,
            ServerInstanceLifecycleState.FAILED,
        ):
            return server
        server.lifecycle_state = ServerInstanceLifecycleState.CONFIGURED
        self.server_catalog.save_server(server)
        return server

    def start(self, server: ServerInstance) -> TaskRun:
        """Execute a start task and transition the server to RUNNING if success."""
        if server.lifecycle_state not in (
            ServerInstanceLifecycleState.CONFIGURED,
            ServerInstanceLifecycleState.STOPPED,
        ):
            raise ServerInstanceLifecycleError(
                f"Cannot start server from state {server.lifecycle_state.value!r}."
            )

        server.lifecycle_state = ServerInstanceLifecycleState.STARTING

        def _start_server_task() -> None:
            terminal_buffer = self.terminal_store.get_buffer(server.server_instance_id)
            terminal_buffer.clear()
            handle = self.process_manager.start(server.command, server.location)
            handle.set_log_streamer(self.process_manager.create_log_streamer(
                handle,
                terminal_buffer.append,
            ))
            log_streamer = handle.get_log_streamer()
            assert log_streamer is not None
            log_streamer.start()
            if not self._wait_for_state(handle, desired_running=True):
                self._shutdown_handle(handle)
                raise ServerInstanceLifecycleError(
                    "Server process did not remain running long enough to confirm startup."
                )
            self._handles[server.server_instance_id] = handle

        result = self.execution_service.run_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id=server.server_instance_id,
            task_operation=_start_server_task,
        )
        if result.final_status is TaskStatus.COMPLETED:
            server.lifecycle_state = ServerInstanceLifecycleState.RUNNING
            self._save_recovery_state(
                server,
                ServerInstanceLifecycleState.CONFIGURED,
            )
        else:
            server.lifecycle_state = ServerInstanceLifecycleState.FAILED
            self.server_catalog.save_server(server)
        task = self.execution_service.get_task(result.task_run_id)
        if task is None:
            raise ServerInstanceLifecycleError("Start task record was not persisted.")
        return task

    def stop(self, server: ServerInstance) -> TaskRun:
        """Execute a stop task and transition the server to STOPPED if success."""
        if server.lifecycle_state is not ServerInstanceLifecycleState.RUNNING:
            raise ServerInstanceLifecycleError(
                f"Cannot stop server from state {server.lifecycle_state.value!r}."
            )
        handle = self._handles.get(server.server_instance_id)
        if handle is None:
            raise ServerInstanceLifecycleError(
                "Cannot stop server without an active process handle."
            )

        server.lifecycle_state = ServerInstanceLifecycleState.STOPPING

        def _stop_server_task() -> None:
            self._shutdown_handle(handle)
            if not self._wait_for_state(handle, desired_running=False):
                raise ServerInstanceLifecycleError(
                    "Server process did not stop within the observation window."
                )
            self._handles.pop(server.server_instance_id, None)

        result = self.execution_service.run_task(
            task_kind="server_instance.stop",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id=server.server_instance_id,
            task_operation=_stop_server_task,
        )
        if result.final_status is TaskStatus.COMPLETED:
            server.lifecycle_state = ServerInstanceLifecycleState.STOPPED
            self.server_catalog.save_server(server)
        else:
            server.lifecycle_state = ServerInstanceLifecycleState.FAILED
            self.server_catalog.save_server(server)
        task = self.execution_service.get_task(result.task_run_id)
        if task is None:
            raise ServerInstanceLifecycleError("Stop task record was not persisted.")
        return task

    def get_handle(self, server_instance_id: str) -> ProcessHandle | None:
        """Return the active runtime handle for a managed server, if one exists."""
        return self._handles.get(server_instance_id)

    def _wait_for_state(
        self,
        handle: ProcessHandle,
        *,
        desired_running: bool,
    ) -> bool:
        """Poll the process state until the desired condition is met or timeout occurs."""
        deadline = monotonic() + self.observation_timeout
        if desired_running:
            while monotonic() < deadline:
                if not self.process_manager.is_running(handle):
                    return False
                sleep(self.poll_interval)
            return self.process_manager.is_running(handle)

        while monotonic() < deadline:
            if not self.process_manager.is_running(handle):
                return True
            sleep(self.poll_interval)
        return not self.process_manager.is_running(handle)

    def _shutdown_handle(self, handle: ProcessHandle) -> None:
        """Stop the log reader and process using a consistent shutdown sequence."""
        log_streamer = handle.get_log_streamer()
        if log_streamer is not None:
            log_streamer.stop()
        self.process_manager.stop(handle)
        if log_streamer is not None:
            log_streamer.join(timeout=self.observation_timeout)

    def _save_recovery_state(
        self,
        server: ServerInstance,
        persisted_state: ServerInstanceLifecycleState,
    ) -> None:
        """Persist only the stable lifecycle state needed for safe restart recovery."""
        self.server_catalog.save_server(
            replace(server, lifecycle_state=persisted_state)
        )
