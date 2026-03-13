from dataclasses import dataclass
from typing import Callable

from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType


@dataclass
class ExecutionResult:
    """Outcome returned by the execution service."""

    task_run_id: str
    final_status: TaskStatus
    error_summary: str | None = None


class ExecutionService:
    """Thin stub for task creation and execution ownership."""

    def create_task(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
    ) -> TaskRun:
        raise NotImplementedError("Task creation is not implemented yet.")

    def run_task(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
        executor: Callable[[], None],
    ) -> ExecutionResult:
        raise NotImplementedError("Task execution is not implemented yet.")
