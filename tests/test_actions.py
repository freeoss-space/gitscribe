"""Tests for post-generation actions."""

from unittest.mock import MagicMock, patch

from gitscribe.actions import ActionChoice, ActionHandler
from gitscribe.models import GhConfig


class TestActionChoice:
    def test_values(self) -> None:
        assert ActionChoice.COMMIT.value == "commit"
        assert ActionChoice.CREATE_PR.value == "create_pr"
        assert ActionChoice.COPY.value == "copy"
        assert ActionChoice.REGENERATE.value == "regenerate"
        assert ActionChoice.REGENERATE_FEEDBACK.value == "regenerate_feedback"
        assert ActionChoice.EDIT.value == "edit"
        assert ActionChoice.QUIT.value == "quit"


class TestActionHandler:
    def test_do_commit(self) -> None:
        git_ops = MagicMock()
        handler = ActionHandler(git_ops=git_ops, gh_config=GhConfig())
        handler.do_commit("feat: add feature")
        git_ops.commit.assert_called_once_with("feat: add feature")

    def test_do_copy(self) -> None:
        with patch("pyperclip.copy") as mock_copy:
            handler = ActionHandler(git_ops=MagicMock(), gh_config=GhConfig())
            handler.do_copy("some text")
            mock_copy.assert_called_once_with("some text")

    def test_do_edit(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("subprocess.run", return_value=mock_result),
            patch("tempfile.NamedTemporaryFile") as mock_tmp,
        ):
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.txt"
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_tmp.return_value = mock_file
            with (
                patch("builtins.open", MagicMock()),
                patch("pathlib.Path.read_text", return_value="edited message"),
            ):
                handler = ActionHandler(git_ops=MagicMock(), gh_config=GhConfig())
                result = handler.do_edit("original message")
                assert result == "edited message"

    def test_do_create_pr_default_command(self) -> None:
        gh_config = GhConfig(command="gh pr create --title {title} --body {body}")
        handler = ActionHandler(git_ops=MagicMock(), gh_config=gh_config)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            handler.do_create_pr("Add feature\n\nThis adds a new feature.")
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert isinstance(cmd, str)
            assert "gh pr create" in cmd

    def test_do_create_pr_parses_title_and_body(self) -> None:
        gh_config = GhConfig(command="gh pr create --title {title} --body {body}")
        handler = ActionHandler(git_ops=MagicMock(), gh_config=gh_config)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            handler.do_create_pr("My Title\n\nBody line 1\nBody line 2")
            cmd = mock_run.call_args[0][0]
            assert "My Title" in cmd
            assert "Body line 1" in cmd
