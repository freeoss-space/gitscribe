"""Prompt builder for gitscribe."""

from gitscribe.models import (
    BODY_LENGTH_DESCRIPTIONS,
    BodyLength,
    CommitFormat,
    Style,
)

FORMAT_DESCRIPTIONS: dict[CommitFormat, str] = {
    CommitFormat.CONVENTIONAL: "Conventional Commits (e.g., feat:, fix:, chore:)",
    CommitFormat.GITMOJI: "Gitmoji (e.g., :sparkles:, :bug:, :recycle:)",
    CommitFormat.NONE: "No specific format",
}

_PLAIN_TEXT_INSTRUCTION = (
    "Respond only with plain text."
    " Do not format with markdown."
    " Do not format as JSON."
    " Do not format as code blocks."
)


class PromptBuilder:
    """Builds prompts for AI backends."""

    @staticmethod
    def commit(
        diff: str,
        style: Style,
        fmt: CommitFormat,
        body_length: BodyLength,
        feedback: str | None = None,
    ) -> str:
        body_desc = BODY_LENGTH_DESCRIPTIONS[body_length]
        format_desc = FORMAT_DESCRIPTIONS[fmt]

        parts = [
            "Use the following git diff to generate a commit message.",
            f"Style: {style.value}.",
            f"Format: {format_desc}.",
            f"Max body lines: {body_desc}.",
            f"{_PLAIN_TEXT_INSTRUCTION} Reply with nothing but the commit message.",
        ]

        if feedback:
            parts.append(f"\nAdditional feedback: {feedback}")

        parts.append(f"\n{diff}")

        return " ".join(parts)

    @staticmethod
    def pr(
        diff: str,
        style: Style,
        template: str | None = None,
        feedback: str | None = None,
    ) -> str:
        parts = [
            "Use the following git diff to create a pull request message.",
            f"Style: {style.value}.",
            f"{_PLAIN_TEXT_INSTRUCTION} Reply with nothing but the PR message.",
        ]

        if template:
            parts.append(f"\nFollow this PR template strictly:\n{template}")

        if feedback:
            parts.append(f"\nAdditional feedback: {feedback}")

        parts.append(f"\n{diff}")

        return " ".join(parts)
