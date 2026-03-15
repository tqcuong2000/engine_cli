from pathlib import Path

from engine_cli.application.agent_runtimes import AgentRuntimeManager
from engine_cli.application.lifecycle import (
    AgentRuntimeLifecycleService,
    ServerInstanceLifecycleService,
    ServerRuntimeStateResolver,
)
from engine_cli.application.execution import ExecutionService
from engine_cli.application.server_commands import ServerCommandService
from engine_cli.application.server_instances import ServerInstanceManager
from engine_cli.application.session import (
    AgentProfileSelectionService,
    SessionCoordinator,
    SessionContext,
)
from engine_cli.application.terminal import ServerTerminalStore
from engine_cli.config import ConfigResolver
from engine_cli.infrastructure.agent_runtime import InMemoryAgentRuntimeSupervisor
from engine_cli.infrastructure.persistence import (
    AppPaths,
    SqliteAgentRuntimeRepository,
    SqliteServerInstanceRepository,
)
from engine_cli.infrastructure.persistence.sqlite import SqliteTaskRunRepository

from engine_cli.application.composition.runtime import AppRuntime
from engine_cli.domain import AgentRuntimeLifecycleState


TRANSIENT_AGENT_RUNTIME_STATES = frozenset(
    {
        AgentRuntimeLifecycleState.STARTING,
        AgentRuntimeLifecycleState.ACTIVE,
        AgentRuntimeLifecycleState.STOPPING,
    }
)


def create_app_runtime(
    *,
    app_root: Path | None = None,
    workspace_root: Path | None = None,
) -> AppRuntime:
    """Assemble the TUI runtime from application-owned dependencies."""
    app_paths = AppPaths.from_root(app_root)
    resolved_workspace_root = (
        workspace_root.expanduser().resolve() if workspace_root is not None else None
    )
    settings = ConfigResolver().resolve(
        global_config_dir=app_paths.config_dir,
        workspace_root=resolved_workspace_root,
    )

    session_context = SessionContext()
    session_coordinator = SessionCoordinator(session_context)
    profile_selection_service = AgentProfileSelectionService()
    session_coordinator.set_agent_profile(
        profile_selection_service.resolve_effective_profile_id(
            session_context=session_context,
            settings=settings,
        )
    )

    terminal_store = ServerTerminalStore()
    task_repository = SqliteTaskRunRepository(app_paths.db_path)
    execution_service = ExecutionService(
        task_repository=task_repository
    )
    server_repository = SqliteServerInstanceRepository(app_paths.db_path)
    agent_runtime_repository = SqliteAgentRuntimeRepository(app_paths.db_path)
    _reconcile_persisted_agent_runtimes(agent_runtime_repository)
    server_manager = ServerInstanceManager(
        catalog=server_repository,
        runtime_catalog=agent_runtime_repository,
    )
    agent_runtime_manager = AgentRuntimeManager(
        catalog=agent_runtime_repository,
        server_catalog=server_repository,
    )
    agent_runtime_supervisor = InMemoryAgentRuntimeSupervisor()
    lifecycle_service = ServerInstanceLifecycleService(
        execution_service=execution_service,
        terminal_store=terminal_store,
    )
    agent_runtime_lifecycle_service = AgentRuntimeLifecycleService(
        execution_service=execution_service,
        runtime_catalog=agent_runtime_repository,
        supervisor=agent_runtime_supervisor,
    )
    server_command_service = ServerCommandService(
        lifecycle_service=lifecycle_service,
        terminal_store=terminal_store,
    )
    server_runtime_state_resolver = ServerRuntimeStateResolver(lifecycle_service)

    return AppRuntime(
        app_paths=app_paths,
        workspace_root=resolved_workspace_root,
        settings=settings,
        session_coordinator=session_coordinator,
        session_context=session_context,
        profile_selection_service=profile_selection_service,
        terminal_store=terminal_store,
        server_manager=server_manager,
        lifecycle_service=lifecycle_service,
        agent_runtime_manager=agent_runtime_manager,
        agent_runtime_lifecycle_service=agent_runtime_lifecycle_service,
        server_command_service=server_command_service,
        server_runtime_state_resolver=server_runtime_state_resolver,
    )


def _reconcile_persisted_agent_runtimes(
    agent_runtime_repository: SqliteAgentRuntimeRepository,
) -> None:
    """Normalize transient persisted runtime states into a safe recoverable state."""
    for runtime in agent_runtime_repository.list_runtimes():
        if runtime.lifecycle_state not in TRANSIENT_AGENT_RUNTIME_STATES:
            continue
        runtime.lifecycle_state = AgentRuntimeLifecycleState.STOPPED
        agent_runtime_repository.save_runtime(runtime)
