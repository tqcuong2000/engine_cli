import sys
import tempfile
from pathlib import Path
import unittest

from engine_cli.application.composition import create_app_runtime
from engine_cli.domain import AgentRuntimeLifecycleState, OperatingMode, TaskStatus


class TestAgentRuntimeVerticalSlice(unittest.TestCase):
    def _write_server_files(self, root: Path) -> None:
        (root / "logs").mkdir()
        (root / "versions" / "1.21.11").mkdir(parents=True)
        (root / "server.properties").write_text("motd=Lobby\n", encoding="utf-8")
        (root / "logs" / "latest.log").write_text(
            "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
            encoding="utf-8",
        )
        (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
            "",
            encoding="utf-8",
        )

    def test_runtime_services_are_reachable_end_to_end_without_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)
            server_root = app_root / "server"
            server_root.mkdir()
            self._write_server_files(server_root)
            runtime = create_app_runtime(app_root=app_root)
            server = runtime.server_manager.import_server(
                name="Lobby",
                location=str(server_root),
                command=(
                    f'"{sys.executable}" -u -c "import time; print(\'server booted\'); '
                    'time.sleep(30)"'
                ),
            )
            profile = runtime.settings.default_profile_for(OperatingMode.SERVER)

            runtime.lifecycle_service.validate(server)
            server_start_task = runtime.lifecycle_service.start(server)
            agent_runtime = runtime.agent_runtime_manager.create_runtime(
                name="Ops Bot",
                agent_profile=profile,
                server=server,
            )
            validated_runtime = runtime.agent_runtime_lifecycle_service.validate(
                agent_runtime,
                server,
            )
            start_task = runtime.agent_runtime_lifecycle_service.start(
                validated_runtime,
                server,
            )
            stop_task = runtime.agent_runtime_lifecycle_service.stop(validated_runtime)

            self.assertEqual(server_start_task.status, TaskStatus.COMPLETED)
            self.assertEqual(start_task.status, TaskStatus.COMPLETED)
            self.assertEqual(stop_task.status, TaskStatus.COMPLETED)
            persisted_runtime = runtime.agent_runtime_manager.get_runtime(
                validated_runtime.agent_runtime_id
            )
            self.assertIsNotNone(persisted_runtime)
            assert persisted_runtime is not None
            persisted_server = runtime.server_manager.get_server(server.server_instance_id)
            self.assertIsNotNone(persisted_server)
            assert persisted_server is not None
            self.assertEqual(
                persisted_runtime.lifecycle_state,
                AgentRuntimeLifecycleState.STOPPED,
            )
            self.assertEqual(
                persisted_server.attached_agents,
                [validated_runtime.agent_runtime_id],
            )
            persisted_tasks = runtime.agent_runtime_lifecycle_service.execution_service.list_tasks_for_target(
                start_task.target_type,
                start_task.target_id,
            )
            self.assertEqual(
                [persisted_task.task_kind for persisted_task in persisted_tasks],
                ["agent_runtime.start", "agent_runtime.stop"],
            )

            runtime.lifecycle_service.stop(server)
