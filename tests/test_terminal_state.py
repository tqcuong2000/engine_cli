import unittest

from engine_cli.application import (
    ServerTerminalBuffer,
    ServerTerminalStore,
    parse_terminal_log_line,
)


class TestTerminalState(unittest.TestCase):
    def test_parse_minecraft_log_line_extracts_timestamp_and_level(self):
        line = parse_terminal_log_line(
            "[22:38:09] [Server thread/INFO]: Starting minecraft server version 1.21.11"
        )

        self.assertEqual(line.timestamp, "22:38:09")
        self.assertEqual(line.level, "INFO")
        self.assertIn("Starting minecraft server version", line.raw)

    def test_parse_unmatched_line_preserves_raw_text(self):
        line = parse_terminal_log_line("plain output without minecraft formatting")

        self.assertEqual(line.raw, "plain output without minecraft formatting")
        self.assertIsNone(line.timestamp)
        self.assertIsNone(line.level)

    def test_terminal_buffer_truncates_and_can_clear(self):
        buffer = ServerTerminalBuffer(max_lines=2)

        buffer.append("line 1")
        buffer.append("line 2")
        buffer.append("line 3")

        self.assertEqual([line.raw for line in buffer.snapshot()], ["line 2", "line 3"])

        buffer.clear()

        self.assertEqual(buffer.snapshot(), [])

    def test_terminal_store_returns_stable_buffers(self):
        store = ServerTerminalStore(default_max_lines=5)

        first = store.get_buffer("srv-1")
        second = store.get_buffer("srv-1")
        other = store.get_buffer("srv-2")

        self.assertIs(first, second)
        self.assertIsNot(first, other)
        self.assertEqual(first.max_lines, 5)
