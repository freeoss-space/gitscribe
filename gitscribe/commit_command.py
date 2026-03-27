"""Commit command orchestrator."""

import asyncio

from rich.console import Console

from gitscribe.actions import ActionChoice, ActionHandler
from gitscribe.ai_backend import AiBackend
from gitscribe.git_operations import GitOperations
from gitscribe.models import BodyLength, CommitFormat, GhConfig, Style
from gitscribe.prompt_builder import PromptBuilder
from gitscribe.ui import UI


class CommitCommand:
    """Orchestrates the commit message generation flow."""

    def __init__(
        self,
        ai_backend: AiBackend,
        git_ops: GitOperations,
        ui: UI,
        console: Console,
        gh_config: GhConfig,
    ) -> None:
        self._ai = ai_backend
        self._git = git_ops
        self._ui = ui
        self._console = console
        self._actions = ActionHandler(git_ops=git_ops, gh_config=gh_config)

    def run(
        self,
        style: Style,
        fmt: CommitFormat,
        body_length: BodyLength,
    ) -> None:
        self._ui.show_banner()

        if not self._git.has_staged_changes():
            self._ui.show_warning("No staged changes found. Stage files with `git add` first.")
            return

        diff = self._git.get_staged_diff()
        if not diff.strip():
            self._ui.show_warning("Empty diff. Nothing to generate.")
            return

        self._ui.show_diff_stats(diff)

        prompt = PromptBuilder.commit(diff=diff, style=style, fmt=fmt, body_length=body_length)
        message = self._generate(prompt)

        self._interaction_loop(message, diff, style, fmt, body_length)

    def _generate(self, prompt: str) -> str:
        self._ui.show_generating()
        with self._console.status("[secondary]Thinking...[/secondary]"):
            return asyncio.run(self._ai.generate(prompt))

    def _interaction_loop(
        self,
        message: str,
        diff: str,
        style: Style,
        fmt: CommitFormat,
        body_length: BodyLength,
    ) -> None:
        while True:
            self._ui.show_message(message, title="Commit Message")
            action = self._ui.prompt_commit_action()

            if action == ActionChoice.COMMIT:
                self._actions.do_commit(message)
                self._ui.show_success("Committed!")
                return

            if action == ActionChoice.COPY:
                self._actions.do_copy(message)
                self._ui.show_success("Copied to clipboard!")
                return

            if action == ActionChoice.REGENERATE:
                prompt = PromptBuilder.commit(
                    diff=diff, style=style, fmt=fmt, body_length=body_length
                )
                message = self._generate(prompt)

            elif action == ActionChoice.REGENERATE_FEEDBACK:
                feedback = self._ui.prompt_feedback()
                prompt = PromptBuilder.commit(
                    diff=diff,
                    style=style,
                    fmt=fmt,
                    body_length=body_length,
                    feedback=feedback,
                )
                message = self._generate(prompt)

            elif action == ActionChoice.EDIT:
                message = self._actions.do_edit(message)

            elif action == ActionChoice.QUIT:
                return
