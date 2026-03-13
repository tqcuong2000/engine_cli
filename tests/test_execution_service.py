import unittest

from engine_cli.application.execution.service import ExecutionService
from engine_cli.domain import TaskStatus, TaskTargetType


class TestExecutionService(unittest.TestCase):
    def test_run_task_success_transitions_to_completed(self):
        service = ExecutionService()

        result = service.run_task(
            task_kind="server_instance.start",
            target_type=TaskTargetType.SERVER_INSTANCE,
            target_id="srv-1",
            executor=lambda: None,
        )

        self.assertEqual(result.final_status, TaskStatus.COMPLETED)
        self.assertIsNone(result.error_summary)

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
