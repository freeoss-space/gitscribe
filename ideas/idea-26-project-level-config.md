# Idea 26 — Project-level `.gitscribe.json` config

**Confidence: 87%**

## What it is

Walk up from the current working directory to the git repo root looking for a
`.gitscribe.json` file. If found, deep-merge it on top of the user config (project
config takes precedence for non-credential fields; credentials are always taken from
the user config).

```python
# config_manager.py
def load(self) -> AppConfig:
    user_data = self._load_file(self.config_path)
    project_data = self._load_project_config()
    merged = _deep_merge(user_data, project_data) if project_data else user_data
    return self._parse_config(merged)

def _load_project_config(self) -> dict | None:
    try:
        root = GitOperations().get_repo_root()
    except subprocess.CalledProcessError:
        return None
    path = root / ".gitscribe.json"
    if path.exists():
        return json.loads(path.read_text())
    return None
```

Sensitive fields (`ai.api.token`, `ai.api.url`) are ignored in project-level config to
prevent token leakage via committed config files. Document this clearly.

## Why it is a good improvement

Teams can share a `.gitscribe.json` that enforces the project's commit convention (e.g.,
`conventional` format, `professional` style, custom prompt template) without each
developer manually configuring their user config.

## Possible downsides

- Must never allow `token` in the project config (accidental secret commit).
- Precedence rules need clear documentation.
