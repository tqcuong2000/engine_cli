from dataclasses import dataclass
from pathlib import Path
import re


class ServerInspectionError(Exception):
    """Raised when the server directory cannot be inspected into a valid shape."""


@dataclass
class ServerInspectionResult:
    """Derived metadata from a local Minecraft server directory."""

    location: str
    minecraft_version: str
    server_distribution: str


class MinecraftServerInspector:
    """Inspect local Minecraft server folders and derive a server candidate."""

    def inspect(self, location: str) -> ServerInspectionResult:
        """Inspect a local server directory and derive metadata for import."""
        root = Path(location)
        if not root.is_dir():
            raise ServerInspectionError(f"Server location does not exist: {location}")

        self._read_server_properties(root)
        latest_log = self._read_latest_log(root)
        minecraft_version = self._derive_version(root, latest_log)
        server_distribution = self._derive_distribution(root, latest_log)

        return ServerInspectionResult(
            location=str(root),
            minecraft_version=minecraft_version,
            server_distribution=server_distribution,
        )

    def suggest_start_command(self, location: str) -> str | None:
        """Return a default Java launch command when the server root and jar are present."""
        root = Path(location)
        if not root.is_dir():
            return None
        properties = root / "server.properties"
        if not properties.is_file():
            return None
        jar_path = self._find_launch_jar(root)
        if jar_path is None:
            return None
        return f"java -Xms2G -Xmx2G -Xmn512m -jar {jar_path.name} --nogui"

    def _read_server_properties(self, root: Path) -> str:
        """Read server.properties to confirm the directory is a valid server root."""
        properties = root / "server.properties"
        if not properties.is_file():
            raise ServerInspectionError("Missing server.properties in server root.")
        return properties.read_text(encoding="utf-8")

    def _read_latest_log(self, root: Path) -> str:
        """Read the latest server log if present, otherwise return an empty string."""
        latest_log = root / "logs" / "latest.log"
        if latest_log.is_file():
            return latest_log.read_text(encoding="utf-8")
        return ""

    def _derive_version(self, root: Path, latest_log: str) -> str:
        """Derive the Minecraft version from logs first, then fall back to jar paths."""
        for pattern in (
            r"Loading Minecraft\s+([0-9A-Za-z.\-+]+)",
            r"Starting minecraft server version\s+([0-9A-Za-z.\-+]+)",
        ):
            match = re.search(pattern, latest_log)
            if match:
                return match.group(1)

        jar_match = re.search(
            r"versions[\\/](?P<version>[^\\/]+)[\\/].*?\.jar",
            "\n".join(str(path) for path in root.rglob("*.jar")),
        )
        if jar_match:
            return jar_match.group("version")

        raise ServerInspectionError("Could not derive Minecraft version from server files.")

    def _derive_distribution(self, root: Path, latest_log: str) -> str:
        """Infer the server distribution from jar names and log content."""
        jar_listing = "\n".join(path.name for path in root.rglob("*.jar"))
        source = f"{jar_listing}\n{latest_log}".lower()
        if "fabric" in source:
            return "fabric"
        if "paper" in source:
            return "paper"
        if "forge" in source:
            return "forge"
        return "vanilla"

    def _find_launch_jar(self, root: Path) -> Path | None:
        """Return the most likely root-level launch jar for a local server."""
        candidates = sorted(root.glob("*.jar"))
        if not candidates:
            return None

        def sort_key(path: Path) -> tuple[int, str]:
            name = path.name.lower()
            if name == "fabric.jar":
                return (0, name)
            if "paper" in name:
                return (1, name)
            if "forge" in name:
                return (2, name)
            if "server" in name:
                return (3, name)
            return (4, name)

        return min(candidates, key=sort_key)
