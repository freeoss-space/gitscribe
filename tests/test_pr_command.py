"""Tests for PR command."""

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

from gitscribe.actions import ActionChoice
from gitscribe.models import GhConfig, Style, ThemeConfig
from gitscribe.pr_command import PrCommand
from gitscribe.theme import create_console
from gitscribe.ui import UI


def _make_command(
    ai_response: str = "## PR Title\n\nSome description",
    branch_diff: str = "diff --git a/f.py\n+new",
    pr_template: str | None = None,
    default_branch: str = "main",
) -> tuple[PrCommand, MagicMock, MagicMock]:
    backend = MagicMock()
    backend.generate = AsyncMock(return_value=ai_response)

    git_ops = MagicMock()
    git_ops.get_branch_diff.return_value = branch_diff
    git_ops.get_default_branch.return_value = default_branch
    git_ops.find_pr_template.return_value = pr_template

    console = create_console(ThemeConfig())
    console.file = StringIO()
    ui = UI(console)

    cmd = PrCommand(
        ai_backend=backend,
        git_ops=git_ops,
        ui=ui,
        console=console,
        gh_config=GhConfig(),
    )
    return cmd, backend, git_ops


class TestPrCommand:
    def test_empty_diff_shows_warning(self) -> None:
        cmd, backend, _ = _make_command(branch_diff="")
        cmd.run(style=Style.PROFESSIONAL)
        backend.generate.assert_not_called()

    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.QUIT)
    def test_generates_message(self, _mock: MagicMock) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(style=Style.PROFESSIONAL)
        backend.generate.assert_called_once()

    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.QUIT)
    def test_uses_default_branch(self, _mock: MagicMock) -> None:
        cmd, _, git_ops = _make_command(default_branch="develop")
        cmd.run(style=Style.PROFESSIONAL)
        git_ops.get_default_branch.assert_called_once()
        git_ops.get_branch_diff.assert_called_once_with("develop")

    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.QUIT)
    def test_uses_explicit_base_branch(self, _mock: MagicMock) -> None:
        cmd, _, git_ops = _make_command()
        cmd.run(style=Style.PROFESSIONAL, base_branch="release")
        git_ops.get_default_branch.assert_not_called()
        git_ops.get_branch_diff.assert_called_once_with("release")

    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.QUIT)
    def test_includes_pr_template_in_prompt(self, _mock: MagicMock) -> None:
        template = "## Description\n## Changes"
        cmd, backend, _ = _make_command(pr_template=template)
        cmd.run(style=Style.PROFESSIONAL)
        prompt_sent = backend.generate.call_args[0][0]
        assert "## Description" in prompt_sent

    @patch("subprocess.run")
    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.CREATE_PR)
    def test_create_pr_action(self, _mock_action: MagicMock, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        cmd, _, _ = _make_command()
        cmd.run(style=Style.PROFESSIONAL)
        mock_run.assert_called_once()

    @patch("pyperclip.copy")
    @patch.object(UI, "prompt_pr_action", return_value=ActionChoice.COPY)
    def test_copy_action(self, _mock_action: MagicMock, mock_copy: MagicMock) -> None:
        cmd, _, _ = _make_command()
        cmd.run(style=Style.PROFESSIONAL)
        mock_copy.assert_called_once()

    @patch.object(UI, "prompt_pr_action", side_effect=[ActionChoice.REGENERATE, ActionChoice.QUIT])
    def test_regenerate(self, _mock: MagicMock) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(style=Style.PROFESSIONAL)
        assert backend.generate.call_count == 2

    @patch.object(UI, "prompt_feedback", return_value="add changelog")
    @patch.object(
        UI,
        "prompt_pr_action",
        side_effect=[ActionChoice.REGENERATE_FEEDBACK, ActionChoice.QUIT],
    )
    def test_regenerate_with_feedback(
        self, _mock_action: MagicMock, _mock_feedback: MagicMock
    ) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(style=Style.PROFESSIONAL)
        assert backend.generate.call_count == 2
        second_prompt = backend.generate.call_args_list[1][0][0]
        assert "add changelog" in second_prompt
