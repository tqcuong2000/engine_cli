from engine_cli.domain import OperatingMode


class AgentRuntimeManagerError(Exception):
    """Base error for agent runtime management failures."""


class AgentRuntimeNotFoundError(AgentRuntimeManagerError):
    """Raised when an agent runtime cannot be found in the catalog."""

    def __init__(self, agent_runtime_id: str, *, detail: str | None = None) -> None:
        message = f"Unknown agent runtime '{agent_runtime_id}'."
        if detail is not None:
            message = f"{message} {detail}"
        super().__init__(message)


class LiveAgentRuntimeRemovalError(AgentRuntimeManagerError):
    """Raised when a managed runtime is removed while still live."""

    def __init__(
        self,
        agent_runtime_id: str,
        lifecycle_state: str,
    ) -> None:
        super().__init__(
            f"Cannot remove live agent runtime '{agent_runtime_id}' while it is "
            f"in state '{lifecycle_state}'."
        )


class InvalidAgentRuntimeProfileModeError(AgentRuntimeManagerError):
    """Raised when a profile mode cannot define a server-attached runtime."""

    def __init__(self, agent_profile_id: str, mode: OperatingMode) -> None:
        super().__init__(
            f"Agent profile '{agent_profile_id}' with mode '{mode.value}' "
            "cannot define an attached runtime."
        )


class AgentRuntimeAttachedServerNotFoundError(AgentRuntimeManagerError):
    """Raised when a runtime references a server that cannot be loaded."""

    def __init__(self, server_instance_id: str) -> None:
        super().__init__(
            f"Attached server '{server_instance_id}' is not available for runtime management."
        )


class AgentRuntimeAttachmentProjectionMismatchError(AgentRuntimeManagerError):
    """Raised when server.attached_agents drifts from runtime attachment truth."""

    def __init__(self, server_instance_id: str) -> None:
        super().__init__(
            "Server attachment projection drift detected for "
            f"'{server_instance_id}'."
        )


class ServerInstanceHasAttachedRuntimesError(AgentRuntimeManagerError):
    """Raised when a server removal would orphan attached runtimes."""

    def __init__(self, server_instance_id: str, agent_runtime_ids: list[str]) -> None:
        joined_runtime_ids = ", ".join(agent_runtime_ids)
        super().__init__(
            f"Server '{server_instance_id}' still has attached runtimes: "
            f"{joined_runtime_ids}."
        )
