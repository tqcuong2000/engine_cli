import tempfile
import unittest

from engine_cli.application import (
    ServerInstanceLifecycleService,
    ServerInstanceValidationError,
)
from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState


class TestServerInstanceValidation(unittest.TestCase):
    def test_validate_draft_server_to_configured(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            server = ServerInstance(
                server_instance_id="srv-1",
                name="Lobby",
                location=temp_dir,
                command="python -c \"import time; time.sleep(1)\"",
                minecraft_version="1.21.11",
                server_distribution="fabric",
                lifecycle_state=ServerInstanceLifecycleState.DRAFT,
            )

            validated = ServerInstanceLifecycleService().validate(server)

            self.assertIs(validated, server)
            self.assertEqual(
                validated.lifecycle_state,
                ServerInstanceLifecycleState.CONFIGURED,
            )

    def test_validate_rejects_missing_location_or_command(self):
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
            ServerInstanceLifecycleService().validate(server)
