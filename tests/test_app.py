import tempfile
import json
from pathlib import Path
from typing import Any, cast
import unittest
from unittest import mock

from engine_cli.application.composition import create_app_runtime
from engine_cli.domain import OperatingMode
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
import engine_cli.interfaces.tui.app as app_module
from engine_cli.interfaces.tui.app import EngineCli
from engine_cli.interfaces.tui.main.user_inputs import UserInputs


class TestApp(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.app_root = Path(self._temp_dir.name)
        self.workspace_root = self.app_root / "workspace"
        self.workspace_root.mkdir()

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def create_app(self, *, workspace_root: Path | None = None) -> EngineCli:
        return EngineCli(
            create_app_runtime(
                app_root=self.app_root,
                workspace_root=workspace_root,
            )
        )

    def test_app_init(self):
        app = self.create_app()
        self.assertEqual(app.title, "EngineCli")
        self.assertIsNotNone(app.terminal_store)
        self.assertIsNotNone(app.server_manager)
        self.assertEqual(app.app_paths.db_path, self.app_root / "db" / "engine.db")
        self.assertEqual(app.session_context.active_agent_profile_id, "base-default")

    def test_engine_cli_applies_default_agent_profile_from_resolved_config(self):
        settings_path = self.app_root / "config" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "default_agent_profiles": {
                        "base": "global-base",
                        "server": "server-default",
                        "datapack": "datapack-default",
                    },
                    "agent_profiles": [
                        {
                            "agent_profile_id": "global-base",
                            "name": "Global Base",
                            "mode": "base",
                            "agent_kind": "system_assistant",
                        },
                        {
                            "agent_profile_id": "server-default",
                            "name": "Server Ops",
                            "mode": "server",
                            "agent_kind": "server_ops",
                        },
                        {
                            "agent_profile_id": "datapack-default",
                            "name": "Datapack Dev",
                            "mode": "datapack",
                            "agent_kind": "datapack_dev",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        app = self.create_app()

        self.assertEqual(app.session_context.active_agent_profile_id, "global-base")

    def test_run_uses_current_working_directory_when_workspace_root_is_not_provided(self):
        runtime = object()
        with (
            mock.patch.object(app_module.Path, "cwd", return_value=self.workspace_root),
            mock.patch.object(app_module, "create_app_runtime", return_value=runtime) as create_runtime,
            mock.patch.object(app_module, "EngineCli") as engine_cli_cls,
        ):
            app_module.run()

        create_runtime.assert_called_once_with(
            app_root=None,
            workspace_root=self.workspace_root,
        )
        engine_cli_cls.assert_called_once_with(runtime)
        engine_cli_cls.return_value.run.assert_called_once_with()

    def test_app_bindings_include_mode_and_panel_controls(self):
        app = self.create_app()
        binding_keys = {
            binding[0] if isinstance(binding, tuple) else binding.key
            for binding in app.BINDINGS
        }
        self.assertTrue({"b", "s", "p", "[", "]"}.issubset(binding_keys))

    def test_base_mode_action_updates_session_context(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_base_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertEqual(app.session_context.active_agent_profile_id, "base-default")

    def test_server_mode_action_requires_selected_server(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_server_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertIsNone(app.session_context.active_server_instance_id)

    def test_datapack_mode_action_requires_selected_server(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None

        app.action_set_datapack_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertIsNone(app.session_context.active_server_instance_id)

    def test_server_mode_action_switches_with_real_selected_server(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")

        app.action_set_server_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)
        self.assertEqual(app.session_context.active_agent_profile_id, "server-default")

    def test_base_mode_action_re_resolves_incompatible_profile(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        app.action_set_server_mode()

        app.action_set_base_mode()

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertEqual(app.session_context.active_agent_profile_id, "base-default")

    def test_server_selection_updates_session_context(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)

        app._handle_server_select("srv-1")

        self.assertEqual(app.session_context.active_server_instance_id, "srv-1")
        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)
        self.assertEqual(app.session_context.active_agent_profile_id, "server-default")

    def test_start_server_uses_repository_backed_instance(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        captured: list[ServerInstance] = []
        cast(Any, app.lifecycle_service).start = (
            lambda server: captured.append(server) or object()
        )

        app._handle_start_server()

        self.assertEqual(captured, [server])
        self.assertEqual(app.session_context.mode, OperatingMode.SERVER)
        self.assertEqual(app.session_context.active_agent_profile_id, "server-default")

    def test_remove_active_server_re_resolves_profile_for_base_mode(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        app.action_set_server_mode()

        app._handle_remove_server_result("srv-1", True)

        self.assertEqual(app.session_context.mode, OperatingMode.BASE)
        self.assertIsNone(app.session_context.active_server_instance_id)
        self.assertEqual(app.session_context.active_agent_profile_id, "base-default")

    def test_stop_server_uses_runtime_handle_backed_instance(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        cast(Any, app.lifecycle_service).get_handle = lambda _server_id: object()
        captured: list[ServerInstance] = []
        cast(Any, app.lifecycle_service).stop = (
            lambda server: captured.append(server) or object()
        )

        app._handle_stop_server()

        self.assertEqual(len(captured), 1)
        self.assertEqual(
            captured[0].lifecycle_state,
            ServerInstanceLifecycleState.RUNNING,
        )

    def test_start_server_validates_draft_server_before_start(self):
        app = self.create_app()
        app._refresh_mode_aware_widgets = lambda: None
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.DRAFT,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        called_with: list[ServerInstance] = []
        cast(Any, app.lifecycle_service).start = (
            lambda server: called_with.append(server) or object()
        )

        app._handle_start_server()

        self.assertEqual(len(called_with), 1)
        self.assertEqual(
            called_with[0].lifecycle_state,
            ServerInstanceLifecycleState.CONFIGURED,
        )

    def test_server_mode_input_submission_routes_to_command_service(self):
        app = self.create_app()
        app.notify = lambda *args, **kwargs: None
        server = ServerInstance(
            server_instance_id="srv-1",
            name="Lobby",
            location="X:/servers/lobby",
            command="java -jar server.jar nogui",
            minecraft_version="1.21.11",
            server_distribution="fabric",
            lifecycle_state=ServerInstanceLifecycleState.CONFIGURED,
        )
        app.server_manager.catalog.save_server(server)
        app.session_context.select_server("srv-1")
        app.session_context.switch_mode(OperatingMode.SERVER)
        captured: list[tuple[ServerInstance, str]] = []
        cast(Any, app.server_command_service).send = lambda server, command: captured.append(
            (server, command)
        )
        submitted_control = _StubUserInputs("say hello")

        app.on_user_inputs_submitted(
            UserInputs.Submitted(cast(Any, submitted_control), "say hello")
        )

        self.assertEqual(captured, [(server, "say hello")])
        self.assertTrue(submitted_control.cleared)

    def test_non_server_mode_input_submission_is_ignored(self):
        app = self.create_app()
        submitted_control = _StubUserInputs("hello")
        called: list[bool] = []
        cast(Any, app.server_command_service).send = lambda *args, **kwargs: called.append(True)

        app.on_user_inputs_submitted(
            UserInputs.Submitted(cast(Any, submitted_control), "hello")
        )

        self.assertFalse(called)
        self.assertFalse(submitted_control.cleared)


class _StubUserInputs:
    def __init__(self, value: str) -> None:
        self.value = value
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True


if __name__ == "__main__":
    unittest.main()
