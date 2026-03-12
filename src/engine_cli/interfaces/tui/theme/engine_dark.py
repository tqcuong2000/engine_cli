from textual.theme import Theme

ENGINE_THEME = Theme(
    name="engine_dark",
    primary="#004578",
    secondary="#0078d4",
    accent="#ffb900",
    foreground="#ffffff",
    background="#1a1a1a",
    success="#107c10",
    warning="#ffb900",
    error="#d83b01",
    surface="#2b2b2b",
    panel="#333333",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#0078d4",
    },
)
