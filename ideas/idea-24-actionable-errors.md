# Idea 24 — Actionable error messages

**Confidence: 90%**

## What it is

Wrap every call that can fail (API calls, subprocess calls, config loading, clipboard)
with structured error handling that appends a suggested fix to the error message.
Implement a central `handle_error(exc)` utility in `cli.py`:

```python
ERROR_HINTS = {
    "api.token": "Set GITSCRIBE_AI_API_TOKEN or run `gitscribe config` to add your API key.",
    "connection": "Check your internet connection and API URL (`gitscribe config show`).",
    "not a git repository": "Run `gitscribe` from inside a git repository.",
    "no staged changes": "Stage files with `git add <files>` before running `gitscribe commit`.",
    "CalledProcessError": "A git command failed. Run `git status` to check the repository state.",
}
```

For `aiohttp.ClientResponseError` with status 401: display
`"API authentication failed — check your token with gitscribe config validate"`.
For status 429: display `"Rate limit hit — reduce request frequency or upgrade your API plan"`.

## Why it is a good improvement

The current code lets most exceptions bubble up as raw Python tracebacks. New users see
`aiohttp.ClientConnectorError` and have no idea what to do. Actionable messages turn
confusion into a clear next step.

## Possible downsides

- Must not suppress the original exception entirely (use `--verbose` / `--debug` flag to
  re-raise for debugging).
