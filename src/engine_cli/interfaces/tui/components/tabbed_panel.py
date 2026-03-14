from dataclasses import dataclass
from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Click
from textual.widget import Widget
from textual.widgets import Static


@dataclass(frozen=True)
class PanelTabDefinition:
    """Definition of one tab inside a tabbed panel frame."""

    key: str
    title: str
    view_factory: Callable[[Any], Widget]


class TabbedPanelFrame(Widget):
    """Reusable panel frame with header chrome and tab cycling."""

    def __init__(self, view_context: object) -> None:
        super().__init__()
        self.view_context = view_context
        self.active_tab_index = 0

    @property
    def tabs(self) -> tuple[PanelTabDefinition, ...]:
        """Return the tab definitions for this frame."""
        raise NotImplementedError

    @property
    def active_tab(self) -> PanelTabDefinition:
        """Return the currently active tab definition."""
        return self.tabs[self.active_tab_index]

    def compose(self) -> ComposeResult:
        self._ensure_valid_index()
        active_tab = self.active_tab
        with Container(classes="header"):
            yield Static("<", classes="nav-btn", id="panel-nav-prev")
            yield Static(active_tab.title, classes="title")
            yield Static(">", classes="nav-btn", id="panel-nav-next")
        yield active_tab.view_factory(self.view_context)

    def previous_tab(self) -> None:
        """Cycle to the previous valid panel tab."""
        self.active_tab_index = (self.active_tab_index - 1) % len(self.tabs)
        self.refresh(recompose=True)

    def next_tab(self) -> None:
        """Cycle to the next valid panel tab."""
        self.active_tab_index = (self.active_tab_index + 1) % len(self.tabs)
        self.refresh(recompose=True)

    def on_click(self, event: Click) -> None:
        """Handle clicks on the reusable header navigation buttons."""
        widget = event.widget
        if widget is None:
            return
        if widget.id == "panel-nav-prev":
            self.previous_tab()
        elif widget.id == "panel-nav-next":
            self.next_tab()

    def _ensure_valid_index(self) -> None:
        if self.active_tab_index >= len(self.tabs):
            self.active_tab_index = 0
