import tempfile
from pathlib import Path
import unittest

from engine_cli.application import (
    ServerInstanceLifecycleService,
    ServerInstanceValidationError,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.infrastructure.persistence import SqliteServerInstanceRepository


class TestServerInstanceValidation(unittest.TestCase):
    def test_validate_draft_server_to_configured(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = SqliteServerInstanceRepository(Path(temp_dir) / "engine.db")
            server = ServerInstance(
                server_instance_id="srv-1",
                name="Lobby",
                location=temp_dir,
                command="python -c \"import time; time.sleep(1)\"",
                minecraft_version="1.21.11",
                server_distribution="fabric",
                lifecycle_state=ServerInstanceLifecycleState.DRAFT,
            )

            service = ServerInstanceLifecycleService(server_catalog=repository)
            validated = service.validate(server)

            self.assertIs(validated, server)
            self.assertEqual(
                validated.lifecycle_state,
                ServerInstanceLifecycleState.CONFIGURED,
            )
            persisted_server = repository.get_server("srv-1")
            self.assertIsNotNone(persisted_server)
            assert persisted_server is not None
            self.assertEqual(
                persisted_server.lifecycle_state,
                ServerInstanceLifecycleState.CONFIGURED,
            )

    def test_validate_rejects_missing_location_or_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = SqliteServerInstanceRepository(Path(temp_dir) / "engine.db")
            server = ServerInstance(
                server_instance_id="srv-1",
                name="Lobby",
                location="",
                command="",
                minecraft_version="1.21.11",
                server_distribution="fabric",
                lifecycle_state=ServerInstanceLifecycleState.DRAFT,
            )

            with self.assertRaises(ServerInstanceValidationError):
                ServerInstanceLifecycleService(server_catalog=repository).validate(server)

            self.assertIsNone(repository.get_server("srv-1"))
