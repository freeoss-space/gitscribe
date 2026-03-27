"""Tests for git operations."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from gitscribe.git_operations import GitOperations


class TestGitOperations:
    def test_get_diff_staged(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "diff --git a/file.py\n+new line"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            ops = GitOperations()
            diff = ops.get_staged_diff()
            assert diff == "diff --git a/file.py\n+new line"
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert "diff" in args[0][0]
            assert "--cached" in args[0][0]

    def test_get_branch_diff(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "diff content"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            ops = GitOperations()
            diff = ops.get_branch_diff("main")
            assert diff == "diff content"
            cmd = mock_run.call_args[0][0]
            assert "main...HEAD" in cmd

    def test_get_current_branch(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "feature/my-branch\n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            ops = GitOperations()
            branch = ops.get_current_branch()
            assert branch == "feature/my-branch"

    def test_get_default_branch(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "main\n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            ops = GitOperations()
            branch = ops.get_default_branch()
            assert branch == "main"

    def test_get_default_branch_fallback(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            ops = GitOperations()
            branch = ops.get_default_branch()
            assert branch == "main"

    def test_commit(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            ops = GitOperations()
            ops.commit("feat: add feature")
            cmd = mock_run.call_args[0][0]
            assert "commit" in cmd
            assert "-m" in cmd

    def test_has_staged_changes_true(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1  # diff --cached returns 1 when there are changes
        with patch("subprocess.run", return_value=mock_result):
            ops = GitOperations()
            assert ops.has_staged_changes() is True

    def test_has_staged_changes_false(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            ops = GitOperations()
            assert ops.has_staged_changes() is False

    def test_find_pr_template_found(self, tmp_path: Path) -> None:
        template_dir = tmp_path / ".github"
        template_dir.mkdir()
        template_file = template_dir / "pull_request_template.md"
        template_file.write_text("## Description\n\n## Changes")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = str(tmp_path) + "\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            ops = GitOperations()
            template = ops.find_pr_template()
            assert template == "## Description\n\n## Changes"

    def test_find_pr_template_not_found(self, tmp_path: Path) -> None:
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = str(tmp_path) + "\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            ops = GitOperations()
            template = ops.find_pr_template()
            assert template is None
