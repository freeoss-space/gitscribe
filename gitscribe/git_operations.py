"""Git operations for gitscribe."""

import subprocess
from pathlib import Path


class GitOperations:
    """Handles all git-related operations."""

    def get_staged_diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def get_branch_diff(self, base_branch: str) -> str:
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def get_default_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().removeprefix("origin/")
        except subprocess.CalledProcessError:
            return "main"

    def commit(self, message: str) -> None:
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
        )

    def has_staged_changes(self) -> bool:
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        return result.returncode != 0

    def find_pr_template(self) -> str | None:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_root = Path(result.stdout.strip())

        template_paths = [
            repo_root / ".github" / "pull_request_template.md",
            repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md",
            repo_root / "pull_request_template.md",
            repo_root / "PULL_REQUEST_TEMPLATE.md",
            repo_root / "docs" / "pull_request_template.md",
        ]

        for path in template_paths:
            if path.exists():
                return path.read_text()
        return None

    def get_repo_root(self) -> Path:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
