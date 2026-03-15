from typing import Protocol

from engine_cli.domain import AgentRuntime


class AgentRuntimeRepository(Protocol):
    """Application-facing persistence contract for agent runtimes."""

    def get_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Return one persisted runtime if it exists."""
        ...

    def list_runtimes(self) -> list[AgentRuntime]:
        """Return all persisted runtimes."""
        ...

    def list_runtimes_for_server(self, server_instance_id: str) -> list[AgentRuntime]:
        """Return persisted runtimes attached to one server."""
        ...

    def save_runtime(self, runtime: AgentRuntime) -> AgentRuntime:
        """Insert or replace a persisted runtime."""
        ...

    def remove_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Remove and return a persisted runtime if it exists."""
        ...
