# Idea 25 — `gitscribe config set <key> <value>`

**Confidence: 88%**

## What it is

A subcommand that sets a single config value by dotted-path key without opening the editor:

```
$ gitscribe config set ai.api.token sk-abc123
$ gitscribe config set commit.style fun
$ gitscribe config set ai.api.model gpt-4o
```

Implementation: parse the dotted key into a path, load config as a raw dict, apply the
value using `functools.reduce` to walk the nested dict, then serialize and write back.

```python
@config_app.command(name="set")
def config_set(key: str, value: str):
    config_mgr = ConfigManager()
    raw = config_mgr.load_raw()          # returns dict, not AppConfig
    parts = key.split(".")
    node = raw
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    config_mgr.save_raw(raw)
    typer.echo(f"Set {key} = {value}")
```

## Why it is a good improvement

CI/CD onboarding scripts, dotfile managers, and setup playbooks all need a scriptable
way to configure gitscribe. Opening an editor in a script is impractical.

## Possible downsides

- Setting an invalid value (e.g., `commit.style = typo`) fails silently until the
  next `gitscribe commit`; should call `validate` after each `set`.
