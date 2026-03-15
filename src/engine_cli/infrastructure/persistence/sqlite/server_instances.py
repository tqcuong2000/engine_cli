from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3

from engine_cli.domain import ServerInstance, ServerInstanceLifecycleState
from engine_cli.infrastructure.persistence.sqlite.bootstrap import ensure_schema


STABLE_SERVER_STATES = frozenset(
    {
        ServerInstanceLifecycleState.DRAFT,
        ServerInstanceLifecycleState.CONFIGURED,
        ServerInstanceLifecycleState.STOPPED,
        ServerInstanceLifecycleState.FAILED,
    }
)


class ServerInstanceStorageError(Exception):
    """Raised when persisted server data is invalid for durable storage."""


class SqliteServerInstanceRepository:
    """SQLite-backed persistence adapter for durable server instance records."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        ensure_schema(self.database_path)

    def list_servers(self) -> list[ServerInstance]:
        """Return all stored server instances in insertion order."""
        query = """
        SELECT
            server_instance_id,
            name,
            location,
            command,
            minecraft_version,
            server_distribution,
            lifecycle_state,
            attached_agents_json
        FROM server_instances
        ORDER BY rowid
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query).fetchall()
        return [self._row_to_server(row) for row in rows]

    def get_server(self, server_instance_id: str) -> ServerInstance | None:
        """Return one stored server instance if it exists."""
        query = """
        SELECT
            server_instance_id,
            name,
            location,
            command,
            minecraft_version,
            server_distribution,
            lifecycle_state,
            attached_agents_json
        FROM server_instances
        WHERE server_instance_id = ?
        """
        with closing(self._connect()) as connection:
            row = connection.execute(query, (server_instance_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_server(row)

    def save_server(self, server: ServerInstance) -> ServerInstance:
        """Insert or replace one stored server instance."""
        lifecycle_state = self._validate_persistable_state(server.lifecycle_state)
        query = """
        INSERT INTO server_instances (
            server_instance_id,
            name,
            location,
            command,
            minecraft_version,
            server_distribution,
            lifecycle_state,
            attached_agents_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(server_instance_id) DO UPDATE SET
            name = excluded.name,
            location = excluded.location,
            command = excluded.command,
            minecraft_version = excluded.minecraft_version,
            server_distribution = excluded.server_distribution,
            lifecycle_state = excluded.lifecycle_state,
            attached_agents_json = excluded.attached_agents_json
        """
        attached_agents_json = json.dumps(server.attached_agents)
        with closing(self._connect()) as connection:
            connection.execute(
                query,
                (
                    server.server_instance_id,
                    server.name,
                    server.location,
                    server.command,
                    server.minecraft_version,
                    server.server_distribution,
                    lifecycle_state.value,
                    attached_agents_json,
                ),
            )
            connection.commit()
        return server

    def remove_server(self, server_instance_id: str) -> ServerInstance | None:
        """Remove and return one stored server instance if it exists."""
        existing = self.get_server(server_instance_id)
        if existing is None:
            return None
        with closing(self._connect()) as connection:
            connection.execute(
                "DELETE FROM server_instances WHERE server_instance_id = ?",
                (server_instance_id,),
            )
            connection.commit()
        return existing

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_server(self, row: sqlite3.Row) -> ServerInstance:
        lifecycle_state = self._parse_persisted_state(row["lifecycle_state"])
        attached_agents = self._parse_attached_agents(row["attached_agents_json"])
        return ServerInstance(
            server_instance_id=row["server_instance_id"],
            name=row["name"],
            location=row["location"],
            command=row["command"],
            minecraft_version=row["minecraft_version"],
            server_distribution=row["server_distribution"],
            lifecycle_state=lifecycle_state,
            attached_agents=attached_agents,
        )

    def _parse_persisted_state(self, raw_value: str) -> ServerInstanceLifecycleState:
        try:
            lifecycle_state = ServerInstanceLifecycleState(raw_value)
        except ValueError as exc:
            raise ServerInstanceStorageError(
                f"Unknown persisted server lifecycle state: {raw_value!r}"
            ) from exc
        return self._validate_persistable_state(lifecycle_state)

    def _validate_persistable_state(
        self,
        lifecycle_state: ServerInstanceLifecycleState,
    ) -> ServerInstanceLifecycleState:
        if lifecycle_state not in STABLE_SERVER_STATES:
            raise ServerInstanceStorageError(
                "Transient runtime lifecycle states are not valid durable storage values: "
                f"{lifecycle_state.value!r}"
            )
        return lifecycle_state

    def _parse_attached_agents(self, raw_value: str) -> list[str]:
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ServerInstanceStorageError("Invalid attached_agents JSON payload.") from exc
        if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
            raise ServerInstanceStorageError(
                "Persisted attached_agents must decode to a list of strings."
            )
        return decoded
