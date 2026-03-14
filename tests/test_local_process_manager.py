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

    def test_send_command_writes_to_process_stdin(self):
        manager = LocalProcessManager()
        command = (
            f'"{sys.executable}" -c '
            '"import sys; '
            "print(sys.stdin.readline().strip(), flush=True)"
            '"'
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            handle = manager.start(command, temp_dir)
            try:
                manager.send_command(handle, "list")
                output = handle.process.stdout.readline().strip() if handle.process.stdout else ""
            finally:
                manager.stop(handle)

            self.assertEqual(output, "list")
