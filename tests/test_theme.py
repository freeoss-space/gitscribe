"""Tests for theme module."""

from rich.console import Console
from rich.theme import Theme

from gitscribe.models import ThemeConfig
from gitscribe.theme import create_console, create_theme


class TestCreateTheme:
    def test_returns_theme(self) -> None:
        config = ThemeConfig()
        theme = create_theme(config)
        assert isinstance(theme, Theme)

    def test_theme_has_styles(self) -> None:
        config = ThemeConfig(primary="blue", accent="yellow")
        theme = create_theme(config)
        assert "primary" in theme.styles
        assert "accent" in theme.styles
        assert "title" in theme.styles
        assert "highlight" in theme.styles


class TestCreateConsole:
    def test_returns_console(self) -> None:
        config = ThemeConfig()
        console = create_console(config)
        assert isinstance(console, Console)
