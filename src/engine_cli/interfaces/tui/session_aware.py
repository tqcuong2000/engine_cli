from collections.abc import Callable
from typing import cast

from textual.widget import Widget

from engine_cli.application import SessionCoordinator, SessionSnapshot


class SessionAwareRecomposeMixin:
    """Subscribe to session changes and recompose the widget on update."""

    session_coordinator: SessionCoordinator | None
    _session_unsubscribe: Callable[[], None] | None = None

    def on_mount(self) -> None:
        if self.session_coordinator is None:
            return
        self._session_unsubscribe = self.session_coordinator.subscribe(
            self._handle_session_snapshot
        )

    def on_unmount(self) -> None:
        if self._session_unsubscribe is None:
            return
        self._session_unsubscribe()
        self._session_unsubscribe = None

    def _handle_session_snapshot(self, _snapshot: SessionSnapshot) -> None:
        cast(Widget, self).refresh(recompose=True)
