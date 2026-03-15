from __future__ import annotations

from dataclasses import replace

from engine_cli.application.execution.repository import TaskRunRepository
from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType


ACTIVE_TASK_STATUSES = frozenset({TaskStatus.PENDING, TaskStatus.RUNNING})


class InMemoryTaskRunCatalog(TaskRunRepository):
    """In-memory task-run repository for focused tests and local flows."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRun] = {}
        self._order: list[str] = []

    def get_task(self, task_run_id: str) -> TaskRun | None:
        task = self._tasks.get(task_run_id)
        if task is None:
            return None
        return replace(task)

    def list_tasks(self) -> list[TaskRun]:
        return [replace(self._tasks[task_run_id]) for task_run_id in self._order]

    def list_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        return [
            replace(task)
            for task in self._tasks.values()
            if task.target_type is target_type and task.target_id == target_id
        ]

    def list_active_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        return [
            replace(task)
            for task in self._tasks.values()
            if task.target_type is target_type
            and task.target_id == target_id
            and task.status in ACTIVE_TASK_STATUSES
        ]

    def save_task(self, task: TaskRun) -> TaskRun:
        stored_task = replace(task)
        if stored_task.task_run_id not in self._tasks:
            self._order.append(stored_task.task_run_id)
        self._tasks[stored_task.task_run_id] = stored_task
        return replace(stored_task)
