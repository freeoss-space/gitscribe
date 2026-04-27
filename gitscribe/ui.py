"""Rich TUI components for gitscribe."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from gitscribe.actions import ActionChoice

if TYPE_CHECKING:
    from collections.abc import Generator

    from rich.console import Console

# ── single-keypress input ─────────────────────────────────────────────────────

def _read_single_key() -> str:
    """Read exactly one keypress without requiring Enter.

    Uses platform-native APIs: termios/tty on POSIX, msvcrt on Windows.
    Raises io.UnsupportedOperation when stdin is not an interactive terminal.
    """
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415

        ch = msvcrt.getwch()
        return ch if isinstance(ch, str) else ch.decode("utf-8", errors="replace")

    import termios  # noqa: PLC0415
    import tty  # noqa: PLC0415

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


# ── action labels & key maps ──────────────────────────────────────────────────

COMMIT_ACTION_LABELS: dict[ActionChoice, str] = {
    ActionChoice.COMMIT: "[accent]c[/accent]ommit",
    ActionChoice.COPY: "co[accent]p[/accent]y",
    ActionChoice.REGENERATE: "[accent]r[/accent]egenerate",
    ActionChoice.REGENERATE_FEEDBACK: "re[accent]f[/accent]eedback",
    ActionChoice.EDIT: "[accent]e[/accent]dit",
    ActionChoice.QUIT: "[accent]q[/accent]uit",
}

PR_ACTION_LABELS: dict[ActionChoice, str] = {
    ActionChoice.CREATE_PR: "[accent]c[/accent]reate PR",
    ActionChoice.COPY: "co[accent]p[/accent]y",
    ActionChoice.REGENERATE: "[accent]r[/accent]egenerate",
    ActionChoice.REGENERATE_FEEDBACK: "re[accent]f[/accent]eedback",
    ActionChoice.EDIT: "[accent]e[/accent]dit",
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

_BAR_CHAR = "█"
_MAX_BAR_WIDTH = 40

# Responsive subtitle thresholds
_FULL_SUBTITLE_MIN_WIDTH = 50


# ── UI class ──────────────────────────────────────────────────────────────────


class UI:
    """Rich TUI for gitscribe — responsive, full-screen-ready, single-keypress."""

    def __init__(self, console: Console) -> None:
        self._console = console

    # ── banner & status ───────────────────────────────────────────────────────

    def show_banner(self) -> None:
        width = self._console.size.width
        subtitle = (
            "AI-powered git messages" if width >= _FULL_SUBTITLE_MIN_WIDTH else "AI git messages"
        )
        title = Text()
        title.append("GitScribe", style="bold title")
        title.append(f"  {subtitle}", style="muted")
        self._console.print(Panel(title, border_style="primary", padding=(0, 1)))

    @contextmanager
    def show_thinking(self) -> Generator[None, None, None]:
        """Context manager that shows a spinner while AI is generating."""
        with self._console.status("[secondary]Thinking…[/secondary]", spinner="dots"):
            yield

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

    # ── feedback messages ─────────────────────────────────────────────────────

    def show_error(self, message: str) -> None:
        self._console.print(
            Panel(f"[error]✗[/error]  {message}", border_style="error", padding=(0, 1))
        )

    def show_success(self, message: str) -> None:
        self._console.print(
            Panel(f"[accent]✓[/accent]  {message}", border_style="accent", padding=(0, 1))
        )

    def show_warning(self, message: str) -> None:
        self._console.print(
            Panel(f"[warning]⚠[/warning]  {message}", border_style="warning", padding=(0, 1))
        )

    # ── diff stats ────────────────────────────────────────────────────────────

    def show_diff_stats(self, diff: str) -> None:
        lines = diff.split("\n")
        additions = sum(
            1 for line in lines if line.startswith("+") and not line.startswith("+++")
        )
        deletions = sum(
            1 for line in lines if line.startswith("-") and not line.startswith("---")
        )
        total = additions + deletions
        bar = self._build_diff_bar(additions, deletions, total)
        prefix = f"{bar}  " if bar else ""
        self._console.print(
            f"{prefix}[accent]+{additions}[/accent] [error]-{deletions}[/error] "
            f"[muted]({total} lines changed)[/muted]"
        )

    def _build_diff_bar(self, additions: int, deletions: int, total: int) -> str:
        if total == 0:
            return ""
        max_w = min(_MAX_BAR_WIDTH, self._console.size.width // 4)
        add_w = round(additions / total * max_w)
        del_w = round(deletions / total * max_w)
        return (
            f"[accent]{_BAR_CHAR * add_w}[/accent]"
            f"[error]{_BAR_CHAR * del_w}[/error]"
        )

    # ── action prompts ────────────────────────────────────────────────────────

    def prompt_commit_action(self) -> ActionChoice:
        return self._prompt_action(COMMIT_ACTION_LABELS, COMMIT_KEY_MAP)

    def prompt_pr_action(self) -> ActionChoice:
        return self._prompt_action(PR_ACTION_LABELS, PR_KEY_MAP)

    def prompt_feedback(self) -> str:
        return Prompt.ask("\n[secondary]Feedback[/secondary]")

    def _prompt_action(
        self,
        labels: dict[ActionChoice, str],
        key_map: dict[str, ActionChoice],
    ) -> ActionChoice:
        self._console.print()
        self._render_action_bar(labels)
        while True:
            key = self._read_key().lower()
            if key == "\x03":  # Ctrl-C
                raise KeyboardInterrupt
            if key in key_map:
                return key_map[key]

    def _render_action_bar(self, labels: dict[ActionChoice, str]) -> None:
        width = self._console.size.width
        sep = "  │  " if width >= 80 else "  "
        options = sep.join(labels.values())
        self._console.print(
            Panel(options, border_style="secondary", padding=(0, 1))
        )

    def _read_key(self) -> str:
        """Read a single keypress.  Override in tests via instance assignment."""
        return _read_single_key()
