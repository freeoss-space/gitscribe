"""Tests for config manager."""

import json
from pathlib import Path
from unittest.mock import patch

from gitscribe.config_manager import ConfigManager
from gitscribe.models import (
    AiConfig,
    ApiConfig,
    AppConfig,
    BodyLength,
    CommitFormat,
    Style,
    ThemeConfig,
)


class TestConfigManager:
    def test_default_config_path(self) -> None:
        with patch("gitscribe.config_manager.user_config_dir", return_value="/tmp/test_xdg"):
            manager = ConfigManager()
            assert manager.config_path == Path("/tmp/test_xdg/config.json")

    def test_load_default_when_no_file(self, tmp_path: Path) -> None:
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config == AppConfig()

    def test_save_and_load(self, tmp_path: Path) -> None:
        manager = ConfigManager(config_dir=tmp_path)
        config = AppConfig(
            ai=AiConfig(
                backend="api",
                api=ApiConfig(url="http://localhost:8080", token="sk-test", model="gpt-4"),
            ),
            theme=ThemeConfig(primary="blue"),
        )
        manager.save(config)
        loaded = manager.load()
        assert loaded == config

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "nested" / "dir"
        manager = ConfigManager(config_dir=config_dir)
        manager.save(AppConfig())
        assert manager.config_path.exists()

    def test_load_partial_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        partial = {"ai": {"backend": "cli", "cli": {"command": "llm {model}", "model": "gpt-4"}}}
        config_file.write_text(json.dumps(partial))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.ai.backend == "cli"
        assert config.ai.cli.command == "llm {model}"
        assert config.ai.cli.model == "gpt-4"
        # Defaults preserved for unset fields
        assert config.theme == ThemeConfig()

    def test_load_with_enum_values(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        data = {
            "commit": {
                "style": "fun",
                "format": "gitmoji",
                "body_length": "long",
            }
        }
        config_file.write_text(json.dumps(data))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.commit.style == Style.FUN
        assert config.commit.format == CommitFormat.GITMOJI
        assert config.commit.body_length == BodyLength.LONG

    def test_load_handles_corrupt_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text("not json{{{")
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config == AppConfig()

    def test_load_commit_model_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"commit": {"model": "gpt-4-turbo"}}))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.commit.model == "gpt-4-turbo"

    def test_load_commit_command_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"commit": {"command": "claude --fast"}}))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.commit.command == "claude --fast"

    def test_load_pr_model_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"pr": {"model": "claude-opus-4-5"}}))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.pr.model == "claude-opus-4-5"

    def test_load_pr_command_override(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"pr": {"command": "claude --verbose"}}))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.pr.command == "claude --verbose"

    def test_save_and_load_with_per_command_overrides(self, tmp_path: Path) -> None:
        from gitscribe.models import CommitDefaults, PrDefaults
        manager = ConfigManager(config_dir=tmp_path)
        config = AppConfig(
            commit=CommitDefaults(model="gpt-4-turbo", command="llm -m {model}"),
            pr=PrDefaults(model="claude-opus-4-5", command="claude"),
        )
        manager.save(config)
        loaded = manager.load()
        assert loaded.commit.model == "gpt-4-turbo"
        assert loaded.commit.command == "llm -m {model}"
        assert loaded.pr.model == "claude-opus-4-5"
        assert loaded.pr.command == "claude"

    def test_per_command_overrides_default_to_empty(self, tmp_path: Path) -> None:
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.commit.model == ""
        assert config.commit.command == ""
        assert config.pr.model == ""
        assert config.pr.command == ""
