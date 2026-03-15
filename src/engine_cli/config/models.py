from dataclasses import dataclass
from typing import Mapping

from engine_cli.config.errors import ConfigResolutionError


@dataclass(frozen=True)
class ResolvedSettings:
    """Minimal structured view of resolved application settings."""

    default_agent_profile_id: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "ResolvedSettings":
        profile_id = values.get("default_agent_profile_id")
        if not isinstance(profile_id, str):
            raise ConfigResolutionError(
                "Resolved setting 'default_agent_profile_id' must be a string."
            )
        return cls(default_agent_profile_id=profile_id)
