# Idea 10 — Token count estimation and warning

**Confidence: 80%**

## What it is

Before calling the AI, compute a rough token estimate using the heuristic
`tokens ≈ len(text) / 4` (widely accepted for English-heavy code). If the estimate
exceeds a configurable threshold (default: `8000` tokens), print a warning and offer
the user a chance to abort or truncate.

```python
# In CommitCommand.run / PrCommand.run
APPROX_TOKEN_WARNING = 8_000

estimated_tokens = len(prompt.encode()) // 4
if estimated_tokens > APPROX_TOKEN_WARNING:
    self._ui.show_warning(
        f"Estimated prompt size: ~{estimated_tokens:,} tokens. "
        "This may exceed your model's context window or cost more than expected."
    )
    if not self._ui.confirm("Continue anyway?"):
        return
```

## Why it is a good improvement

Without this, large diffs cause silent API failures (HTTP 400 / context length exceeded)
with no guidance. The warning is non-blocking by default and requires zero new dependencies.

## Possible downsides

- The heuristic is inaccurate for non-Latin code (CJK, Arabic); could be off by 2–3×.
- Adds an interactive pause that could be annoying for `--output-only` mode (should be
  skipped in that mode).
