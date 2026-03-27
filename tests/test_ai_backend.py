"""Tests for AI backends."""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from gitscribe.ai_backend import ApiBackend, CliBackend, create_backend
from gitscribe.models import AiConfig, ApiConfig, CliConfig


class TestApiBackend:
    @pytest.mark.anyio
    async def test_generate_sends_request(self) -> None:
        config = ApiConfig(url="http://localhost:8080/v1", token="sk-test", model="gpt-4")
        backend = ApiBackend(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "feat: add feature"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_response
        ) as mock_post:
            result = await backend.generate("Generate a commit message")
            assert result == "feat: add feature"
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args
            assert call_kwargs[1]["json"]["model"] == "gpt-4"
            assert call_kwargs[1]["json"]["messages"][0]["content"] == "Generate a commit message"

    @pytest.mark.anyio
    async def test_generate_raises_on_error(self) -> None:
        config = ApiConfig(url="http://localhost:8080/v1", token="sk-test", model="gpt-4")
        backend = ApiBackend(config)

        with (
            patch.object(
                httpx.AsyncClient,
                "post",
                new_callable=AsyncMock,
                side_effect=httpx.HTTPStatusError(
                    "error", request=MagicMock(), response=MagicMock()
                ),
            ),
            pytest.raises(httpx.HTTPStatusError),
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
