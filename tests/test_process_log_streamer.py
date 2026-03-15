import io
import sys
import tempfile
import time
import unittest

from engine_cli.application import ServerTerminalBuffer
from engine_cli.infrastructure.process import LocalProcessManager, ProcessLogStreamer


class TestProcessLogStreamer(unittest.TestCase):
    def test_streamer_reads_lines_from_text_stream(self):
        terminal_buffer = ServerTerminalBuffer()
        stream = io.StringIO("first line\nsecond line\n")
        streamer = ProcessLogStreamer(stream, terminal_buffer.append)

        streamer.start()
        streamer.join(timeout=1.0)

        self.assertEqual(
            [line.raw for line in terminal_buffer.snapshot()],
            ["first line", "second line"],
        )

    def test_local_process_manager_merges_stderr_into_stdout_stream(self):
        manager = LocalProcessManager()
        command = (
            f'"{sys.executable}" -u -c "import sys; '
            "print('stdout line'); print('stderr line', file=sys.stderr)\""
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            handle = manager.start(command, temp_dir)
            terminal_buffer = ServerTerminalBuffer()
            self.assertIsNone(handle.process.stderr)
            self.assertIsNotNone(handle.process.stdout)

            streamer = manager.create_log_streamer(handle, terminal_buffer.append)
            handle.log_streamer = streamer
            streamer.start()

            deadline = time.time() + 1.0
            while time.time() < deadline and len(terminal_buffer) < 2:
                time.sleep(0.01)

            manager.stop(handle)
            streamer.join(timeout=1.0)

            self.assertEqual(
                [line.raw for line in terminal_buffer.snapshot()],
                ["stdout line", "stderr line"],
            )
