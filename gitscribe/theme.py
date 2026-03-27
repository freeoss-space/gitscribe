"""Rich theme management for gitscribe."""

from rich.console import Console
from rich.theme import Theme

from gitscribe.models import ThemeConfig


def create_theme(config: ThemeConfig) -> Theme:
    """Create a Rich theme from config."""
    return Theme(
        {
            "primary": config.primary,
            "secondary": config.secondary,
            "accent": config.accent,
            "error": config.error,
            "warning": config.warning,
            "title": f"bold {config.primary}",
            "subtitle": f"bold {config.secondary}",
            "highlight": f"bold {config.accent}",
            "muted": "dim",
        }
    )


def create_console(config: ThemeConfig) -> Console:
    """Create a themed Rich console."""
    return Console(theme=create_theme(config))
