import tempfile
from pathlib import Path
import unittest

from engine_cli.application.composition import create_app_runtime
from engine_cli.interfaces.tui.app import EngineCli


class TestAppPersistence(unittest.TestCase):
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

    def test_engine_cli_uses_durable_server_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir)
            server_root = app_root / "server"
            server_root.mkdir()
            self._write_server_files(server_root)
            app = EngineCli(create_app_runtime(app_root=app_root))
            app.server_manager.import_server(
                name="Lobby",
                location=str(server_root),
                command="java -jar fabric.jar --nogui",
            )

            reloaded_app = EngineCli(create_app_runtime(app_root=app_root))
            servers = reloaded_app.server_manager.list_servers()

            self.assertEqual(len(servers), 1)
            self.assertEqual(servers[0].name, "Lobby")
            self.assertEqual(
                reloaded_app.session_context.active_agent_profile_id,
                "base-default",
            )
