from engine_cli.interfaces.tui.components import PanelTabDefinition
from engine_cli.interfaces.tui.panel.actions_panel import ActionsPanelView
from engine_cli.interfaces.tui.panel.context import PanelViewContext
from engine_cli.interfaces.tui.panel.context_panel import ContextPanelView
from engine_cli.interfaces.tui.panel.servers_panel import ServersPanelView
from engine_cli.interfaces.tui.panel.tasks_panel import TasksPanelView


BASE_PANEL_TABS = (
    PanelTabDefinition("context", "Context", ContextPanelView),
    PanelTabDefinition("servers", "Servers", ServersPanelView),
    PanelTabDefinition("actions", "Actions", ActionsPanelView),
    PanelTabDefinition("tasks", "Tasks", TasksPanelView),
)


def get_panel_tabs(_mode: object) -> tuple[PanelTabDefinition, ...]:
    """Return the current panel tabs.

    The shell keeps the same utility tabs across modes for now.
    """
    return BASE_PANEL_TABS
