from dataclasses import dataclass
from typing import Callable

from textual.widget import Widget

from engine_cli.application import SessionContext
from engine_cli.interfaces.tui.panel.actions_panel import ActionsPanelView
from engine_cli.interfaces.tui.panel.context_panel import ContextPanelView
from engine_cli.interfaces.tui.panel.tasks_panel import TasksPanelView


@dataclass(frozen=True)
class PanelTab:
    """Definition of one available panel tab."""

    key: str
    title: str
    view_factory: Callable[[SessionContext], Widget]


BASE_PANEL_TABS = (
    PanelTab("context", "Context", ContextPanelView),
    PanelTab("actions", "Actions", ActionsPanelView),
    PanelTab("tasks", "Tasks", TasksPanelView),
)


def get_panel_tabs(_mode: object) -> tuple[PanelTab, ...]:
    """Return the current panel tabs.

    The shell keeps the same three panel tabs across modes for now.
    """
    return BASE_PANEL_TABS
