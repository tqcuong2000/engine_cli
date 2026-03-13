from dataclasses import dataclass
from enum import StrEnum

from engine_cli.domain.mode import OperatingMode


class AgentRuntimeLifecycleState(StrEnum):
    DRAFT = "draft"
    ATTACHED = "attached"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class AgentProfile:
    """Configuration-level definition of agent behavior."""

    agent_profile_id: str
    name: str
    mode: OperatingMode
    agent_kind: str


@dataclass
class AgentRuntime:
    """Live managed agent instance attached to a server."""

    agent_runtime_id: str
    name: str
    agent_profile_id: str
    server_instance_id: str
    agent_kind: str
    lifecycle_state: AgentRuntimeLifecycleState
