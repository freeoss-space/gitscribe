"""Tests for UI module."""

from dataclasses import dataclass
from io import StringIO

import pytest
from rich.console import Console

from gitscribe.actions import ActionChoice
from gitscribe.models import ThemeConfig
from gitscribe.theme import create_console, create_theme
from gitscribe.ui import COMMIT_KEY_MAP, PR_KEY_MAP, UI


@dataclass
class UIFixture:
    ui: UI
    console: Console


class TestUI:
    def _make_ui(self) -> UIFixture:
        console = create_console(ThemeConfig())
        console.file = StringIO()
        ui = UI(console)
        return UIFixture(ui=ui, console=console)

    def test_show_banner(self) -> None:
        fixture = self._make_ui()
        fixture.ui.show_banner()
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "GitScribe" in output

    def test_show_message(self) -> None:
        fixture = self._make_ui()
        fixture.ui.show_message("feat: add stuff", title="Commit Message")
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "Commit Message" in output

    def test_show_error(self) -> None:
        fixture = self._make_ui()
        fixture.ui.show_error("something went wrong")
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "something went wrong" in output

    def test_show_success(self) -> None:
        fixture = self._make_ui()
        fixture.ui.show_success("done!")
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "done!" in output

    def test_show_diff_stats(self) -> None:
        fixture = self._make_ui()
        diff = "--- a/file.py\n+++ b/file.py\n+new line\n-old line"
        fixture.ui.show_diff_stats(diff)
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "+1" in output
        assert "-1" in output

    def test_show_diff_stats_counts_changed_lines_not_total_diff_lines(self) -> None:
        fixture = self._make_ui()
        # diff has 4 lines total but only 2 are changed (1 addition + 1 deletion)
        diff = "--- a/file.py\n+++ b/file.py\n+new line\n-old line"
        fixture.ui.show_diff_stats(diff)
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "(2 lines changed)" in output

    def test_show_diff_stats_excludes_context_lines_from_count(self) -> None:
        fixture = self._make_ui()
        # diff with context lines (space-prefixed) should not count them
        diff = "--- a/file.py\n+++ b/file.py\n context\n+added\n-removed\n context2"
        fixture.ui.show_diff_stats(diff)
        output = fixture.console.file.getvalue()  # type: ignore[union-attr]
        assert "+1" in output
        assert "-1" in output
        assert "(2 lines changed)" in output


class TestKeyMaps:
    def test_commit_key_map_complete(self) -> None:
        assert COMMIT_KEY_MAP["c"] == ActionChoice.COMMIT
        assert COMMIT_KEY_MAP["p"] == ActionChoice.COPY
        assert COMMIT_KEY_MAP["r"] == ActionChoice.REGENERATE
        assert COMMIT_KEY_MAP["f"] == ActionChoice.REGENERATE_FEEDBACK
        assert COMMIT_KEY_MAP["e"] == ActionChoice.EDIT
        assert COMMIT_KEY_MAP["q"] == ActionChoice.QUIT

    def test_pr_key_map_complete(self) -> None:
        assert PR_KEY_MAP["c"] == ActionChoice.CREATE_PR
        assert PR_KEY_MAP["p"] == ActionChoice.COPY
        assert PR_KEY_MAP["r"] == ActionChoice.REGENERATE
        assert PR_KEY_MAP["f"] == ActionChoice.REGENERATE_FEEDBACK
        assert PR_KEY_MAP["e"] == ActionChoice.EDIT
        assert PR_KEY_MAP["q"] == ActionChoice.QUIT


# ── NEW TDD TESTS ─────────────────────────────────────────────────────────────


