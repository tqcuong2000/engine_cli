import tempfile
from pathlib import Path
import unittest

from engine_cli.infrastructure.minecraft import (
    MinecraftServerInspector,
    ServerInspectionError,
)


class TestMinecraftServerInspector(unittest.TestCase):
    def test_inspect_server_directory_derives_required_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs").mkdir()
            (root / "versions" / "1.21.11").mkdir(parents=True)
            (root / "server.properties").write_text(
                "level-name=world\nserver-port=30066\n",
                encoding="utf-8",
            )
            (root / "logs" / "latest.log").write_text(
                "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
                encoding="utf-8",
            )
            (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
                "",
                encoding="utf-8",
            )

            result = MinecraftServerInspector().inspect(str(root))

            self.assertEqual(result.location, str(root))
            self.assertEqual(result.minecraft_version, "1.21.11")
            self.assertEqual(result.server_distribution, "fabric")

    def test_inspect_does_not_require_start_command_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs").mkdir()
            (root / "versions" / "1.21.11").mkdir(parents=True)
            (root / "server.properties").write_text("level-name=world\n", encoding="utf-8")
            (root / "logs" / "latest.log").write_text(
                "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
                encoding="utf-8",
            )
            (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
                "",
                encoding="utf-8",
            )

            result = MinecraftServerInspector().inspect(str(root))

            self.assertEqual(result.minecraft_version, "1.21.11")

    def test_inspect_rejects_missing_server_properties(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with self.assertRaises(ServerInspectionError):
                MinecraftServerInspector().inspect(str(root))

    def test_import_server_requires_explicit_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "logs").mkdir()
            (root / "versions" / "1.21.11").mkdir(parents=True)
            (root / "server.properties").write_text("level-name=world\n", encoding="utf-8")
            (root / "logs" / "latest.log").write_text(
                "[22:37:58] [main/INFO]: Loading Minecraft 1.21.11 with Fabric Loader 0.18.4\n",
                encoding="utf-8",
            )
            (root / "versions" / "1.21.11" / "server-1.21.11.jar").write_text(
                "",
                encoding="utf-8",
            )

            server = MinecraftServerInspector().import_server(
                server_instance_id="srv-1",
                name="Lobby",
                location=str(root),
                command="java -Xmx2G -jar fabric.jar --nogui",
            )

            self.assertEqual(server.command, "java -Xmx2G -jar fabric.jar --nogui")
