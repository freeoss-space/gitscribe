"""Tests for prompt builder."""

from gitscribe.models import BodyLength, CommitFormat, Style
from gitscribe.prompt_builder import PromptBuilder


class TestCommitPrompt:
    def test_basic_commit_prompt(self) -> None:
        prompt = PromptBuilder.commit(
            diff="diff --git a/file.py\n+new line",
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        assert "git diff" in prompt
        assert "commit message" in prompt.lower()
        assert "professional" in prompt.lower()
        assert "conventional" in prompt.lower()
        assert "2-4 body" in prompt
        assert "diff --git a/file.py" in prompt

    def test_commit_prompt_fun_style(self) -> None:
        prompt = PromptBuilder.commit(
            diff="some diff",
            style=Style.FUN,
            fmt=CommitFormat.GITMOJI,
            body_length=BodyLength.TITLE_ONLY,
        )
        assert "fun" in prompt.lower()
        assert "gitmoji" in prompt.lower()
        assert "0 body" in prompt

    def test_commit_prompt_long_body(self) -> None:
        prompt = PromptBuilder.commit(
            diff="some diff",
            style=Style.CASUAL,
            fmt=CommitFormat.NONE,
            body_length=BodyLength.LONG,
        )
        assert "casual" in prompt.lower()
        assert "5 or more" in prompt

    def test_commit_with_feedback(self) -> None:
        prompt = PromptBuilder.commit(
            diff="some diff",
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
            feedback="Make it shorter",
        )
        assert "Make it shorter" in prompt
        assert "feedback" in prompt.lower()

    def test_commit_prompt_has_plain_text_instruction(self) -> None:
        prompt = PromptBuilder.commit(
            diff="some diff",
            style=Style.PROFESSIONAL,
            fmt=CommitFormat.CONVENTIONAL,
            body_length=BodyLength.SHORT,
        )
        assert "Respond only with plain text" in prompt
        assert "Do not format with markdown" in prompt
        assert "Do not format as JSON" in prompt
        assert "Do not format as code blocks" in prompt
        assert "Reply with nothing but the commit message" in prompt


class TestPrPrompt:
    def test_basic_pr_prompt(self) -> None:
        prompt = PromptBuilder.pr(
            diff="diff content",
            style=Style.PROFESSIONAL,
        )
        assert "pull request" in prompt.lower()
        assert "professional" in prompt.lower()
        assert "diff content" in prompt

    def test_pr_prompt_with_template(self) -> None:
        template = "## Description\n\n## Changes"
        prompt = PromptBuilder.pr(
            diff="diff content",
            style=Style.CASUAL,
            template=template,
        )
        assert "## Description" in prompt
        assert "follow" in prompt.lower() and "template" in prompt.lower()

    def test_pr_prompt_without_template(self) -> None:
        prompt = PromptBuilder.pr(
            diff="diff content",
            style=Style.FUN,
        )
        assert "template" not in prompt.lower() or "no template" in prompt.lower()

    def test_pr_with_feedback(self) -> None:
        prompt = PromptBuilder.pr(
            diff="diff content",
            style=Style.PROFESSIONAL,
            feedback="Add more detail about the API changes",
        )
        assert "Add more detail about the API changes" in prompt

    def test_pr_prompt_has_plain_text_instruction(self) -> None:
        prompt = PromptBuilder.pr(
            diff="diff content",
            style=Style.PROFESSIONAL,
        )
        assert "Respond only with plain text" in prompt
        assert "Do not format with markdown" in prompt
        assert "Do not format as JSON" in prompt
        assert "Do not format as code blocks" in prompt
        assert "Reply with nothing but the PR message" in prompt
