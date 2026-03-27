"""PR command orchestrator."""

import asyncio

from rich.console import Console

from gitscribe.actions import ActionChoice, ActionHandler
from gitscribe.ai_backend import AiBackend
from gitscribe.git_operations import GitOperations
from gitscribe.models import GhConfig, Style
from gitscribe.prompt_builder import PromptBuilder
from gitscribe.ui import UI


class PrCommand:
    """Orchestrates the PR message generation flow."""

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

    def run(self, style: Style, base_branch: str | None = None) -> None:
        self._ui.show_banner()

        if base_branch is None:
            base_branch = self._git.get_default_branch()

        diff = self._git.get_branch_diff(base_branch)
        if not diff.strip():
            self._ui.show_warning(
                f"No diff found between {base_branch} and HEAD. "
                "Make sure you have commits on your branch."
            )
            return

        self._ui.show_diff_stats(diff)

        template = self._git.find_pr_template()
        prompt = PromptBuilder.pr(diff=diff, style=style, template=template)
        message = self._generate(prompt)

        self._interaction_loop(message, diff, style, template)

    def _generate(self, prompt: str) -> str:
        self._ui.show_generating()
        with self._console.status("[secondary]Thinking...[/secondary]"):
            return asyncio.run(self._ai.generate(prompt))

    def _interaction_loop(
        self,
        message: str,
        diff: str,
        style: Style,
        template: str | None,
    ) -> None:
        while True:
            self._ui.show_message(message, title="Pull Request Message")
            action = self._ui.prompt_pr_action()

            if action == ActionChoice.CREATE_PR:
                self._actions.do_create_pr(message)
                self._ui.show_success("PR created!")
                return

            if action == ActionChoice.COPY:
                self._actions.do_copy(message)
                self._ui.show_success("Copied to clipboard!")
                return

            if action == ActionChoice.REGENERATE:
                prompt = PromptBuilder.pr(diff=diff, style=style, template=template)
                message = self._generate(prompt)

            elif action == ActionChoice.REGENERATE_FEEDBACK:
                feedback = self._ui.prompt_feedback()
                prompt = PromptBuilder.pr(
                    diff=diff, style=style, template=template, feedback=feedback
                )
                message = self._generate(prompt)

            elif action == ActionChoice.EDIT:
                message = self._actions.do_edit(message)

            elif action == ActionChoice.QUIT:
                return