class TestSingleKeyPrompt:
    """Prompt actions must respond to a single keypress — no Enter required."""

    def _make_ui(self, *keys: str) -> UI:
        console = Console(width=80, theme=create_theme(ThemeConfig()), file=StringIO())
        ui = UI(console)
        key_iter = iter(keys)
        ui._read_key = lambda: next(key_iter)  # type: ignore[method-assign]
        return ui

    def test_commit_c_returns_commit_action(self) -> None:
        assert self._make_ui("c").prompt_commit_action() == ActionChoice.COMMIT

    def test_commit_p_returns_copy(self) -> None:
        assert self._make_ui("p").prompt_commit_action() == ActionChoice.COPY

    def test_commit_r_returns_regenerate(self) -> None:
        assert self._make_ui("r").prompt_commit_action() == ActionChoice.REGENERATE

    def test_commit_f_returns_regenerate_feedback(self) -> None:
        assert self._make_ui("f").prompt_commit_action() == ActionChoice.REGENERATE_FEEDBACK

    def test_commit_e_returns_edit(self) -> None:
        assert self._make_ui("e").prompt_commit_action() == ActionChoice.EDIT

    def test_commit_q_returns_quit(self) -> None:
        assert self._make_ui("q").prompt_commit_action() == ActionChoice.QUIT

    def test_invalid_keys_silently_ignored_until_valid(self) -> None:
        assert self._make_ui("x", "z", "1", "q").prompt_commit_action() == ActionChoice.QUIT

    def test_ctrl_c_raises_keyboard_interrupt(self) -> None:
        with pytest.raises(KeyboardInterrupt):
            self._make_ui("\x03").prompt_commit_action()

    def test_uppercase_key_normalised_to_lowercase(self) -> None:
        assert self._make_ui("C").prompt_commit_action() == ActionChoice.COMMIT

    def test_pr_c_returns_create_pr(self) -> None:
        assert self._make_ui("c").prompt_pr_action() == ActionChoice.CREATE_PR

    def test_pr_q_returns_quit(self) -> None:
        assert self._make_ui("q").prompt_pr_action() == ActionChoice.QUIT

    def test_pr_e_returns_edit(self) -> None:
        assert self._make_ui("e").prompt_pr_action() == ActionChoice.EDIT


class TestResponsiveBanner:
    """Banner subtitle adapts to the terminal width."""

    def _make_ui(self, width: int) -> tuple[UI, StringIO]:
        buf: StringIO = StringIO()
        console = Console(width=width, theme=create_theme(ThemeConfig()), file=buf)
        return UI(console), buf

    def test_banner_shows_gitscribe_at_narrow_width(self) -> None:
        ui, buf = self._make_ui(40)
        ui.show_banner()
        assert "GitScribe" in buf.getvalue()

    def test_banner_shows_full_subtitle_on_wide_terminal(self) -> None:
        ui, buf = self._make_ui(80)
        ui.show_banner()
        assert "AI-powered git messages" in buf.getvalue()

    def test_banner_omits_full_subtitle_on_narrow_terminal(self) -> None:
        ui, buf = self._make_ui(40)
        ui.show_banner()
        assert "AI-powered git messages" not in buf.getvalue()

    def test_banner_shows_short_subtitle_on_narrow_terminal(self) -> None:
        ui, buf = self._make_ui(40)
        ui.show_banner()
        assert "GitScribe" in buf.getvalue()


