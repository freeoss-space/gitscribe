"""Rich TUI components for gitscribe."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from gitscribe.actions import ActionChoice

COMMIT_ACTION_LABELS: dict[ActionChoice, str] = {
    ActionChoice.COMMIT: "[accent]c[/accent]ommit",
    ActionChoice.COPY: "co[accent]p[/accent]y to clipboard",
    ActionChoice.REGENERATE: "[accent]r[/accent]egenerate",
    ActionChoice.REGENERATE_FEEDBACK: "regenerate with [accent]f[/accent]eedback",
    ActionChoice.EDIT: "[accent]e[/accent]dit in $EDITOR",
    ActionChoice.QUIT: "[accent]q[/accent]uit",
}

PR_ACTION_LABELS: dict[ActionChoice, str] = {
    ActionChoice.CREATE_PR: "[accent]c[/accent]reate PR",
    ActionChoice.COPY: "co[accent]p[/accent]y to clipboard",
    ActionChoice.REGENERATE: "[accent]r[/accent]egenerate",
    ActionChoice.REGENERATE_FEEDBACK: "regenerate with [accent]f[/accent]eedback",
    ActionChoice.EDIT: "[accent]e[/accent]dit in $EDITOR",
    ActionChoice.QUIT: "[accent]q[/accent]uit",
}

COMMIT_KEY_MAP: dict[str, ActionChoice] = {
    "c": ActionChoice.COMMIT,
    "p": ActionChoice.COPY,
    "r": ActionChoice.REGENERATE,
    "f": ActionChoice.REGENERATE_FEEDBACK,
    "e": ActionChoice.EDIT,
    "q": ActionChoice.QUIT,
}

PR_KEY_MAP: dict[str, ActionChoice] = {
    "c": ActionChoice.CREATE_PR,
    "p": ActionChoice.COPY,
    "r": ActionChoice.REGENERATE,
    "f": ActionChoice.REGENERATE_FEEDBACK,
    "e": ActionChoice.EDIT,
    "q": ActionChoice.QUIT,
}


class UI:
    """Rich TUI for gitscribe."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_banner(self) -> None:
        self._console.print(
            Panel(
                "[title]GitScribe[/title] [muted]— AI-powered git messages[/muted]",
                border_style="primary",
            )
        )

    def show_generating(self) -> None:
        self._console.print("\n[secondary]Generating with AI...[/secondary]")

    def show_message(self, message: str, title: str = "Generated Message") -> None:
        self._console.print()
        self._console.print(
            Panel(
                Markdown(message),
                title=f"[title]{title}[/title]",
                border_style="accent",
                padding=(1, 2),
            )
        )

    def show_error(self, message: str) -> None:
        self._console.print(f"\n[error]Error:[/error] {message}")

    def show_success(self, message: str) -> None:
        self._console.print(f"\n[accent]Success:[/accent] {message}")

    def show_warning(self, message: str) -> None:
        self._console.print(f"\n[warning]Warning:[/warning] {message}")

    def prompt_commit_action(self) -> ActionChoice:
        return self._prompt_action(COMMIT_ACTION_LABELS, COMMIT_KEY_MAP)

    def prompt_pr_action(self) -> ActionChoice:
        return self._prompt_action(PR_ACTION_LABELS, PR_KEY_MAP)

    def prompt_feedback(self) -> str:
        return Prompt.ask("\n[secondary]Enter feedback[/secondary]")

    def _prompt_action(
        self,
        labels: dict[ActionChoice, str],
        key_map: dict[str, ActionChoice],
    ) -> ActionChoice:
        options = " | ".join(labels.values())
        self._console.print(f"\n{options}")
        while True:
            choice = Prompt.ask("[primary]Choose[/primary]").strip().lower()
            if choice in key_map:
                return key_map[choice]
            self._console.print("[warning]Invalid choice, try again[/warning]")

    def show_diff_stats(self, diff: str) -> None:
        lines = diff.split("\n")
        additions = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
        self._console.print(
            f"[accent]+{additions}[/accent] [error]-{deletions}[/error] "
            f"[muted]({len(lines)} lines)[/muted]"
        )
