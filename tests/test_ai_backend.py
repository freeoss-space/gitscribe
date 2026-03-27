"""Tests for AI backends."""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from gitscribe.ai_backend import ApiBackend, CliBackend, create_backend
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
