from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from uuid import uuid4

from engine_cli.application.execution.catalog import InMemoryTaskRunCatalog
from engine_cli.application.execution.errors import (
    ActiveTaskConflictError,
    ExecutionServiceError,
    InvalidTaskTransitionError,
    UnsupportedTaskCancellationError,
    UnsupportedTaskKindError,
)
from engine_cli.application.execution.repository import TaskRunRepository
from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType


SUPPORTED_TASK_KINDS = frozenset(
    {
        "server_instance.start",
        "server_instance.stop",
        "server_instance.inspect",
        "server_instance.reload_datapacks",
        "server_instance.validate_datapack",
        "agent_runtime.start",
        "agent_runtime.stop",
    }
)

LIFECYCLE_CHANGING_TASK_KINDS = frozenset(
    {
        "server_instance.start",
        "server_instance.stop",
        "agent_runtime.start",
        "agent_runtime.stop",
    }
)


@dataclass
class ExecutionResult:
    """Outcome returned by the execution service."""

    task_run_id: str
    final_status: TaskStatus
    error_summary: str | None = None


class ExecutionService:
    """Repository-backed owner of task creation and status transitions."""

    def __init__(self, task_repository: TaskRunRepository | None = None) -> None:
        self.task_repository = task_repository or InMemoryTaskRunCatalog()

    def start_task(self, task: TaskRun | str) -> TaskRun:
        """Move a pending task into the running state."""
        stored_task = self._require_task(task)
        if stored_task.status is not TaskStatus.PENDING:
            raise InvalidTaskTransitionError(
                f"Cannot start task from state {stored_task.status.value!r}."
            )
        stored_task.status = TaskStatus.RUNNING
        stored_task.started_at = datetime.now()
        stored_task.finished_at = None
        stored_task.error_summary = None
        return self._sync_task_reference(task, self.task_repository.save_task(stored_task))

    def complete_task(self, task: TaskRun | str) -> TaskRun:
        """Move a running task into the completed state."""
        stored_task = self._require_task(task)
        if stored_task.status is not TaskStatus.RUNNING:
            raise InvalidTaskTransitionError(
                f"Cannot complete task from state {stored_task.status.value!r}."
            )
        stored_task.status = TaskStatus.COMPLETED
        stored_task.finished_at = datetime.now()
        stored_task.error_summary = None
        return self._sync_task_reference(task, self.task_repository.save_task(stored_task))

    def fail_task(self, task: TaskRun | str, error_summary: str) -> TaskRun:
        """Move a running task into the failed state."""
        stored_task = self._require_task(task)
        if stored_task.status is not TaskStatus.RUNNING:
            raise InvalidTaskTransitionError(
                f"Cannot fail task from state {stored_task.status.value!r}."
            )
        failure_summary = error_summary.strip()
        if not failure_summary:
            raise ExecutionServiceError("Failed tasks require a non-empty error summary.")
        stored_task.status = TaskStatus.FAILED
        stored_task.finished_at = datetime.now()
        stored_task.error_summary = failure_summary
        return self._sync_task_reference(task, self.task_repository.save_task(stored_task))

    def cancel_task(self, task: TaskRun | str) -> TaskRun:
        """Move a pending task into the cancelled state."""
        stored_task = self._require_task(task)
        if stored_task.status is TaskStatus.RUNNING:
            raise UnsupportedTaskCancellationError(
                "Cancellation of running tasks is not supported in v1."
            )
        if stored_task.status is not TaskStatus.PENDING:
            raise InvalidTaskTransitionError(
                f"Cannot cancel task from state {stored_task.status.value!r}."
            )
        stored_task.status = TaskStatus.CANCELLED
        stored_task.finished_at = datetime.now()
        stored_task.error_summary = None
        return self._sync_task_reference(task, self.task_repository.save_task(stored_task))

    def create_task(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
    ) -> TaskRun:
        self._validate_task_kind(task_kind)
        if not target_id.strip():
            raise ExecutionServiceError("Target id must be a non-empty string.")
        self._guard_active_task_conflict(task_kind, target_type, target_id)
        task = TaskRun(
            task_run_id=uuid4().hex,
            task_kind=task_kind,
            target_type=target_type,
            target_id=target_id,
            status=TaskStatus.PENDING,
        )
        return self.task_repository.save_task(task)

    def execute_task(
        self,
        task: TaskRun | str,
        executor: Callable[[], None],
    ) -> ExecutionResult:
        """Execute a task and mutate its status through terminal completion."""
        running_task = self.start_task(task)
        try:
            executor()
        except Exception as exc:  # pragma: no cover - behavior verified by tests
            terminal_task = self.fail_task(
                running_task,
                str(exc) or exc.__class__.__name__,
            )
        else:
            terminal_task = self.complete_task(running_task)
        return ExecutionResult(
            task_run_id=terminal_task.task_run_id,
            final_status=terminal_task.status,
            error_summary=terminal_task.error_summary,
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

    def get_task(self, task_run_id: str) -> TaskRun | None:
        """Return one stored task if it exists."""
        return self.task_repository.get_task(task_run_id)

    def list_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        """Return all stored tasks for one target."""
        return self.task_repository.list_tasks_for_target(target_type, target_id)

    def _validate_task_kind(self, task_kind: str) -> None:
        if task_kind not in SUPPORTED_TASK_KINDS:
            raise UnsupportedTaskKindError(f"Unsupported task kind: {task_kind!r}")

    def _guard_active_task_conflict(
        self,
        task_kind: str,
        target_type: TaskTargetType,
        target_id: str,
    ) -> None:
        if task_kind not in LIFECYCLE_CHANGING_TASK_KINDS:
            return
        active_tasks = self.task_repository.list_active_tasks_for_target(
            target_type,
            target_id,
        )
        if active_tasks:
            raise ActiveTaskConflictError(
                "A lifecycle-changing task is already active for this target."
            )

    def _require_task(self, task: TaskRun | str) -> TaskRun:
        task_run_id = task if isinstance(task, str) else task.task_run_id
        stored_task = self.task_repository.get_task(task_run_id)
        if stored_task is None:
            raise ExecutionServiceError(f"Unknown task run id: {task_run_id!r}")
        return stored_task

    def _sync_task_reference(
        self,
        original_task: TaskRun | str,
        saved_task: TaskRun,
    ) -> TaskRun:
        if isinstance(original_task, TaskRun):
            original_task.task_kind = saved_task.task_kind
            original_task.target_type = saved_task.target_type
            original_task.target_id = saved_task.target_id
            original_task.status = saved_task.status
            original_task.started_at = saved_task.started_at
            original_task.finished_at = saved_task.finished_at
            original_task.error_summary = saved_task.error_summary
            return original_task
        return saved_task
