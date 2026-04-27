# Idea 14 — Configurable system prompt / persona for API backend

**Confidence: 84%**

## What it is

The OpenAI chat-completions API supports a `"system"` role message that sets the
model's persona and standing instructions. Expose this as `ai.api.system_prompt` in
config. The `ApiBackend` prepends it to the messages list:

```python
# models.py
@dataclass(frozen=True)
class ApiConfig:
    url: str = ""
    token: str = ""
    model: str = ""
    system_prompt: str = "You are an expert software engineer who writes clear, concise git commit messages."
    temperature: float = 0.7
```

```python
# ai_backend.py — ApiBackend.generate
messages = []
if self._config.system_prompt:
    messages.append({"role": "system", "content": self._config.system_prompt})
messages.append({"role": "user", "content": prompt})
```

## Why it is a good improvement

A system prompt that sets a domain-specific persona (e.g., "You follow the Angular
commit convention strictly") consistently improves output quality compared to weaving
instructions into the user prompt. It is the standard recommended way to use chat models.

## Possible downsides

- Some third-party API proxies ignore the `system` role; negligible downside since it
  falls back gracefully.
- Slightly increases prompt token count.
