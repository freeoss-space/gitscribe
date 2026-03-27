"""Tests for CLI entry point."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gitscribe.cli import app
from gitscribe.models import (
    AiConfig,
    ApiConfig,
    AppConfig,
    CommitDefaults,
    CommitFormat,
    GhConfig,
    PrDefaults,
    Style,
    ThemeConfig,
)

runner = CliRunner()

_TEST_CONFIG = AppConfig(
    ai=AiConfig(api=ApiConfig(url="http://test", token="tk", model="m")),
    theme=ThemeConfig(),
    commit=CommitDefaults(),
    pr=PrDefaults(),
    gh=GhConfig(),
)


class TestCli:
    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        # no_args_is_help uses exit code 0 in typer
        assert "commit" in result.output.lower() or "usage" in result.output.lower()

    def test_help_flag(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "commit" in result.output
        assert "pr" in result.output

    @patch("gitscribe.cli.CommitCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_commit_command_invoked(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["commit"])
        assert result.exit_code == 0
        mock_cmd_cls.return_value.run.assert_called_once()

    @patch("gitscribe.cli.PrCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_pr_command_invoked(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["pr"])
        assert result.exit_code == 0
        mock_cmd_cls.return_value.run.assert_called_once()

    @patch("gitscribe.cli.CommitCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_commit_with_style_override(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["commit", "--style", "fun"])
        assert result.exit_code == 0
        call_kwargs = mock_cmd_cls.return_value.run.call_args[1]
        assert call_kwargs["style"] == Style.FUN

    @patch("gitscribe.cli.CommitCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_commit_with_format_override(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["commit", "--format", "gitmoji"])
        assert result.exit_code == 0
        call_kwargs = mock_cmd_cls.return_value.run.call_args[1]
        assert call_kwargs["fmt"] == CommitFormat.GITMOJI

    @patch("gitscribe.cli.PrCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_pr_with_base_branch(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["pr", "--base", "develop"])
        assert result.exit_code == 0
        call_kwargs = mock_cmd_cls.return_value.run.call_args[1]
        assert call_kwargs["base_branch"] == "develop"

    @patch("gitscribe.cli.CommitCommand")
    @patch("gitscribe.cli.create_backend")
    @patch("gitscribe.cli.ConfigManager")
    def test_c_alias_works(
        self,
        mock_config_mgr_cls: MagicMock,
        mock_create_backend: MagicMock,
        mock_cmd_cls: MagicMock,
    ) -> None:
        mock_config_mgr = MagicMock()
        mock_config_mgr.load.return_value = _TEST_CONFIG
        mock_config_mgr_cls.return_value = mock_config_mgr

        result = runner.invoke(app, ["c"])
        assert result.exit_code == 0
        mock_cmd_cls.return_value.run.assert_called_once()
