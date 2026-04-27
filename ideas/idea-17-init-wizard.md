# Idea 17 — `gitscribe init` guided-setup wizard

**Confidence: 86%**

## What it is

A new top-level command that walks the user through configuring gitscribe for the first
time via interactive prompts, then writes the config file.

```
$ gitscribe init

Welcome to gitscribe!

? AI backend [api / cli]: api
? API URL (e.g. https://api.openai.com/v1): https://api.openai.com/v1
? API token: sk-...
? Model (e.g. gpt-4o-mini): gpt-4o-mini
? Default commit style [professional / fun / casual]: professional
? Default commit format [conventional / gitmoji / none]: conventional

✅ Config written to ~/.config/gitscribe/config.json
Run `gitscribe commit` to generate your first commit message!
```

Uses `typer.prompt` / `rich.prompt.Prompt` for each question with sensible defaults.
Runs `config validate` automatically at the end.

## Why it is a good improvement

First-time setup is the highest-friction point for new users. A wizard eliminates
the need to understand the JSON schema, remember file paths, or read documentation.

## Possible downsides

- Overwrites existing config (should check first and ask for confirmation).
- Interactive — not usable in CI/CD (but `config set` — Idea 25 — covers that case).
