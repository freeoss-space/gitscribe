# Idea 27 — Expose `temperature` and `max_tokens` in config

**Confidence: 83%**

## What it is

Add `temperature: float` (default: `0.7`) and `max_tokens: int` (default: `0`, meaning
"let the API decide") to `ApiConfig`. Pass them through to the request payload.

```python
# models.py
@dataclass(frozen=True)
class ApiConfig:
    url: str = ""
    token: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 0         # 0 = omit from request

# ai_backend.py
payload = {
    "model": self._config.model,
    "messages": messages,
    "temperature": self._config.temperature,
}
if self._config.max_tokens > 0:
    payload["max_tokens"] = self._config.max_tokens
```

## Why it is a good improvement

`temperature` directly controls creativity vs. consistency. Users generating highly
structured `conventional` commit messages want low temperature (0.1–0.3); users
choosing the `fun` style want higher temperature (0.9+). `max_tokens` lets users cap
cost/latency for short commit messages.

## Possible downsides

- Exposing raw model parameters may confuse novice users; good defaults mitigate this.
