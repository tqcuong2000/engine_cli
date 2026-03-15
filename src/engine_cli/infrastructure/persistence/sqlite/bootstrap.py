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
"""


def ensure_schema(database_path: Path) -> None:
    """Create the SQLite database file and required schema if missing."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(SCHEMA)
        connection.commit()
