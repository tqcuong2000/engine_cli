from dataclasses import replace
from datetime import datetime
import unittest

from engine_cli.application.execution import (
    ActiveTaskConflictError,
    InMemoryTaskRunCatalog,
    InvalidTaskTransitionError,
    UnsupportedTaskCancellationError,
)
from engine_cli.application.execution.service import ExecutionService
from engine_cli.domain import TaskRun, TaskStatus, TaskTargetType


class RecordingTaskRunCatalog(InMemoryTaskRunCatalog):
    def __init__(self) -> None:
        super().__init__()
        self.saved_tasks: list[TaskRun] = []

    def save_task(self, task: TaskRun) -> TaskRun:
        self.saved_tasks.append(replace(task))
        return super().save_task(task)


class TestExecutionService(unittest.TestCase):
    def test_execution_service_run_task_persists_pending_running_and_completed_states(self):
        catalog = RecordingTaskRunCatalog()
        service = ExecutionService(task_repository=catalog)

        def assert_running_state_is_persisted() -> None:
            stored_tasks = catalog.list_tasks_for_target(
                TaskTargetType.SERVER_INSTANCE,
                "srv-1",
            )
            self.assertEqual(len(stored_tasks), 1)
            self.assertEqual(stored_tasks[0].status, TaskStatus.RUNNING)
            self.assertIsNotNone(stored_tasks[0].started_at)
            self.assertIsNone(stored_tasks[0].finished_at)

        result = service.run_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
            executor=assert_running_state_is_persisted,
        )

        self.assertEqual(result.final_status, TaskStatus.COMPLETED)
        self.assertIsNone(result.error_summary)
        stored_tasks = catalog.list_tasks_for_target(
            TaskTargetType.SERVER_INSTANCE,
            "srv-1",
        )
        self.assertEqual(len(stored_tasks), 1)
        self.assertEqual(stored_tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(
            [task.status for task in catalog.saved_tasks],
            [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED],
        )

    def test_run_task_failure_transitions_to_failed(self):
        service = ExecutionService()

        def raise_failure() -> None:
            raise RuntimeError("boom")

        result = service.run_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
            executor=raise_failure,
        )

        self.assertEqual(result.final_status, TaskStatus.FAILED)
        self.assertEqual(result.error_summary, "boom")

    def test_execution_service_rejects_invalid_status_transition(self):
        service = ExecutionService()
        task = service.create_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
        )

        with self.assertRaises(InvalidTaskTransitionError):
            service.complete_task(task)

    def test_execution_service_rejects_second_active_lifecycle_task_for_same_target(self):
        service = ExecutionService()
        service.create_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
        )

        with self.assertRaises(ActiveTaskConflictError):
            service.create_task(
                task_kind="server_instance.stop",
                target_type=TaskTargetType.SERVER_INSTANCE,
                target_id="srv-1",
            )

    def test_execution_service_rejects_running_task_cancellation_in_v1(self):
        service = ExecutionService()
        task = service.create_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
        )
        service.start_task(task)

        with self.assertRaises(UnsupportedTaskCancellationError):
            service.cancel_task(task)

    def test_execution_service_run_task_is_synchronous_in_v1(self):
        service = ExecutionService()
        result = service.run_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
            executor=lambda: None,
        )

        stored_task = service.get_task(result.task_run_id)

        self.assertIsNotNone(stored_task)
        assert stored_task is not None
        self.assertIn(
            stored_task.status,
            {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        )
        self.assertIsInstance(stored_task.finished_at, datetime)


class TestInMemoryTaskRunCatalog(unittest.TestCase):
    def test_in_memory_task_run_catalog_lists_active_tasks_for_target(self):
        catalog = InMemoryTaskRunCatalog()
        catalog.save_task(
            TaskRun(
                task_run_id="pending-1",
                task_kind="server_instance.start",
                target_type=TaskTargetType.SERVER_INSTANCE,
                target_id="srv-1",
                status=TaskStatus.PENDING,
            )
        )
        catalog.save_task(
            TaskRun(
                task_run_id="running-1",
                task_kind="server_instance.stop",
                target_type=TaskTargetType.SERVER_INSTANCE,
                target_id="srv-1",
                status=TaskStatus.RUNNING,
            )
        )
        catalog.save_task(
            TaskRun(
                task_run_id="done-1",
                task_kind="server_instance.inspect",
                target_type=TaskTargetType.SERVER_INSTANCE,
                target_id="srv-1",
                status=TaskStatus.COMPLETED,
            )
        )
        catalog.save_task(
            TaskRun(
                task_run_id="other-target",
                task_kind="server_instance.start",
                target_type=TaskTargetType.SERVER_INSTANCE,
                target_id="srv-2",
                status=TaskStatus.PENDING,
            )
        )

        tasks = catalog.list_active_tasks_for_target(
            TaskTargetType.SERVER_INSTANCE,
            "srv-1",
        )

        self.assertEqual([task.task_run_id for task in tasks], ["pending-1", "running-1"])
