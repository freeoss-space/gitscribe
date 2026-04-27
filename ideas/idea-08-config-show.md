# Idea 8 — `gitscribe config show`

**Confidence: 90%**

## What it is

A subcommand of `config` (or a standalone command `gitscribe config show`) that
pretty-prints the resolved config as JSON to stdout, with sensitive fields (API token)
redacted.

```python
@config_app.command(name="show")
def config_show():
    config_mgr = ConfigManager()
    config = config_mgr.load()
    data = config_mgr._serialize_config(config)
    # redact token
    data.setdefault("ai", {}).setdefault("api", {})["token"] = "***" if data["ai"]["api"]["token"] else ""
    typer.echo(json.dumps(data, indent=2))
```

## Why it is a good improvement

Debugging "why is gitscribe using model X?" is currently only possible by opening the
config file manually. `config show` is scriptable, CI-friendly, and surfaces the
platform-merged effective config (not just the raw file).

## Possible downsides

- Minimal. The only risk is accidentally printing a real token if the redaction logic
  has a bug; use an allowlist approach instead.
