"""Tests for AI backends."""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from gitscribe.ai_backend import ApiBackend, CliBackend, create_backend, resolve_ai_config
from gitscribe.models import AiConfig, ApiConfig, CliConfig


class TestApiBackend:
    @pytest.mark.anyio
    async def test_generate_sends_request(self) -> None:
        config = ApiConfig(url="http://localhost:8080/v1", token="sk-test", model="gpt-4")
        backend = ApiBackend(config)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "feat: add feature"}}]}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await backend.generate("Generate a commit message")
            assert result == "feat: add feature"
            mock_session.post.assert_called_once()
            call_kwargs = mock_session.post.call_args
            assert call_kwargs[1]["json"]["model"] == "gpt-4"
            assert call_kwargs[1]["json"]["messages"][0]["content"] == "Generate a commit message"

    @pytest.mark.anyio
    async def test_generate_raises_on_error(self) -> None:
        config = ApiConfig(url="http://localhost:8080/v1", token="sk-test", model="gpt-4")
        backend = ApiBackend(config)

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=500,
                message="Server Error",
            )
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("aiohttp.ClientSession", return_value=mock_session),
            pytest.raises(aiohttp.ClientResponseError),
        ):
            await backend.generate("test")


class TestCliBackend:
    @pytest.mark.anyio
    async def test_generate_runs_command(self) -> None:
        config = CliConfig(command="llm -m {model}", model="gpt-4")
        backend = CliBackend(config)

        mock_result = MagicMock()
        mock_result.stdout = "feat: add feature\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = await backend.generate("Generate a commit message")
            assert result == "feat: add feature"
            cmd = mock_run.call_args[0][0]
            assert "llm" in cmd
            assert "-m" in cmd
            assert "gpt-4" in cmd

    @pytest.mark.anyio
    async def test_generate_raises_on_failure(self) -> None:
        config = CliConfig(command="llm -m {model}", model="gpt-4")
        backend = CliBackend(config)

        with (
            patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "llm")),
            pytest.raises(subprocess.CalledProcessError),
        ):
            await backend.generate("test")


class TestCreateBackend:
    def test_create_api_backend(self) -> None:
        config = AiConfig(
            backend="api",
            api=ApiConfig(url="http://localhost", token="sk", model="gpt-4"),
        )
        backend = create_backend(config)
        assert isinstance(backend, ApiBackend)

    def test_create_cli_backend(self) -> None:
        config = AiConfig(
            backend="cli",
            cli=CliConfig(command="llm {model}", model="gpt-4"),
        )
        backend = create_backend(config)
        assert isinstance(backend, CliBackend)

    def test_create_unknown_backend_raises(self) -> None:
        config = AiConfig(backend="unknown")
        with pytest.raises(ValueError, match="Unknown backend"):
            create_backend(config)


class TestResolveAiConfig:
    def test_no_overrides_returns_same_api_config(self) -> None:
        ai = AiConfig(backend="api", api=ApiConfig(url="http://x", token="t", model="global"))
        resolved = resolve_ai_config(ai)
        assert resolved.api.model == "global"
        assert resolved.backend == "api"

    def test_model_override_replaces_api_model(self) -> None:
        ai = AiConfig(backend="api", api=ApiConfig(url="http://x", token="t", model="global"))
        resolved = resolve_ai_config(ai, model="override-model")
        assert resolved.api.model == "override-model"

    def test_model_override_replaces_cli_model(self) -> None:
        ai = AiConfig(backend="cli", cli=CliConfig(command="claude", model="global"))
        resolved = resolve_ai_config(ai, model="override-model")
        assert resolved.cli.model == "override-model"

    def test_command_override_replaces_cli_command(self) -> None:
        ai = AiConfig(backend="cli", cli=CliConfig(command="claude", model="m"))
        resolved = resolve_ai_config(ai, command="claude --fast")
        assert resolved.cli.command == "claude --fast"

    def test_empty_model_override_keeps_global(self) -> None:
        ai = AiConfig(backend="api", api=ApiConfig(model="global"))
        resolved = resolve_ai_config(ai, model="")
        assert resolved.api.model == "global"

    def test_empty_command_override_keeps_global(self) -> None:
        ai = AiConfig(backend="cli", cli=CliConfig(command="claude", model="m"))
        resolved = resolve_ai_config(ai, command="")
        assert resolved.cli.command == "claude"

    def test_command_override_ignored_for_api_backend(self) -> None:
        ai = AiConfig(backend="api", api=ApiConfig(model="global"))
        resolved = resolve_ai_config(ai, command="ignored")
        assert resolved.api.model == "global"

    def test_both_overrides_applied(self) -> None:
        ai = AiConfig(backend="cli", cli=CliConfig(command="claude", model="base"))
        resolved = resolve_ai_config(ai, model="new-model", command="new-cmd")
        assert resolved.cli.model == "new-model"
        assert resolved.cli.command == "new-cmd"
