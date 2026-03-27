"""CLI entry point for gitscribe."""

from dataclasses import dataclass
from typing import Annotated

import typer

from gitscribe.ai_backend import create_backend
from gitscribe.commit_command import CommitCommand
from gitscribe.config_manager import ConfigManager
from gitscribe.git_operations import GitOperations
from gitscribe.models import BodyLength, CommitFormat, Style
from gitscribe.pr_command import PrCommand
from gitscribe.theme import create_console
from gitscribe.ui import UI

app = typer.Typer(
    name="gitscribe",
    help="AI-powered git commit and PR message generator.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@dataclass
class Dependencies:
    config_manager: ConfigManager
    ui: UI
    git_ops: GitOperations


def _load_deps() -> Dependencies:
    config_mgr = ConfigManager()
    config = config_mgr.load()
    console = create_console(config.theme)
    ui = UI(console)
    git_ops = GitOperations()
    return Dependencies(config_manager=config_mgr, ui=ui, git_ops=git_ops)


@app.command(name="commit", help="Generate a commit message from staged changes.")
@app.command(name="c", hidden=True)
def commit_cmd(
    style: Annotated[
        str | None,
        typer.Option("--style", "-s", help="Message style: professional, fun, casual"),
    ] = None,
    fmt: Annotated[
        str | None,
        typer.Option("--format", "-f", help="Message format: conventional, gitmoji, none"),
    ] = None,
    body_length: Annotated[
        str | None,
        typer.Option("--body", "-b", help="Body length: title-only, short, long"),
    ] = None,
) -> None:
    deps = _load_deps()
    config = deps.config_manager.load()

    resolved_style = Style(style) if style else config.commit.style
    resolved_fmt = CommitFormat(fmt) if fmt else config.commit.format
    resolved_body = BodyLength(body_length) if body_length else config.commit.body_length

    backend = create_backend(config.ai)
    console = create_console(config.theme)

    cmd = CommitCommand(
        ai_backend=backend,
        git_ops=deps.git_ops,
        ui=deps.ui,
        console=console,
        gh_config=config.gh,
    )
    cmd.run(style=resolved_style, fmt=resolved_fmt, body_length=resolved_body)


@app.command(name="pr", help="Generate a PR message from branch diff.")
def pr_cmd(
    style: Annotated[
        str | None,
        typer.Option("--style", "-s", help="Message style: professional, fun, casual"),
    ] = None,
    base: Annotated[
        str | None,
        typer.Option("--base", help="Base branch to diff against (default: auto-detect)"),
    ] = None,
) -> None:
    deps = _load_deps()
    config = deps.config_manager.load()

    resolved_style = Style(style) if style else config.pr.style

    backend = create_backend(config.ai)
    console = create_console(config.theme)

    cmd = PrCommand(
        ai_backend=backend,
        git_ops=deps.git_ops,
        ui=deps.ui,
        console=console,
        gh_config=config.gh,
    )
    cmd.run(style=resolved_style, base_branch=base)


if __name__ == "__main__":
    app()
