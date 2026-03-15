from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Resolved application storage roots for config, database, runtime, and logs."""

    app_root: Path
    config_dir: Path
    db_dir: Path
    db_path: Path
    runtime_dir: Path
    logs_dir: Path

    @classmethod
    def from_root(cls, app_root: Path | None = None) -> "AppPaths":
        """Create application paths rooted at the provided directory or the user home."""
        root = (app_root or (Path.home() / ".engine_cli")).expanduser().resolve()
        config_dir = root / "config"
        db_dir = root / "db"
        runtime_dir = root / "runtime"
        logs_dir = root / "logs"

        for directory in (root, config_dir, db_dir, runtime_dir, logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

        return cls(
            app_root=root,
            config_dir=config_dir,
            db_dir=db_dir,
            db_path=db_dir / "engine.db",
            runtime_dir=runtime_dir,
            logs_dir=logs_dir,
        )
