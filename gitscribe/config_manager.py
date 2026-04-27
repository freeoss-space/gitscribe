"""Configuration manager for gitscribe."""

import json
import sys
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from gitscribe.models import (
    AiConfig,
    ApiConfig,
    AppConfig,
    BodyLength,
    CliConfig,
    CommitDefaults,
    CommitFormat,
    GhConfig,
    PrDefaults,
    Style,
    ThemeConfig,
)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _current_platform() -> str:
    """Return the normalized platform name: 'macos', 'linux', or 'windows'."""
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


class ConfigManager:
    """Manages loading and saving of gitscribe configuration."""

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is not None:
            self._config_dir = config_dir
        else:
            self._config_dir = Path(user_config_dir("gitscribe"))

    @property
    def config_path(self) -> Path:
        return self._config_dir / "config.json"

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            return AppConfig()
        try:
            data = json.loads(self.config_path.read_text())
        except (json.JSONDecodeError, OSError):
            return AppConfig()
        return self._parse_config(data)

    def save(self, config: AppConfig) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = self._serialize_config(config)
        self.config_path.write_text(json.dumps(data, indent=2))

    def _parse_config(self, data: dict[str, Any]) -> AppConfig:
        platforms = data.get("platforms", {})
        platform_overrides = platforms.get(_current_platform(), {})
        if platform_overrides:
            data = _deep_merge(data, platform_overrides)

        ai_data = data.get("ai", {})
        api_data = ai_data.get("api", {})
        cli_data = ai_data.get("cli", {})
        theme_data = data.get("theme", {})
        commit_data = data.get("commit", {})
        pr_data = data.get("pr", {})
        gh_data = data.get("gh", {})

        return AppConfig(
            ai=AiConfig(
                backend=ai_data.get("backend", "api"),
                api=ApiConfig(
                    url=api_data.get("url", ""),
                    token=api_data.get("token", ""),
                    model=api_data.get("model", ""),
                ),
                cli=CliConfig(
                    command=cli_data.get("command", ""),
                    model=cli_data.get("model", ""),
                ),
            ),
            theme=ThemeConfig(
                primary=theme_data.get("primary", "cyan"),
                secondary=theme_data.get("secondary", "magenta"),
                accent=theme_data.get("accent", "green"),
                error=theme_data.get("error", "red"),
                warning=theme_data.get("warning", "yellow"),
            ),
            commit=CommitDefaults(
                style=Style(commit_data.get("style", "professional")),
                format=CommitFormat(commit_data.get("format", "conventional")),
                body_length=BodyLength(commit_data.get("body_length", "short")),
                model=commit_data.get("model", ""),
                command=commit_data.get("command", ""),
            ),
            pr=PrDefaults(
                style=Style(pr_data.get("style", "professional")),
                model=pr_data.get("model", ""),
                command=pr_data.get("command", ""),
            ),
            gh=GhConfig(
                command=gh_data.get("command", "gh pr create --title {title} --body {body}"),
            ),
        )

    def _serialize_config(self, config: AppConfig) -> dict[str, Any]:
        return {
            "ai": {
                "backend": config.ai.backend,
                "api": {
                    "url": config.ai.api.url,
                    "token": config.ai.api.token,
                    "model": config.ai.api.model,
                },
                "cli": {
                    "command": config.ai.cli.command,
                    "model": config.ai.cli.model,
                },
            },
            "theme": {
                "primary": config.theme.primary,
                "secondary": config.theme.secondary,
                "accent": config.theme.accent,
                "error": config.theme.error,
                "warning": config.theme.warning,
            },
            "commit": {
                "style": config.commit.style.value,
                "format": config.commit.format.value,
                "body_length": config.commit.body_length.value,
                "model": config.commit.model,
                "command": config.commit.command,
            },
            "pr": {
                "style": config.pr.style.value,
                "model": config.pr.model,
                "command": config.pr.command,
            },
            "gh": {
                "command": config.gh.command,
            },
        }
