# Idea 16 — `gitscribe config validate`

**Confidence: 88%**

## What it is

A subcommand that loads and validates the config file, printing a human-readable
report of any problems found:

```
✅  ai.backend: "api" — valid
❌  ai.api.url: empty — API backend requires a URL (e.g., https://api.openai.com/v1)
❌  ai.api.token: empty — API backend requires a token
✅  commit.style: "professional" — valid
```

Validation checks:
- If `backend == "api"`: `url` and `token` must be non-empty; `url` must look like a URL.
- If `backend == "cli"`: `command` must be non-empty and the executable must be found
  via `shutil.which`.
- Enum fields (`style`, `format`, `body_length`) must be valid enum values.
- Theme colors must be valid Rich color names.

## Why it is a good improvement

The most common support question for any CLI tool with a config file is "why isn't it
working?" This command turns silent misconfiguration into an actionable error list.

## Possible downsides

- Validating Rich color names requires loading the Rich color database.
- Network reachability of the API URL is out of scope for `validate`.
