"""Tests for UI module."""

from dataclasses import dataclass
from io import StringIO

from rich.console import Console

from gitscribe.actions import ActionChoice
from gitscribe.models import ThemeConfig
from gitscribe.theme import create_console
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
