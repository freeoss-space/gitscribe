# Idea 13 — `--dry-run` flag

**Confidence: 95%**

## What it is

A `--dry-run` flag on both `commit` and `pr` commands that prints the exact prompt
that *would* be sent to the AI backend and exits without making any API call.

```python
# cli.py — commit_cmd
@app.command(name="commit")
def commit_cmd(
    ...,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the AI prompt and exit")] = False,
):
    ...
    if dry_run:
        prompt = PromptBuilder.commit(diff=diff, style=resolved_style, ...)
        typer.echo(prompt)
        return
```

## Why it is a good improvement

Prompt engineering and debugging are the most common pain points when gitscribe produces
bad output. `--dry-run` gives users full visibility into what the model receives, enabling
fast iteration on custom templates (Idea 7) and config tuning.

## Possible downsides

- None significant. Purely additive.
