import unittest

import engine_cli.application
import engine_cli.config
import engine_cli.domain
import engine_cli.infrastructure


class TestPackageImports(unittest.TestCase):
    def test_core_packages_import(self):
        self.assertTrue(hasattr(engine_cli.application, "SessionContext"))
        self.assertTrue(hasattr(engine_cli.domain, "ServerInstance"))
        self.assertIsNotNone(engine_cli.config)
        self.assertIsNotNone(engine_cli.infrastructure)
