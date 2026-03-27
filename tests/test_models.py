"""Tests for gitscribe models."""

from gitscribe.models import (
    BODY_LENGTH_DESCRIPTIONS,
    AiConfig,
    ApiConfig,
    AppConfig,
    BodyLength,
    CliConfig,
    CommitDefaults,
    CommitFormat,
    GhConfig,
    PrDefaults,
    Style,
    ThemeConfig,
)


class TestEnums:
    def test_style_values(self) -> None:
        assert Style.PROFESSIONAL.value == "professional"
        assert Style.FUN.value == "fun"
        assert Style.CASUAL.value == "casual"

    def test_commit_format_values(self) -> None:
        assert CommitFormat.CONVENTIONAL.value == "conventional"
        assert CommitFormat.GITMOJI.value == "gitmoji"
        assert CommitFormat.NONE.value == "none"

    def test_body_length_values(self) -> None:
        assert BodyLength.TITLE_ONLY.value == "title-only"
        assert BodyLength.SHORT.value == "short"
        assert BodyLength.LONG.value == "long"

    def test_body_length_descriptions(self) -> None:
        assert BodyLength.TITLE_ONLY in BODY_LENGTH_DESCRIPTIONS
        assert BodyLength.SHORT in BODY_LENGTH_DESCRIPTIONS
        assert BodyLength.LONG in BODY_LENGTH_DESCRIPTIONS


class TestApiConfig:
    def test_defaults(self) -> None:
        config = ApiConfig()
        assert config.url == ""
        assert config.token == ""
        assert config.model == ""

    def test_custom_values(self) -> None:
        config = ApiConfig(url="http://localhost:8080", token="sk-123", model="gpt-4")
        assert config.url == "http://localhost:8080"
        assert config.token == "sk-123"
        assert config.model == "gpt-4"

    def test_frozen(self) -> None:
        config = ApiConfig()
        try:
            config.url = "new"  # type: ignore[misc]
            raise AssertionError("Should raise")
        except AttributeError:
            pass


class TestCliConfig:
    def test_defaults(self) -> None:
        config = CliConfig()
        assert config.command == ""
        assert config.model == ""


class TestAiConfig:
    def test_defaults(self) -> None:
        config = AiConfig()
        assert config.backend == "api"
        assert isinstance(config.api, ApiConfig)
        assert isinstance(config.cli, CliConfig)


class TestThemeConfig:
    def test_defaults(self) -> None:
        theme = ThemeConfig()
        assert theme.primary == "cyan"
        assert theme.secondary == "magenta"
        assert theme.accent == "green"
        assert theme.error == "red"
        assert theme.warning == "yellow"


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig()
        assert isinstance(config.ai, AiConfig)
        assert isinstance(config.theme, ThemeConfig)
        assert isinstance(config.commit, CommitDefaults)
        assert isinstance(config.pr, PrDefaults)
        assert isinstance(config.gh, GhConfig)

    def test_commit_defaults(self) -> None:
        config = AppConfig()
        assert config.commit.style == Style.PROFESSIONAL
        assert config.commit.format == CommitFormat.CONVENTIONAL
        assert config.commit.body_length == BodyLength.SHORT

    def test_pr_defaults(self) -> None:
        config = AppConfig()
        assert config.pr.style == Style.PROFESSIONAL

    def test_gh_defaults(self) -> None:
        config = AppConfig()
        assert "gh pr create" in config.gh.command
