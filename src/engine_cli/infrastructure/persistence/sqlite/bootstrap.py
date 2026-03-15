from contextlib import closing
from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS server_instances (
    server_instance_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    command TEXT NOT NULL,
    minecraft_version TEXT NOT NULL,
    server_distribution TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    attached_agents_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS agent_runtimes (
    agent_runtime_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    agent_profile_id TEXT NOT NULL,
    server_instance_id TEXT NOT NULL,
    agent_kind TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_runtimes_server
    ON agent_runtimes(server_instance_id);

CREATE INDEX IF NOT EXISTS idx_agent_runtimes_profile
    ON agent_runtimes(agent_profile_id);

CREATE TABLE IF NOT EXISTS task_runs (
    task_run_id TEXT PRIMARY KEY,
    task_kind TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NULL,
    finished_at TEXT NULL,
    error_summary TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_task_runs_target
    ON task_runs(target_type, target_id);

CREATE INDEX IF NOT EXISTS idx_task_runs_status
    ON task_runs(status);
"""


def ensure_schema(database_path: Path) -> None:
    """Create the SQLite database file and required schema if missing."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
