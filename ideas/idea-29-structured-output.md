# Idea 29 — Structured output formats for `--output-only`

**Confidence: 86%**

## What it is

Add an `--output-format` option to both `commit` and `pr` commands that controls the
format of `--output-only` output. Supported formats:

- `text` (default): raw message as-is (current behavior)
- `json`: `{"title": "...", "body": "...", "full": "..."}`
- `md`: message wrapped in a markdown code block with a header

```python
# cli.py
output_format: Annotated[
    str,
    typer.Option("--output-format", help="Output format for --output-only: text, json, md"),
] = "text"
```

```python
# commit_command.py
if output_only:
    lines = message.strip().split("\n", 1)
    title = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else ""
    if output_format == "json":
        import json
        print(json.dumps({"title": title, "body": body, "full": message}))
    elif output_format == "md":
        print(f"# {title}\n\n{body}")
    else:
        print(message)
    return
```

## Why it is a good improvement

`--output-only` exists precisely for scripting/CI use. JSON output enables downstream
tools (GitHub Actions steps, custom hooks, PR bots) to consume title and body separately
without fragile string parsing.

## Possible downsides

- Adds an option combination (`--output-only` + `--output-format`) that only makes
  sense together; should error if `--output-format` is used without `--output-only`.
