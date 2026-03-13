from dataclasses import dataclass, field
from enum import StrEnum


class ServerInstanceLifecycleState(StrEnum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class ServerInstance:
    """Control-plane object for one managed Minecraft server instance."""

    server_instance_id: str
    name: str
    location: str
    command: str
    minecraft_version: str
    server_distribution: str
    lifecycle_state: ServerInstanceLifecycleState
    attached_agents: list[str] = field(default_factory=list)
