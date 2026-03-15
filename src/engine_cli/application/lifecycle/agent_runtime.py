from engine_cli.application.agent_runtimes import (
    AgentRuntimeRepository,
    InMemoryAgentRuntimeCatalog,
)
from engine_cli.application.execution import ExecutionService
from engine_cli.application.lifecycle.errors import (
    AgentRuntimeLifecycleError,
    AgentRuntimeValidationError,
)
from engine_cli.domain import (
    AgentRuntime,
    AgentRuntimeLifecycleState,
    ServerInstance,
    ServerInstanceLifecycleState,
    TaskRun,
    TaskStatus,
    TaskTargetType,
)
from engine_cli.infrastructure.agent_runtime import (
    AgentRuntimeSupervisor,
    InMemoryAgentRuntimeSupervisor,
    ManagedAgentRuntimeHandle,
)


class AgentRuntimeLifecycleService:
    """Orchestrates runtime validation and lifecycle transitions."""

    def __init__(
        self,
        execution_service: ExecutionService | None = None,
        runtime_catalog: AgentRuntimeRepository | None = None,
        supervisor: AgentRuntimeSupervisor | None = None,
    ) -> None:
        self.execution_service = execution_service or ExecutionService()
        self.runtime_catalog = runtime_catalog or InMemoryAgentRuntimeCatalog()
        self.supervisor = supervisor or InMemoryAgentRuntimeSupervisor()

    def validate(self, runtime: AgentRuntime, server: ServerInstance) -> AgentRuntime:
        self._ensure_runtime_matches_server(runtime, server)
        self._ensure_required_fields(runtime)
        if runtime.lifecycle_state in (
            AgentRuntimeLifecycleState.DRAFT,
            AgentRuntimeLifecycleState.FAILED,
        ):
            runtime.lifecycle_state = AgentRuntimeLifecycleState.ATTACHED
        elif runtime.lifecycle_state is not AgentRuntimeLifecycleState.ATTACHED:
            raise AgentRuntimeValidationError(
                "Agent runtime validation only supports draft, failed, or attached states."
            )
        return self.runtime_catalog.save_runtime(runtime)

    def start(self, runtime: AgentRuntime, server: ServerInstance) -> TaskRun:
        self._ensure_runtime_matches_server(runtime, server)
        self._ensure_required_fields(runtime)
        if server.lifecycle_state is not ServerInstanceLifecycleState.RUNNING:
            raise AgentRuntimeLifecycleError(
                "Cannot start an agent runtime unless the attached server is running."
            )
        if runtime.lifecycle_state not in (
            AgentRuntimeLifecycleState.ATTACHED,
            AgentRuntimeLifecycleState.STOPPED,
            AgentRuntimeLifecycleState.FAILED,
        ):
            raise AgentRuntimeLifecycleError(
                f"Cannot start runtime from state {runtime.lifecycle_state.value!r}."
            )

        runtime.lifecycle_state = AgentRuntimeLifecycleState.STARTING
        self.runtime_catalog.save_runtime(runtime)

        def _start_runtime_task() -> None:
            self.supervisor.activate(runtime, server)
            if not self.supervisor.is_active(runtime.agent_runtime_id):
                self.supervisor.deactivate(runtime.agent_runtime_id)
                raise AgentRuntimeLifecycleError(
                    "Agent runtime did not report an active supervisor handle."
                )

        try:
            result = self.execution_service.run_task(
                task_kind="agent_runtime.start",
                target_type=TaskTargetType.AGENT_RUNTIME,
                target_id=runtime.agent_runtime_id,
                task_operation=_start_runtime_task,
            )
        except Exception:
            self.supervisor.deactivate(runtime.agent_runtime_id)
            runtime.lifecycle_state = AgentRuntimeLifecycleState.FAILED
            self.runtime_catalog.save_runtime(runtime)
            raise
        if result.final_status is TaskStatus.COMPLETED:
            runtime.lifecycle_state = AgentRuntimeLifecycleState.ACTIVE
        else:
            self.supervisor.deactivate(runtime.agent_runtime_id)
            runtime.lifecycle_state = AgentRuntimeLifecycleState.FAILED
        self.runtime_catalog.save_runtime(runtime)
        task = self.execution_service.get_task(result.task_run_id)
        if task is None:
            raise AgentRuntimeLifecycleError("Start task record was not persisted.")
        return task

    def stop(self, runtime: AgentRuntime) -> TaskRun:
        self._ensure_required_fields(runtime)
        if runtime.lifecycle_state is not AgentRuntimeLifecycleState.ACTIVE:
            raise AgentRuntimeLifecycleError(
                f"Cannot stop runtime from state {runtime.lifecycle_state.value!r}."
            )
        handle = self.supervisor.get_handle(runtime.agent_runtime_id)
        if handle is None:
            raise AgentRuntimeLifecycleError(
                "Cannot stop runtime without an active supervisor handle."
            )

        runtime.lifecycle_state = AgentRuntimeLifecycleState.STOPPING
        self.runtime_catalog.save_runtime(runtime)

        def _stop_runtime_task() -> None:
            removed_handle = self.supervisor.deactivate(runtime.agent_runtime_id)
            if removed_handle is None:
                raise AgentRuntimeLifecycleError(
                    "Agent runtime handle disappeared before shutdown completed."
                )
            if self.supervisor.is_active(runtime.agent_runtime_id):
                raise AgentRuntimeLifecycleError(
                    "Agent runtime remained active after shutdown."
                )

        result = self.execution_service.run_task(
            task_kind="agent_runtime.stop",
            target_type=TaskTargetType.AGENT_RUNTIME,
            target_id=runtime.agent_runtime_id,
            task_operation=_stop_runtime_task,
        )
        if result.final_status is TaskStatus.COMPLETED:
            runtime.lifecycle_state = AgentRuntimeLifecycleState.STOPPED
        else:
            runtime.lifecycle_state = AgentRuntimeLifecycleState.FAILED
        self.runtime_catalog.save_runtime(runtime)
        task = self.execution_service.get_task(result.task_run_id)
        if task is None:
            raise AgentRuntimeLifecycleError("Stop task record was not persisted.")
        return task

    def get_handle(self, agent_runtime_id: str) -> ManagedAgentRuntimeHandle | None:
        """Return the active runtime handle for a managed agent runtime."""
        return self.supervisor.get_handle(agent_runtime_id)

    def _ensure_runtime_matches_server(
        self,
        runtime: AgentRuntime,
        server: ServerInstance,
    ) -> None:
        if runtime.server_instance_id != server.server_instance_id:
            raise AgentRuntimeValidationError(
                "Agent runtime server attachment does not match the provided server."
            )

    def _ensure_required_fields(self, runtime: AgentRuntime) -> None:
        if not runtime.agent_runtime_id.strip():
            raise AgentRuntimeValidationError(
                "Agent runtime must reference a non-empty runtime id."
            )
        if not runtime.name.strip():
            raise AgentRuntimeValidationError(
                "Agent runtime must reference a non-empty name."
            )
        if not runtime.agent_profile_id.strip():
            raise AgentRuntimeValidationError(
                "Agent runtime must reference a non-empty agent profile id."
            )
        if not runtime.server_instance_id.strip():
            raise AgentRuntimeValidationError(
                "Agent runtime must reference a non-empty server instance id."
            )
        if not runtime.agent_kind.strip():
            raise AgentRuntimeValidationError(
                "Agent runtime must reference a non-empty agent kind."
            )
