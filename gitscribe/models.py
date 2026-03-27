"""Dataclasses for gitscribe configuration and domain objects."""

from dataclasses import dataclass, field
from enum import Enum


class Style(Enum):
    PROFESSIONAL = "professional"
    FUN = "fun"
    CASUAL = "casual"


class CommitFormat(Enum):
    CONVENTIONAL = "conventional"
    GITMOJI = "gitmoji"
    NONE = "none"


class BodyLength(Enum):
    TITLE_ONLY = "title-only"
    SHORT = "short"
    LONG = "long"


BODY_LENGTH_DESCRIPTIONS: dict[BodyLength, str] = {
    BodyLength.TITLE_ONLY: "1 title + 0 body lines",
    BodyLength.SHORT: "1 title + 2-4 body lines",
    BodyLength.LONG: "1 title + 5 or more body lines",
}


@dataclass(frozen=True)
class ApiConfig:
    url: str = ""
    token: str = ""
    model: str = ""


@dataclass(frozen=True)
class CliConfig:
    command: str = ""
    model: str = ""


@dataclass(frozen=True)
class AiConfig:
    backend: str = "api"
    api: ApiConfig = field(default_factory=ApiConfig)
    cli: CliConfig = field(default_factory=CliConfig)


@dataclass(frozen=True)
class ThemeConfig:
    primary: str = "cyan"
    secondary: str = "magenta"
    accent: str = "green"
    error: str = "red"
    warning: str = "yellow"


@dataclass(frozen=True)
class CommitDefaults:
    style: Style = Style.PROFESSIONAL
    format: CommitFormat = CommitFormat.CONVENTIONAL
    body_length: BodyLength = BodyLength.SHORT


@dataclass(frozen=True)
class PrDefaults:
    style: Style = Style.PROFESSIONAL


@dataclass(frozen=True)
class GhConfig:
    command: str = "gh pr create --title {title} --body {body}"


@dataclass(frozen=True)
class AppConfig:
    ai: AiConfig = field(default_factory=AiConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    commit: CommitDefaults = field(default_factory=CommitDefaults)
    pr: PrDefaults = field(default_factory=PrDefaults)
    gh: GhConfig = field(default_factory=GhConfig)
