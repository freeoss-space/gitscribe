# Idea 19 — Environment-variable overrides for config values

**Confidence: 92%**

## What it is

Allow every significant config value to be overridden via environment variables,
following the convention `GITSCRIBE_<SECTION>_<KEY>` (all upper-case, dots become
underscores):

| Env var | Config path |
|---|---|
| `GITSCRIBE_AI_BACKEND` | `ai.backend` |
| `GITSCRIBE_AI_API_URL` | `ai.api.url` |
| `GITSCRIBE_AI_API_TOKEN` | `ai.api.token` |
| `GITSCRIBE_AI_API_MODEL` | `ai.api.model` |
| `GITSCRIBE_COMMIT_STYLE` | `commit.style` |
| `GITSCRIBE_COMMIT_FORMAT` | `commit.format` |

The `ConfigManager.load()` method applies env-var overrides as a final layer on top of
the parsed file config (higher priority than any file-based setting):

```python
import os

def _apply_env_overrides(self, config: AppConfig) -> AppConfig:
    token = os.environ.get("GITSCRIBE_AI_API_TOKEN")
    if token:
        new_api = dataclasses.replace(config.ai.api, token=token)
        new_ai = dataclasses.replace(config.ai, api=new_api)
        config = dataclasses.replace(config, ai=new_ai)
    # ... repeat for other fields
    return config
```

## Why it is a good improvement

This is table-stakes for any CLI tool used in CI/CD. It lets teams inject the API token
via secrets management (GitHub Actions `${{ secrets.OPENAI_TOKEN }}`) without storing
it in the config file.

## Possible downsides

- Long list of env-var names to document and maintain.
- Precedence rules (env > project config > user config) must be clearly documented.
