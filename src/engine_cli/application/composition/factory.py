from pathlib import Path

from engine_cli.application.lifecycle import (
    ServerInstanceLifecycleService,
    ServerRuntimeStateResolver,
)
from engine_cli.application.server_commands import ServerCommandService
from engine_cli.application.server_instances import ServerInstanceManager
from engine_cli.application.session import (
    AgentProfileSelectionService,
    SessionContext,
)
from engine_cli.application.terminal import ServerTerminalStore
from engine_cli.config import ConfigResolver
from engine_cli.infrastructure.persistence import AppPaths, SqliteServerInstanceRepository

from engine_cli.application.composition.runtime import AppRuntime


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
    profile_selection_service = AgentProfileSelectionService()
    session_context.set_agent_profile(
        profile_selection_service.resolve_effective_profile_id(
            session_context=session_context,
            settings=settings,
        )
    )

    terminal_store = ServerTerminalStore()
    server_manager = ServerInstanceManager(
        catalog=SqliteServerInstanceRepository(app_paths.db_path)
    )
    lifecycle_service = ServerInstanceLifecycleService(terminal_store=terminal_store)
    server_command_service = ServerCommandService(
        lifecycle_service=lifecycle_service,
        terminal_store=terminal_store,
    )
    server_runtime_state_resolver = ServerRuntimeStateResolver(lifecycle_service)

    return AppRuntime(
        app_paths=app_paths,
        workspace_root=resolved_workspace_root,
        settings=settings,
        session_context=session_context,
        profile_selection_service=profile_selection_service,
        terminal_store=terminal_store,
        server_manager=server_manager,
        lifecycle_service=lifecycle_service,
        server_command_service=server_command_service,
        server_runtime_state_resolver=server_runtime_state_resolver,
    )
