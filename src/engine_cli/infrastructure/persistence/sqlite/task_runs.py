from __future__ import annotations

from contextlib import closing
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import sqlite3

from engine_cli.application.execution.catalog import ACTIVE_TASK_STATUSES
from engine_cli.application.execution.repository import TaskRunRepository
from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType
from engine_cli.infrastructure.persistence.sqlite.bootstrap import ensure_schema


class TaskRunStorageError(Exception):
    """Raised when persisted task-run data is invalid for durable storage."""


class SqliteTaskRunRepository(TaskRunRepository):
    """SQLite-backed persistence adapter for durable task-run records."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        ensure_schema(self.database_path)

    def get_task(self, task_run_id: str) -> TaskRun | None:
        query = """
        SELECT
            task_run_id,
            task_kind,
            target_type,
            target_id,
            status,
            started_at,
            finished_at,
            error_summary
        FROM task_runs
        WHERE task_run_id = ?
        """
        with closing(self._connect()) as connection:
            row = connection.execute(query, (task_run_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def list_tasks(self) -> list[TaskRun]:
        query = """
        SELECT
            task_run_id,
            task_kind,
            target_type,
            target_id,
            status,
            started_at,
            finished_at,
            error_summary
        FROM task_runs
        ORDER BY rowid
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        query = """
        SELECT
            task_run_id,
            task_kind,
            target_type,
            target_id,
            status,
            started_at,
            finished_at,
            error_summary
        FROM task_runs
        WHERE target_type = ? AND target_id = ?
        ORDER BY rowid
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query, (target_type.value, target_id)).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_active_tasks_for_target(
        self,
        target_type: TaskTargetType,
        target_id: str,
    ) -> list[TaskRun]:
        placeholders = ", ".join("?" for _ in ACTIVE_TASK_STATUSES)
        query = f"""
        SELECT
            task_run_id,
            task_kind,
            target_type,
            target_id,
            status,
            started_at,
            finished_at,
            error_summary
        FROM task_runs
        WHERE target_type = ? AND target_id = ? AND status IN ({placeholders})
        ORDER BY rowid
        """
        parameters = (
            target_type.value,
            target_id,
            *(status.value for status in ACTIVE_TASK_STATUSES),
        )
        with closing(self._connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._row_to_task(row) for row in rows]

    def save_task(self, task: TaskRun) -> TaskRun:
        validated_task = self._validate_task(task)
        query = """
        INSERT INTO task_runs (
            task_run_id,
            task_kind,
            target_type,
            target_id,
            status,
            started_at,
            finished_at,
            error_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_run_id) DO UPDATE SET
            task_kind = excluded.task_kind,
            target_type = excluded.target_type,
            target_id = excluded.target_id,
            status = excluded.status,
            started_at = excluded.started_at,
            finished_at = excluded.finished_at,
            error_summary = excluded.error_summary
        """
        with closing(self._connect()) as connection:
            connection.execute(
                query,
                (
                    validated_task.task_run_id,
                    validated_task.task_kind,
                    validated_task.target_type.value,
                    validated_task.target_id,
                    validated_task.status.value,
                    self._serialize_datetime(validated_task.started_at),
                    self._serialize_datetime(validated_task.finished_at),
                    validated_task.error_summary,
                ),
            )
            connection.commit()
        return replace(validated_task)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_task(self, row: sqlite3.Row) -> TaskRun:
        task = TaskRun(
            task_run_id=row["task_run_id"],
            task_kind=self._parse_task_kind(row["task_kind"]),
            target_type=self._parse_target_type(row["target_type"]),
            target_id=self._parse_target_id(row["target_id"]),
            status=self._parse_status(row["status"]),
            started_at=self._parse_datetime(row["started_at"]),
            finished_at=self._parse_datetime(row["finished_at"]),
            error_summary=self._parse_error_summary(row["error_summary"]),
        )
        return self._validate_task(task)

    def _validate_task(self, task: TaskRun) -> TaskRun:
        self._parse_task_kind(task.task_kind)
        self._parse_target_id(task.target_id)
        started_at = task.started_at
        finished_at = task.finished_at
        error_summary = task.error_summary

        if task.status is TaskStatus.PENDING:
            if started_at is not None or finished_at is not None:
                raise TaskRunStorageError(
                    "Pending tasks must not have started_at or finished_at values."
                )
            if error_summary is not None:
                raise TaskRunStorageError(
                    "Pending tasks must not have an error summary."
                )
            return replace(task)

        if task.status is TaskStatus.RUNNING:
            if started_at is None or finished_at is not None:
                raise TaskRunStorageError(
                    "Running tasks must have started_at and no finished_at value."
                )
            if error_summary is not None:
                raise TaskRunStorageError(
                    "Running tasks must not have an error summary."
                )
            return replace(task)

        if task.status is TaskStatus.FAILED:
            if started_at is None or finished_at is None:
                raise TaskRunStorageError(
                    "Failed tasks must have both started_at and finished_at values."
                )
            if finished_at < started_at:
                raise TaskRunStorageError(
                    "Task finished_at must not be earlier than started_at."
                )
            if not error_summary:
                raise TaskRunStorageError(
                    "Failed tasks must include a non-empty error summary."
                )
            return replace(task)

        if task.status is TaskStatus.COMPLETED:
            if started_at is None or finished_at is None:
                raise TaskRunStorageError(
                    "Completed tasks must have both started_at and finished_at values."
                )
            if finished_at < started_at:
                raise TaskRunStorageError(
                    "Task finished_at must not be earlier than started_at."
                )
            if error_summary is not None:
                raise TaskRunStorageError(
                    "Completed tasks must not have an error summary."
                )
            return replace(task)

        if finished_at is None:
            raise TaskRunStorageError(
                "Cancelled tasks must include a finished_at value."
            )
        if started_at is not None and finished_at < started_at:
            raise TaskRunStorageError(
                "Task finished_at must not be earlier than started_at."
            )
        if error_summary is not None:
            raise TaskRunStorageError(
                "Cancelled tasks must not have an error summary."
            )
        return replace(task)

    def _parse_status(self, raw_value: str) -> TaskStatus:
        try:
            return TaskStatus(raw_value)
        except ValueError as exc:
            raise TaskRunStorageError(
                f"Unknown persisted task status: {raw_value!r}"
            ) from exc

    def _parse_target_type(self, raw_value: str) -> TaskTargetType:
        try:
            return TaskTargetType(raw_value)
        except ValueError as exc:
            raise TaskRunStorageError(
                f"Unknown persisted task target type: {raw_value!r}"
            ) from exc

    def _parse_datetime(self, raw_value: str | None) -> datetime | None:
        if raw_value is None:
            return None
        try:
            return datetime.fromisoformat(raw_value)
        except ValueError as exc:
            raise TaskRunStorageError(
                f"Invalid persisted datetime value: {raw_value!r}"
            ) from exc

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()

    def _parse_task_kind(self, raw_value: str) -> str:
        if not raw_value.strip():
            raise TaskRunStorageError("Persisted task kind must be a non-empty string.")
        return raw_value

    def _parse_target_id(self, raw_value: str) -> str:
        if not raw_value.strip():
            raise TaskRunStorageError("Persisted target_id must be a non-empty string.")
        return raw_value

    def _parse_error_summary(self, raw_value: str | None) -> str | None:
        if raw_value is None:
            return None
        if not raw_value.strip():
            raise TaskRunStorageError(
                "Persisted error_summary must be null or a non-empty string."
            )
        return raw_value
