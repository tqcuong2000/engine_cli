import tempfile
from pathlib import Path
import unittest

from engine_cli.infrastructure.persistence import AppPaths


class TestAppPaths(unittest.TestCase):
    def test_app_paths_create_expected_global_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir) / ".engine_cli"

            paths = AppPaths.from_root(app_root)

            self.assertEqual(paths.app_root, app_root.resolve())
            self.assertEqual(paths.config_dir, app_root.resolve() / "config")
            self.assertEqual(paths.db_dir, app_root.resolve() / "db")
            self.assertEqual(paths.db_path, app_root.resolve() / "db" / "engine.db")
            self.assertEqual(paths.runtime_dir, app_root.resolve() / "runtime")
            self.assertEqual(paths.logs_dir, app_root.resolve() / "logs")
            self.assertTrue(paths.config_dir.is_dir())
            self.assertTrue(paths.db_dir.is_dir())
            self.assertTrue(paths.runtime_dir.is_dir())
            self.assertTrue(paths.logs_dir.is_dir())
