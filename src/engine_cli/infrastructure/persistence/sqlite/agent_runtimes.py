from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from engine_cli.application.agent_runtimes.repository import AgentRuntimeRepository
from engine_cli.domain import AgentRuntime, AgentRuntimeLifecycleState
from engine_cli.infrastructure.persistence.sqlite.bootstrap import ensure_schema


class AgentRuntimeStorageError(Exception):
    """Raised when persisted agent-runtime data is invalid for durable storage."""


class SqliteAgentRuntimeRepository(AgentRuntimeRepository):
    """SQLite-backed persistence adapter for durable agent runtime records."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        ensure_schema(self.database_path)

    def get_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Return one stored runtime if it exists."""
        query = """
        SELECT
            agent_runtime_id,
            name,
            agent_profile_id,
            server_instance_id,
            agent_kind,
            lifecycle_state
        FROM agent_runtimes
        WHERE agent_runtime_id = ?
        """
        with closing(self._connect()) as connection:
            row = connection.execute(query, (agent_runtime_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_runtime(row)

    def list_runtimes(self) -> list[AgentRuntime]:
        """Return all stored runtimes in insertion order."""
        query = """
        SELECT
            agent_runtime_id,
            name,
            agent_profile_id,
            server_instance_id,
            agent_kind,
            lifecycle_state
        FROM agent_runtimes
        ORDER BY rowid
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query).fetchall()
        return [self._row_to_runtime(row) for row in rows]

    def list_runtimes_for_server(self, server_instance_id: str) -> list[AgentRuntime]:
        """Return all stored runtimes attached to one server in insertion order."""
        query = """
        SELECT
            agent_runtime_id,
            name,
            agent_profile_id,
            server_instance_id,
            agent_kind,
            lifecycle_state
        FROM agent_runtimes
        WHERE server_instance_id = ?
        ORDER BY rowid
        """
        with closing(self._connect()) as connection:
            rows = connection.execute(query, (server_instance_id,)).fetchall()
        return [self._row_to_runtime(row) for row in rows]

    def save_runtime(self, runtime: AgentRuntime) -> AgentRuntime:
        """Insert or replace one stored runtime."""
        validated_runtime = self._validate_runtime(runtime)
        query = """
        INSERT INTO agent_runtimes (
            agent_runtime_id,
            name,
            agent_profile_id,
            server_instance_id,
            agent_kind,
            lifecycle_state
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(agent_runtime_id) DO UPDATE SET
            name = excluded.name,
            agent_profile_id = excluded.agent_profile_id,
            server_instance_id = excluded.server_instance_id,
            agent_kind = excluded.agent_kind,
            lifecycle_state = excluded.lifecycle_state
        """
        with closing(self._connect()) as connection:
            connection.execute(
                query,
                (
                    validated_runtime.agent_runtime_id,
                    validated_runtime.name,
                    validated_runtime.agent_profile_id,
                    validated_runtime.server_instance_id,
                    validated_runtime.agent_kind,
                    validated_runtime.lifecycle_state.value,
                ),
            )
            connection.commit()
        return validated_runtime

    def remove_runtime(self, agent_runtime_id: str) -> AgentRuntime | None:
        """Remove and return one stored runtime if it exists."""
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    agent_runtime_id,
                    name,
                    agent_profile_id,
                    server_instance_id,
                    agent_kind,
                    lifecycle_state
                FROM agent_runtimes
                WHERE agent_runtime_id = ?
                """,
                (agent_runtime_id,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "DELETE FROM agent_runtimes WHERE agent_runtime_id = ?",
                (agent_runtime_id,),
            )
            connection.commit()
        return self._row_to_runtime(row)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_runtime(self, row: sqlite3.Row) -> AgentRuntime:
        return AgentRuntime(
            agent_runtime_id=self._parse_non_empty(
                "agent_runtime_id",
                row["agent_runtime_id"],
            ),
            name=self._parse_non_empty("name", row["name"]),
            agent_profile_id=self._parse_non_empty(
                "agent_profile_id",
                row["agent_profile_id"],
            ),
            server_instance_id=self._parse_non_empty(
                "server_instance_id",
                row["server_instance_id"],
            ),
            agent_kind=self._parse_non_empty("agent_kind", row["agent_kind"]),
            lifecycle_state=self._parse_lifecycle_state(row["lifecycle_state"]),
        )

    def _validate_runtime(self, runtime: AgentRuntime) -> AgentRuntime:
        self._parse_non_empty("agent_runtime_id", runtime.agent_runtime_id)
        self._parse_non_empty("name", runtime.name)
        self._parse_non_empty("agent_profile_id", runtime.agent_profile_id)
        self._parse_non_empty("server_instance_id", runtime.server_instance_id)
        self._parse_non_empty("agent_kind", runtime.agent_kind)
        self._parse_lifecycle_state(runtime.lifecycle_state.value)
        return runtime

    def _parse_lifecycle_state(self, raw_value: str) -> AgentRuntimeLifecycleState:
        try:
            return AgentRuntimeLifecycleState(raw_value)
        except ValueError as exc:
            raise AgentRuntimeStorageError(
                f"Unknown persisted agent runtime lifecycle state: {raw_value!r}"
            ) from exc

    def _parse_non_empty(self, field_name: str, raw_value: str) -> str:
        if not raw_value.strip():
            raise AgentRuntimeStorageError(
                f"Persisted {field_name} must be a non-empty string."
            )
        return raw_value
