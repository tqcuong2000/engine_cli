from collections.abc import Callable

from engine_cli.application.session.context import SessionContext
from engine_cli.application.session.snapshot import SessionSnapshot
from engine_cli.domain import OperatingMode

type SessionListener = Callable[[SessionSnapshot], None]


class SessionCoordinator:
    """Own session mutations and notify listeners after accepted changes."""

    def __init__(self, context: SessionContext) -> None:
        self._context = context
        self._listeners: list[SessionListener] = []

    @property
    def context(self) -> SessionContext:
        """Expose the underlying session context as the source of truth."""
        return self._context

    def snapshot(self) -> SessionSnapshot:
        """Return an immutable snapshot of the current session state."""
        return SessionSnapshot.from_context(self._context)

    def subscribe(self, listener: SessionListener) -> Callable[[], None]:
        """Register a listener and return an unsubscribe callback."""
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def switch_mode(self, mode: OperatingMode) -> SessionSnapshot:
        """Switch session mode and notify listeners after success."""
        self._context.switch_mode(mode)
        return self._notify()

    def select_server(self, server_instance_id: str) -> SessionSnapshot:
        """Update the active server selection and notify listeners."""
        self._context.select_server(server_instance_id)
        return self._notify()

    def clear_server_selection(self) -> SessionSnapshot:
        """Clear the active server selection and notify listeners."""
        self._context.clear_server_selection()
        return self._notify()

    def set_agent_profile(self, agent_profile_id: str | None) -> SessionSnapshot:
        """Update the active agent profile and notify listeners."""
        self._context.set_agent_profile(agent_profile_id)
        return self._notify()

    def _notify(self) -> SessionSnapshot:
        snapshot = self.snapshot()
        for listener in list(self._listeners):
            listener(snapshot)
        return snapshot
