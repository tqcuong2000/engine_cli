from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import uuid4

from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType


@dataclass
class ExecutionResult:
    """Outcome returned by the execution service."""

    task_run_id: str
    final_status: TaskStatus
    error_summary: str | None = None


class ExecutionService:
    """Thin stub for task creation and execution ownership."""

    def start_task(self, task: TaskRun) -> TaskRun:
        """Move a pending task into the running state."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        return task

    def complete_task(self, task: TaskRun) -> TaskRun:
        """Move a running task into the completed state."""
        task.status = TaskStatus.COMPLETED
        task.finished_at = datetime.now()
        task.error_summary = None
        return task

    def fail_task(self, task: TaskRun, error_summary: str) -> TaskRun:
        """Move a running task into the failed state."""
        task.status = TaskStatus.FAILED
        task.finished_at = datetime.now()
        task.error_summary = error_summary
        return task

    def cancel_task(self, task: TaskRun) -> TaskRun:
        """Move a pending or running task into the cancelled state."""
        task.status = TaskStatus.CANCELLED
        task.finished_at = datetime.now()
        return task

    def create_task(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
    ) -> TaskRun:
        return TaskRun(
            task_run_id=uuid4().hex,
            task_kind=task_kind,
            target_type=target_type,
            target_id=target_id,
            status=TaskStatus.PENDING,
        )

    def execute_task(
        self,
        task: TaskRun,
        executor: Callable[[], None],
    ) -> ExecutionResult:
        """Execute a task and mutate its status through terminal completion."""
        self.start_task(task)
        try:
            executor()
        except Exception as exc:  # pragma: no cover - behavior verified by tests
            self.fail_task(task, str(exc) or exc.__class__.__name__)
        else:
            self.complete_task(task)
        return ExecutionResult(
            task_run_id=task.task_run_id,
            final_status=task.status,
            error_summary=task.error_summary,
        )

    def run_task(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
        executor: Callable[[], None],
    ) -> ExecutionResult:
        task = self.create_task(task_kind, target_type, target_id)
        return self.execute_task(task, executor)
