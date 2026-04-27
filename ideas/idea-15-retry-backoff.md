# Idea 15 — Retry with exponential back-off

**Confidence: 91%**

## What it is

Wrap `ApiBackend.generate` in a retry loop with exponential back-off for transient
errors (HTTP 429, 500, 502, 503, 504) and `aiohttp.ClientError`. Use at most 3 retries
with jitter (0.5 s, 1 s, 2 s base delays).

```python
import asyncio, random

MAX_RETRIES = 3
BASE_DELAY = 0.5

async def generate(self, prompt: str) -> str:
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await self._do_generate(prompt)
        except aiohttp.ClientResponseError as exc:
            if exc.status not in (429, 500, 502, 503, 504) or attempt == MAX_RETRIES:
                raise
        except aiohttp.ClientError:
            if attempt == MAX_RETRIES:
                raise
        delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.3)
        await asyncio.sleep(delay)
    raise RuntimeError("unreachable")
```

## Why it is a good improvement

Rate-limit (429) and gateway errors (502/503) are extremely common with public AI APIs.
Currently these cause a hard crash with an unformatted traceback. Retries make the tool
resilient without requiring user intervention.

## Possible downsides

- Adds latency when real errors occur (up to ~3 s for 3 retries).
- Should respect `Retry-After` headers from 429 responses for well-behaved APIs.
