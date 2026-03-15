import tempfile
from pathlib import Path
import unittest

from engine_cli.config import JsonConfigError, JsonConfigLoader


class TestJsonConfigLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonConfigLoader()

    def test_load_object_returns_empty_dict_when_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"

            loaded = self.loader.load_object(path)

            self.assertEqual(loaded, {})

    def test_load_object_raises_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text("{invalid", encoding="utf-8")

            with self.assertRaises(JsonConfigError):
                self.loader.load_object(path)

    def test_load_object_rejects_non_object_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text('["not", "an", "object"]', encoding="utf-8")

            with self.assertRaises(JsonConfigError):
                self.loader.load_object(path)
