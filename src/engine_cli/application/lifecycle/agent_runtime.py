from engine_cli.domain import AgentRuntime, ServerInstance, TaskRun


class AgentRuntimeLifecycleService:
    """Thin stub for agent-runtime lifecycle orchestration."""

    def validate(self, runtime: AgentRuntime, server: ServerInstance) -> AgentRuntime:
        raise NotImplementedError("Agent runtime validation is not implemented yet.")

    def start(self, runtime: AgentRuntime, server: ServerInstance) -> TaskRun:
        raise NotImplementedError("Agent runtime start is not implemented yet.")

    def stop(self, runtime: AgentRuntime) -> TaskRun:
        raise NotImplementedError("Agent runtime stop is not implemented yet.")
