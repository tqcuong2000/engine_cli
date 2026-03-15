from dataclasses import dataclass
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
from engine_cli.config import ResolvedSettings
from engine_cli.infrastructure.persistence import AppPaths


@dataclass(frozen=True)
class AppRuntime:
    """Assembled application runtime dependencies for the TUI."""

    app_paths: AppPaths
    workspace_root: Path | None
    settings: ResolvedSettings
    session_context: SessionContext
    profile_selection_service: AgentProfileSelectionService
    terminal_store: ServerTerminalStore
    server_manager: ServerInstanceManager
    lifecycle_service: ServerInstanceLifecycleService
    server_command_service: ServerCommandService
    server_runtime_state_resolver: ServerRuntimeStateResolver
