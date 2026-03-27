"""AI backend implementations for gitscribe."""

import subprocess
from abc import ABC, abstractmethod

import aiohttp

from gitscribe.models import AiConfig, ApiConfig, CliConfig


class AiBackend(ABC):
    """Abstract base class for AI backends."""

    @abstractmethod
    async def generate(self, prompt: str) -> str: ...


class ApiBackend(AiBackend):
    """OpenAI-compatible API backend."""

    def __init__(self, config: ApiConfig) -> None:
        self._config = config

    async def generate(self, prompt: str) -> str:
        timeout = aiohttp.ClientTimeout(total=60.0)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                f"{self._config.url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._config.token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            ) as response,
        ):
            response.raise_for_status()
            data: dict = await response.json()
            return str(data["choices"][0]["message"]["content"]).strip()


class CliBackend(AiBackend):
    """CLI command backend."""

    def __init__(self, config: CliConfig) -> None:
        self._config = config

    async def generate(self, prompt: str) -> str:
        cmd = self._config.command.replace("{model}", self._config.model)
        parts = cmd.split()
        result = subprocess.run(
            [*parts, prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


def create_backend(config: AiConfig) -> AiBackend:
    """Factory function to create the appropriate AI backend."""
    if config.backend == "api":
        return ApiBackend(config.api)
    if config.backend == "cli":
        return CliBackend(config.cli)
    raise ValueError(f"Unknown backend: {config.backend}")
