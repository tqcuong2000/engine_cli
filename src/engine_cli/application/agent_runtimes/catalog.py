from dataclasses import dataclass, field

from engine_cli.domain import AgentRuntime


@dataclass
class InMemoryAgentRuntimeCatalog:
    """In-memory implementation of the agent-runtime repository contract."""

    _runtimes: dict[str, AgentRuntime] = field(default_factory=dict)

    def get_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Return one runtime by identifier if it exists."""
        return self._runtimes.get(agent_runtime_id)

    def list_runtimes(self) -> list[AgentRuntime]:
        """Return all known runtimes in insertion order."""
        return list(self._runtimes.values())

    def list_runtimes_for_server(self, server_instance_id: str) -> list[AgentRuntime]:
        """Return all runtimes attached to one server in insertion order."""
        return [
            runtime
            for runtime in self._runtimes.values()
            if runtime.server_instance_id == server_instance_id
        ]

    def save_runtime(self, runtime: AgentRuntime) -> AgentRuntime:
        """Insert or replace a runtime in the catalog."""
        self._runtimes[runtime.agent_runtime_id] = runtime
        return runtime

    def remove_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Remove and return a runtime if it exists."""
        return self._runtimes.pop(agent_runtime_id, None)
