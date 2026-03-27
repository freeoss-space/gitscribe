"""Tests for commit command."""

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

from gitscribe.actions import ActionChoice
from gitscribe.commit_command import CommitCommand
from gitscribe.models import BodyLength, CommitFormat, GhConfig, Style, ThemeConfig
from gitscribe.theme import create_console
from gitscribe.ui import UI


def _make_command(
    ai_response: str = "feat: add feature",
    has_staged: bool = True,
    staged_diff: str = "diff --git a/f.py\n+new",
) -> tuple[CommitCommand, MagicMock, MagicMock]:
    backend = MagicMock()
    backend.generate = AsyncMock(return_value=ai_response)

    git_ops = MagicMock()
    git_ops.has_staged_changes.return_value = has_staged
    git_ops.get_staged_diff.return_value = staged_diff

    console = create_console(ThemeConfig())
    console.file = StringIO()
    ui = UI(console)

    cmd = CommitCommand(
        ai_backend=backend,
        git_ops=git_ops,
        ui=ui,
        console=console,
        gh_config=GhConfig(),
    )
    return cmd, backend, git_ops


class TestCommitCommand:
    def test_no_staged_changes_shows_warning(self) -> None:
        cmd, backend, _ = _make_command(has_staged=False)
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        backend.generate.assert_not_called()

    def test_empty_diff_shows_warning(self) -> None:
        cmd, backend, _ = _make_command(staged_diff="")
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        backend.generate.assert_not_called()

    @patch.object(UI, "prompt_commit_action", return_value=ActionChoice.QUIT)
    def test_generates_and_shows_message(self, _mock: MagicMock) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        backend.generate.assert_called_once()

    @patch.object(UI, "prompt_commit_action", return_value=ActionChoice.COMMIT)
    def test_commit_action_calls_git(self, _mock: MagicMock) -> None:
        cmd, _, git_ops = _make_command()
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        git_ops.commit.assert_called_once_with("feat: add feature")

    @patch("pyperclip.copy")
    @patch.object(UI, "prompt_commit_action", return_value=ActionChoice.COPY)
    def test_copy_action(self, _mock_action: MagicMock, mock_copy: MagicMock) -> None:
        cmd, _, _ = _make_command()
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        mock_copy.assert_called_once_with("feat: add feature")

    @patch.object(
        UI,
        "prompt_commit_action",
        side_effect=[ActionChoice.REGENERATE, ActionChoice.QUIT],
    )
    def test_regenerate_calls_ai_again(self, _mock: MagicMock) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        assert backend.generate.call_count == 2

    @patch.object(UI, "prompt_feedback", return_value="shorter please")
    @patch.object(
        UI,
        "prompt_commit_action",
        side_effect=[ActionChoice.REGENERATE_FEEDBACK, ActionChoice.QUIT],
    )
    def test_regenerate_with_feedback(
        self, _mock_action: MagicMock, _mock_feedback: MagicMock
    ) -> None:
        cmd, backend, _ = _make_command()
        cmd.run(
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        assert backend.generate.call_count == 2
        second_call_prompt = backend.generate.call_args_list[1][0][0]
        assert "shorter please" in second_call_prompt
