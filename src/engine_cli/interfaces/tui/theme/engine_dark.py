from textual.theme import Theme

ENGINE_THEME = Theme(
    name="engine_dark",
    primary="#1a3a5c",       # Deep navy blue
    secondary="#00aacc",     # Vivid cyan-blue
    accent="#00e5ff",        # Electric cyan
    foreground="#e0e6f0",    # Soft white with a cool tint
    background="#0d0f14",    # Very dark blue-black
    success="#1db954",       # Vibrant green
    warning="#f5a623",       # Warm amber
    error="#ff453a",         # Sharp red
    surface="#141720",       # Dark blue-gray surface
    panel="#1c2030",         # Slightly lighter panel
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#00aacc",
        "border-color": "#2a3550",
        "input-cursor-background": "#00aacc",
    },
)
