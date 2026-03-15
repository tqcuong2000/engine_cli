class ConfigError(Exception):
    """Base error for configuration loading and resolution failures."""


class JsonConfigError(ConfigError):
    """Raised when a JSON config file cannot be decoded into a valid object."""


class ConfigResolutionError(ConfigError):
    """Raised when resolved config values do not match the expected shape."""
