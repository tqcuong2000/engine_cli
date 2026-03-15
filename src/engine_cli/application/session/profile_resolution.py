from engine_cli.application.session.context import SessionContext
from engine_cli.application.session.errors import (
    IncompatibleAgentProfileError,
    UnknownAgentProfileError,
)
from engine_cli.config import ResolvedSettings


class AgentProfileSelectionService:
    """Resolve and validate the effective active profile for a session."""

    def resolve_effective_profile_id(
        self,
        *,
        session_context: SessionContext,
        settings: ResolvedSettings,
    ) -> str:
        active_profile_id = session_context.active_agent_profile_id
        if active_profile_id is None:
            return settings.default_profile_id_for(session_context.mode)

        profile = settings.get_profile(active_profile_id)
        if profile is None or profile.mode is not session_context.mode:
            return settings.default_profile_id_for(session_context.mode)
        return active_profile_id

    def select_profile(
        self,
        *,
        session_context: SessionContext,
        settings: ResolvedSettings,
        agent_profile_id: str,
    ) -> str:
        """Validate an explicit profile choice and return its id."""
        profile = settings.get_profile(agent_profile_id)
        if profile is None:
            raise UnknownAgentProfileError(
                f"Unknown agent profile '{agent_profile_id}'."
            )
        if profile.mode is not session_context.mode:
            raise IncompatibleAgentProfileError(
                f"Agent profile '{agent_profile_id}' is not compatible with "
                f"mode '{session_context.mode.value}'."
            )
        return agent_profile_id
