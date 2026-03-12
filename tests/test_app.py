import unittest

from engine_cli.interfaces.tui.app import EngineCli


class TestApp(unittest.TestCase):
    def test_app_init(self):
        app = EngineCli()
        self.assertEqual(app.title, "EngineCli")


if __name__ == "__main__":
    unittest.main()
