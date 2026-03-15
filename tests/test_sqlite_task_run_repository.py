from contextlib import closing
from datetime import datetime, timedelta
import sqlite3
import tempfile
from pathlib import Path
import unittest

from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType
from engine_cli.infrastructure.persistence.sqlite import (
    SqliteTaskRunRepository,
    TaskRunStorageError,
)


class TestSqliteTaskRunRepository(unittest.TestCase):
    def create_repository(self, database_path: Path) -> SqliteTaskRunRepository:
        return SqliteTaskRunRepository(database_path)

    def create_task(
        self,
        *,
        task_run_id: str = "task-1",
        status: TaskStatus = TaskStatus.RUNNING,
        target_id: str = "srv-1",
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_summary: str | None = None,
    ) -> TaskRun:
        default_started_at = datetime(2026, 3, 15, 12, 0, 0)
        if status is TaskStatus.PENDING:
            started_at = None
            finished_at = None
            error_summary = None
        elif status is TaskStatus.RUNNING:
            started_at = started_at or default_started_at
            finished_at = None
            error_summary = None
        elif status is TaskStatus.FAILED:
            started_at = started_at or default_started_at
            finished_at = finished_at or (started_at + timedelta(seconds=5))
            error_summary = error_summary or "boom"
        else:
            started_at = started_at or default_started_at
            finished_at = finished_at or (started_at + timedelta(seconds=5))
            error_summary = None
        return TaskRun(
            task_run_id=task_run_id,
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id=target_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            error_summary=error_summary,
        )

    def test_sqlite_task_run_repository_persists_and_loads_task_runs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            pending_task = self.create_task(
                task_run_id="task-pending",
                status=TaskStatus.PENDING,
            )
            running_task = self.create_task(
                task_run_id="task-running",
                status=TaskStatus.RUNNING,
            )
            completed_task = self.create_task(
                task_run_id="task-completed",
                status=TaskStatus.COMPLETED,
            )
            repository.save_task(pending_task)
            repository.save_task(running_task)
            repository.save_task(completed_task)

            reloaded_repository = self.create_repository(database_path)
            loaded_running_task = reloaded_repository.get_task("task-running")
            active_tasks = reloaded_repository.list_active_tasks_for_target(
                TaskTargetType.SERVER_INSTANCE,
                "srv-1",
            )
            all_tasks = reloaded_repository.list_tasks()

            self.assertIsNotNone(loaded_running_task)
            assert loaded_running_task is not None
            self.assertEqual(loaded_running_task.status, TaskStatus.RUNNING)
            self.assertEqual(
                [task.task_run_id for task in active_tasks],
                ["task-pending", "task-running"],
            )
            self.assertEqual(
                [task.task_run_id for task in all_tasks],
                ["task-pending", "task-running", "task-completed"],
            )

    def test_sqlite_task_run_repository_rejects_unknown_persisted_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            repository.save_task(self.create_task())
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "UPDATE task_runs SET status = ? WHERE task_run_id = ?",
                    ("unknown", "task-1"),
                )
                connection.commit()

            with self.assertRaises(TaskRunStorageError):
                repository.get_task("task-1")

    def test_sqlite_task_run_repository_rejects_invalid_timestamp_integrity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "engine.db"
            repository = self.create_repository(database_path)
            repository.save_task(self.create_task())
            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    """
                    UPDATE task_runs
                    SET started_at = NULL, finished_at = ?
                    WHERE task_run_id = ?
                    """,
                    (datetime(2026, 3, 15, 12, 0, 5).isoformat(), "task-1"),
                )
                connection.commit()

            with self.assertRaises(TaskRunStorageError):
                repository.get_task("task-1")
