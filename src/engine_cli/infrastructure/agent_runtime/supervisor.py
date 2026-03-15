from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from engine_cli.domain import AgentRuntime, ServerInstance


@dataclass
class ManagedAgentRuntimeHandle:
    """In-memory handle representing one active managed agent runtime."""

    agent_runtime_id: str
    server_instance_id: str
    agent_kind: str


class AgentRuntimeSupervisor(Protocol):
    """Boundary for creating, observing, and removing active runtime handles."""

    def activate(
        self,
        runtime: AgentRuntime,
        server: ServerInstance,
    ) -> ManagedAgentRuntimeHandle:
        """Create and retain an active handle for one runtime."""
        ...

    def deactivate(self, agent_runtime_id: str) -> ManagedAgentRuntimeHandle | None:
        """Remove and return one active runtime handle if it exists."""
        ...

    def get_handle(self, agent_runtime_id: str) -> ManagedAgentRuntimeHandle | None:
        """Return one active runtime handle if it exists."""
        ...

    def is_active(self, agent_runtime_id: str) -> bool:
        """Return whether one runtime is positively observed as active."""
        ...


class InMemoryAgentRuntimeSupervisor:
    """Minimal in-memory runtime supervisor for v1 lifecycle orchestration."""

    def __init__(self) -> None:
        self._handles: dict[str, ManagedAgentRuntimeHandle] = {}

    def activate(
        self,
        runtime: AgentRuntime,
        server: ServerInstance,
    ) -> ManagedAgentRuntimeHandle:
        handle = ManagedAgentRuntimeHandle(
            agent_runtime_id=runtime.agent_runtime_id,
            server_instance_id=server.server_instance_id,
            agent_kind=runtime.agent_kind,
        )
        self._handles[runtime.agent_runtime_id] = handle
        return handle

    def deactivate(self, agent_runtime_id: str) -> ManagedAgentRuntimeHandle | None:
        return self._handles.pop(agent_runtime_id, None)

    def get_handle(self, agent_runtime_id: str) -> ManagedAgentRuntimeHandle | None:
        return self._handles.get(agent_runtime_id)

    def is_active(self, agent_runtime_id: str) -> bool:
        return agent_runtime_id in self._handles