class TestDiffStatsVisualBar:
    """Diff stats include a visual █ bar proportional to additions/deletions."""

    def _make_ui(self) -> tuple[UI, StringIO]:
        buf: StringIO = StringIO()
        console = Console(width=80, theme=create_theme(ThemeConfig()), file=buf)
        return UI(console), buf

    def test_diff_stats_shows_bar_character(self) -> None:
        ui, buf = self._make_ui()
        ui.show_diff_stats("--- a/f.py\n+++ b/f.py\n+added\n-removed")
        assert "█" in buf.getvalue()

    def test_diff_stats_no_bar_when_no_changes(self) -> None:
        ui, buf = self._make_ui()
        ui.show_diff_stats("--- a/f.py\n+++ b/f.py")
        assert "(0 lines changed)" in buf.getvalue()

    def test_build_diff_bar_empty_for_zero_total(self) -> None:
        ui, _ = self._make_ui()
        assert ui._build_diff_bar(0, 0, 0) == ""

    def test_build_diff_bar_contains_block_chars(self) -> None:
        ui, _ = self._make_ui()
        bar = ui._build_diff_bar(5, 5, 10)
        assert "█" in bar

    def test_build_diff_bar_addition_only(self) -> None:
        ui, _ = self._make_ui()
        bar = ui._build_diff_bar(10, 0, 10)
        assert "█" in bar

    def test_build_diff_bar_deletion_only(self) -> None:
        ui, _ = self._make_ui()
        bar = ui._build_diff_bar(0, 10, 10)
        assert "█" in bar


class TestVisualFeedback:
    """Error / success / warning messages include distinctive Unicode icons."""

    def _make_ui(self) -> tuple[UI, StringIO]:
        buf: StringIO = StringIO()
        console = Console(width=80, theme=create_theme(ThemeConfig()), file=buf)
        return UI(console), buf

    def test_show_error_includes_cross_icon(self) -> None:
        ui, buf = self._make_ui()
        ui.show_error("something failed")
        assert "✗" in buf.getvalue()

    def test_show_success_includes_check_icon(self) -> None:
        ui, buf = self._make_ui()
        ui.show_success("all done")
        assert "✓" in buf.getvalue()

    def test_show_warning_includes_warning_icon(self) -> None:
        ui, buf = self._make_ui()
        ui.show_warning("be careful")
        assert "⚠" in buf.getvalue()


class TestActionBarDisplay:
    """Action bar renders all options above the key prompt."""

    def _make_ui(self, *keys: str) -> tuple[UI, StringIO]:
        buf: StringIO = StringIO()
        console = Console(width=80, theme=create_theme(ThemeConfig()), file=buf)
        ui = UI(console)
        key_iter = iter(keys)
        ui._read_key = lambda: next(key_iter)  # type: ignore[method-assign]
        return ui, buf

    def test_commit_action_bar_shows_commit_label(self) -> None:
        ui, buf = self._make_ui("q")
        ui.prompt_commit_action()
        assert "commit" in buf.getvalue().lower()

    def test_commit_action_bar_shows_quit_label(self) -> None:
        ui, buf = self._make_ui("q")
        ui.prompt_commit_action()
        assert "quit" in buf.getvalue().lower()

    def test_commit_action_bar_shows_regenerate_label(self) -> None:
        ui, buf = self._make_ui("q")
        ui.prompt_commit_action()
        assert "regenerate" in buf.getvalue().lower()

    def test_pr_action_bar_shows_create_pr_label(self) -> None:
        ui, buf = self._make_ui("q")
        ui.prompt_pr_action()
        assert "create pr" in buf.getvalue().lower()

    def test_narrow_action_bar_still_shows_all_labels(self) -> None:
        buf: StringIO = StringIO()
        console = Console(width=40, theme=create_theme(ThemeConfig()), file=buf)
        ui = UI(console)
        key_iter = iter(["q"])
        ui._read_key = lambda: next(key_iter)  # type: ignore[method-assign]
        ui.prompt_commit_action()
        output = buf.getvalue().lower()
        assert "commit" in output
        assert "quit" in output


class TestShowThinking:
    """show_thinking() is a context manager that wraps the generation spinner."""

    def _make_ui(self) -> UI:
        console = Console(width=80, theme=create_theme(ThemeConfig()), file=StringIO())
        return UI(console)

    def test_show_thinking_is_context_manager(self) -> None:
        ui = self._make_ui()
        with ui.show_thinking():
            pass  # must not raise

    def test_show_thinking_yields_control(self) -> None:
        ui = self._make_ui()
        ran = False
        with ui.show_thinking():
            ran = True
        assert ran
