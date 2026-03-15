from dataclasses import dataclass


@dataclass
class ServerInspectionResult:
    """Application-owned metadata derived from inspecting a candidate server root."""

    location: str
    minecraft_version: str
    server_distribution: str
