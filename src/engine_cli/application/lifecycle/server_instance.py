from time import monotonic, sleep

from engine_cli.application.execution import ExecutionService
from engine_cli.application.lifecycle.errors import (
    ServerInstanceLifecycleError,
    ServerInstanceValidationError,
)
from engine_cli.domain import (
    ServerInstance,
    ServerInstanceLifecycleState,
    TaskRun,
    TaskStatus,
    TaskTargetType,
)
from engine_cli.infrastructure.process.local_manager import LocalProcessManager
from engine_cli.infrastructure.process.managed_process import ManagedProcessHandle


class ServerInstanceLifecycleService:
    """Orchestrates server state transitions and manages process lifecycles."""

    def __init__(
        self,
        execution_service: ExecutionService | None = None,
        process_manager: LocalProcessManager | None = None,
        observation_timeout: float = 1.0,
        poll_interval: float = 0.05,
    ) -> None:
        """Initialize the service with execution and process management dependencies."""
        self.execution_service = execution_service or ExecutionService()
        self.process_manager = process_manager or LocalProcessManager()
        self.observation_timeout = observation_timeout
        self.poll_interval = poll_interval
        self._handles: dict[str, ManagedProcessHandle] = {}

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

        task = self.execution_service.create_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id=server.server_instance_id,
        )
        server.lifecycle_state = ServerInstanceLifecycleState.STARTING

        def executor() -> None:
            handle = self.process_manager.start(server.command, server.location)
            if not self._wait_for_state(handle, desired_running=True):
                self.process_manager.stop(handle)
                raise ServerInstanceLifecycleError(
                    "Server process did not remain running long enough to confirm startup."
                )
            self._handles[server.server_instance_id] = handle

        result = self.execution_service.execute_task(task, executor)
        if result.final_status is TaskStatus.COMPLETED:
            server.lifecycle_state = ServerInstanceLifecycleState.RUNNING
        else:
            server.lifecycle_state = ServerInstanceLifecycleState.FAILED
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

        task = self.execution_service.create_task(
            task_kind="server_instance.stop",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id=server.server_instance_id,
        )
        server.lifecycle_state = ServerInstanceLifecycleState.STOPPING

        def executor() -> None:
            self.process_manager.stop(handle)
            if not self._wait_for_state(handle, desired_running=False):
                raise ServerInstanceLifecycleError(
                    "Server process did not stop within the observation window."
                )
            self._handles.pop(server.server_instance_id, None)

        result = self.execution_service.execute_task(task, executor)
        if result.final_status is TaskStatus.COMPLETED:
            server.lifecycle_state = ServerInstanceLifecycleState.STOPPED
        else:
            server.lifecycle_state = ServerInstanceLifecycleState.FAILED
        return task

    def _wait_for_state(
        self,
        handle: ManagedProcessHandle,
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
