from __future__ import annotations

from typing import Protocol

from engine_cli.domain import TaskRun, TaskTargetType


class TaskRunRepository(Protocol):
    """Storage and query contract for persisted task runs."""

    def get_task(self, task_run_id: str) -> TaskRun | None:
        """Return one task run if it exists."""
        ...

    def list_tasks(self) -> list[TaskRun]:
        """Return all task runs in storage order."""
        ...

    def list_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        """Return all task runs for one target."""
        ...

    def list_active_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        """Return non-terminal task runs for one target."""
        ...

    def save_task(self, task: TaskRun) -> TaskRun:
        """Insert or update one task run."""
        ...
