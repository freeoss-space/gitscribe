"""Post-generation action handling for gitscribe."""

import os
import shlex
import subprocess
import tempfile
from enum import Enum
from pathlib import Path

import pyperclip

from gitscribe.git_operations import GitOperations
from gitscribe.models import GhConfig


class ActionChoice(Enum):
    COMMIT = "commit"
    CREATE_PR = "create_pr"
    COPY = "copy"
    REGENERATE = "regenerate"
    REGENERATE_FEEDBACK = "regenerate_feedback"
    EDIT = "edit"
    QUIT = "quit"


class ActionHandler:
    """Handles post-generation actions."""

    def __init__(self, git_ops: GitOperations, gh_config: GhConfig) -> None:
        self._git_ops = git_ops
        self._gh_config = gh_config

    def do_commit(self, message: str) -> None:
        self._git_ops.commit(message)

    def do_copy(self, text: str) -> None:
        pyperclip.copy(text)

    def do_edit(self, message: str) -> str:
        editor = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(message)
            tmp_path = tmp.name

        try:
            subprocess.run([editor, tmp_path], check=True)
            return Path(tmp_path).read_text()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def do_create_pr(self, message: str) -> None:
        lines = message.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        cmd = self._gh_config.command.replace("{title}", shlex.quote(title)).replace(
            "{body}", shlex.quote(body)
        )

        subprocess.run(cmd, shell=True, check=True)
