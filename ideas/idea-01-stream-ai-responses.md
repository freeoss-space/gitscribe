# Idea 1 — Stream AI responses token-by-token

**Confidence: 88%**

## What it is

Instead of waiting for the full response from the API, use HTTP Server-Sent Events (SSE)
streaming so that each token appears in the terminal as soon as the model produces it.
The `AiBackend.generate` interface gains a `stream()` async-generator sibling (or an
optional `streaming: bool` parameter). The `ApiBackend` switches the request to
`"stream": true` and yields each chunk as it arrives. The UI shows an animated live-render
panel that updates in place using `rich.live.Live`.

```python
# ai_backend.py — ApiBackend addition
async def stream(self, prompt: str) -> AsyncIterator[str]:
    async with aiohttp.ClientSession(timeout=...) as session:
        async with session.post(
            f"{self._config.url}/chat/completions",
            headers={...},
            json={"model": self._config.model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": self._config.temperature,
                  "stream": True},
        ) as response:
            response.raise_for_status()
            async for line in response.content:
                text = line.decode().strip()
                if text.startswith("data: ") and text != "data: [DONE]":
                    data = json.loads(text[6:])
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
```

```python
# commit_command.py — use Live panel
from rich.live import Live
async def _stream_generate(self, prompt: str) -> str:
    buffer = ""
    with Live(console=self._console, refresh_per_second=15) as live:
        async for chunk in self._ai.stream(prompt):
            buffer += chunk
            live.update(Panel(buffer, title="Generating..."))
    return buffer
```

The `CliBackend` does not stream (process stdout is line-buffered anyway) and
falls back to the current blocking approach.

## Why it is a good improvement

The current UX shows a spinner that can sit for 10-30 seconds with no feedback.
Streaming reduces *perceived* latency to near-zero and lets the user abort early if
the direction is clearly wrong.

## Possible downsides

- Some self-hosted or proxy API endpoints do not correctly implement SSE; needs a
  graceful fallback.
- Adds modest complexity to the `AiBackend` interface.
- `CliBackend` does not benefit.
