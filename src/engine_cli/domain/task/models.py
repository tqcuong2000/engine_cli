from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskTargetType(StrEnum):
    SERVER_INSTANCE = "server_instance"
    AGENT_RUNTIME = "agent_runtime"


@dataclass
class TaskRun:
    """Tracked execution of one operation against one target."""

    task_run_id: str
    task_kind: str
    target_type: TaskTargetType
    target_id: str
    status: TaskStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None
