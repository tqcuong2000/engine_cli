from collections.abc import Mapping
from dataclasses import dataclass

from engine_cli.config.errors import ProfileConfigError
from engine_cli.domain import AgentProfile, OperatingMode


@dataclass(frozen=True)
class ResolvedSettings:
    """Structured resolved settings including the profile catalog."""

    default_agent_profiles: dict[OperatingMode, str]
    agent_profiles: dict[str, AgentProfile]

    @property
    def default_agent_profile_id(self) -> str:
        """Compatibility shim until startup becomes fully mode-aware."""
        return self.default_profile_id_for(OperatingMode.BASE)

    def default_profile_id_for(self, mode: OperatingMode) -> str:
        return self.default_agent_profiles[mode]

    def default_profile_for(self, mode: OperatingMode) -> AgentProfile:
        return self.agent_profiles[self.default_profile_id_for(mode)]

    def get_profile(self, agent_profile_id: str) -> AgentProfile | None:
        return self.agent_profiles.get(agent_profile_id)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "ResolvedSettings":
        profiles = _parse_agent_profiles(values.get("agent_profiles"))
        default_agent_profiles = _parse_default_agent_profiles(
            values.get("default_agent_profiles"),
            profiles,
        )
        return cls(
            default_agent_profiles=default_agent_profiles,
            agent_profiles=profiles,
        )


def _parse_agent_profiles(raw_profiles: object) -> dict[str, AgentProfile]:
    if not isinstance(raw_profiles, list):
        raise ProfileConfigError("Resolved setting 'agent_profiles' must be a list.")

    profiles: dict[str, AgentProfile] = {}
    for index, raw_profile in enumerate(raw_profiles):
        if not isinstance(raw_profile, Mapping):
            raise ProfileConfigError(
                f"Agent profile at index {index} must be an object."
            )
        agent_profile_id = _require_string(
            raw_profile,
            "agent_profile_id",
            context=f"Agent profile at index {index}",
        )
        if agent_profile_id in profiles:
            raise ProfileConfigError(
                f"Duplicate agent profile id '{agent_profile_id}'."
            )
        mode_value = _require_string(
            raw_profile,
            "mode",
            context=f"Agent profile '{agent_profile_id}'",
        )
        try:
            mode = OperatingMode(mode_value)
        except ValueError as exc:
            raise ProfileConfigError(
                f"Agent profile '{agent_profile_id}' has invalid mode '{mode_value}'."
            ) from exc
        profiles[agent_profile_id] = AgentProfile(
            agent_profile_id=agent_profile_id,
            name=_require_string(
                raw_profile,
                "name",
                context=f"Agent profile '{agent_profile_id}'",
            ),
            mode=mode,
            agent_kind=_require_string(
                raw_profile,
                "agent_kind",
                context=f"Agent profile '{agent_profile_id}'",
            ),
        )
    return profiles


def _parse_default_agent_profiles(
    raw_defaults: object,
    profiles: Mapping[str, AgentProfile],
) -> dict[OperatingMode, str]:
    if not isinstance(raw_defaults, Mapping):
        raise ProfileConfigError(
            "Resolved setting 'default_agent_profiles' must be an object."
        )

    valid_modes = {mode.value for mode in OperatingMode}
    unknown_modes = sorted(str(key) for key in raw_defaults if key not in valid_modes)
    if unknown_modes:
        raise ProfileConfigError(
            "Resolved setting 'default_agent_profiles' contains unknown modes: "
            + ", ".join(unknown_modes)
            + "."
        )

    defaults: dict[OperatingMode, str] = {}
    for mode in OperatingMode:
        profile_id = raw_defaults.get(mode.value)
        if not isinstance(profile_id, str):
            raise ProfileConfigError(
                f"Resolved default agent profile for mode '{mode.value}' must be a string."
            )
        profile = profiles.get(profile_id)
        if profile is None:
            raise ProfileConfigError(
                f"Resolved default agent profile for mode '{mode.value}' "
                f"references unknown profile '{profile_id}'."
            )
        if profile.mode is not mode:
            raise ProfileConfigError(
                f"Resolved default agent profile for mode '{mode.value}' "
                f"references profile '{profile_id}' with mode '{profile.mode.value}'."
            )
        defaults[mode] = profile_id
    return defaults


def _require_string(
    values: Mapping[str, object],
    key: str,
    *,
    context: str,
) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ProfileConfigError(f"{context} field '{key}' must be a string.")
    return value
