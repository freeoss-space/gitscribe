"""Tests for config manager."""

import json
from pathlib import Path
from unittest.mock import patch

from gitscribe.config_manager import ConfigManager, _current_platform, _deep_merge
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


class TestCurrentPlatform:
    def test_macos(self) -> None:
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert _current_platform() == "macos"

    def test_linux(self) -> None:
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            assert _current_platform() == "linux"

    def test_windows(self) -> None:
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "win32"
            assert _current_platform() == "windows"

    def test_windows_64(self) -> None:
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "win64"
            assert _current_platform() == "windows"

    def test_unknown_defaults_to_linux(self) -> None:
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "freebsd"
            assert _current_platform() == "linux"


class TestDeepMerge:
    def test_simple_override(self) -> None:
        result = _deep_merge({"a": 1, "b": 2}, {"b": 99})
        assert result == {"a": 1, "b": 99}

    def test_nested_override(self) -> None:
        base = {"ai": {"backend": "api", "cli": {"command": "base-cmd", "model": "base-model"}}}
        override = {"ai": {"cli": {"command": "new-cmd"}}}
        result = _deep_merge(base, override)
        assert result["ai"]["cli"]["command"] == "new-cmd"
        assert result["ai"]["cli"]["model"] == "base-model"
        assert result["ai"]["backend"] == "api"

    def test_new_key_added(self) -> None:
        result = _deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_base_unchanged(self) -> None:
        base = {"a": {"x": 1}}
        _deep_merge(base, {"a": {"x": 2}})
        assert base["a"]["x"] == 1


class TestPlatformOverrides:
    def test_linux_overrides_commit_model(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commit": {"model": "base-model"},
            "platforms": {
                "linux": {"commit": {"model": "linux-model"}},
                "macos": {"commit": {"model": "mac-model"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.commit.model == "linux-model"

    def test_macos_overrides_commit_model(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commit": {"model": "base-model"},
            "platforms": {
                "linux": {"commit": {"model": "linux-model"}},
                "macos": {"commit": {"model": "mac-model"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "darwin"
            config = manager.load()
        assert config.commit.model == "mac-model"

    def test_platform_overrides_commit_command(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "platforms": {
                "linux": {"commit": {"command": "ollama run {model}"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.commit.command == "ollama run {model}"

    def test_platform_overrides_pr_model(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "platforms": {
                "macos": {"pr": {"model": "claude-opus-4-7"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "darwin"
            config = manager.load()
        assert config.pr.model == "claude-opus-4-7"

    def test_platform_overrides_pr_command(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "platforms": {
                "linux": {"pr": {"command": "llm -m {model}"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.pr.command == "llm -m {model}"

    def test_platform_overrides_ai_cli_command(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "ai": {"backend": "cli", "cli": {"command": "default-ai", "model": "default"}},
            "platforms": {
                "macos": {"ai": {"cli": {"command": "mac-ai", "model": "mac-model"}}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "darwin"
            config = manager.load()
        assert config.ai.cli.command == "mac-ai"
        assert config.ai.cli.model == "mac-model"
        assert config.ai.backend == "cli"

    def test_platform_overrides_ai_backend(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "ai": {"backend": "api"},
            "platforms": {
                "linux": {"ai": {"backend": "cli", "cli": {"command": "ollama run {model}"}}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.ai.backend == "cli"
        assert config.ai.cli.command == "ollama run {model}"

    def test_partial_platform_override_preserves_base(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commit": {"model": "base-model", "command": "base-cmd"},
            "platforms": {
                "linux": {"commit": {"model": "linux-model"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.commit.model == "linux-model"
        assert config.commit.command == "base-cmd"

    def test_no_matching_platform_uses_base(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commit": {"model": "base-model"},
            "platforms": {
                "macos": {"commit": {"model": "mac-model"}},
            },
        }))
        manager = ConfigManager(config_dir=tmp_path)
        with patch("gitscribe.config_manager.sys") as mock_sys:
            mock_sys.platform = "linux"
            config = manager.load()
        assert config.commit.model == "base-model"

    def test_empty_platforms_section_ignored(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "commit": {"model": "base-model"},
            "platforms": {},
        }))
        manager = ConfigManager(config_dir=tmp_path)
        config = manager.load()
        assert config.commit.model == "base-model"
