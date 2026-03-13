import sys
import tempfile
import unittest

from engine_cli.infrastructure.process import LocalProcessManager


class TestLocalProcessManager(unittest.TestCase):
    def test_start_and_stop_process(self):
        manager = LocalProcessManager()
        command = f'"{sys.executable}" -c "import time; time.sleep(30)"'

        with tempfile.TemporaryDirectory() as temp_dir:
            handle = manager.start(command, temp_dir)
            self.assertTrue(manager.is_running(handle))

            manager.stop(handle)

            self.assertFalse(manager.is_running(handle))
