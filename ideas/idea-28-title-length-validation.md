# Idea 28 — Commit message title length validation

**Confidence: 82%**

## What it is

After generation and before displaying the message, check if the first line (title)
exceeds 72 characters (the widely-accepted git convention). If it does, display a
warning and a suggestion to regenerate:

```python
# commit_command.py — after message = self._generate(...)
title_line = message.split("\n")[0]
if len(title_line) > 72:
    self._ui.show_warning(
        f"Title is {len(title_line)} chars (recommended ≤ 72). "
        "Consider regenerating with `body_length=short` or providing feedback."
    )
```

Also warn if the title exceeds 50 characters (the soft limit preferred by many
style guides), at a lower severity level.

## Why it is a good improvement

AI models frequently generate overly long commit titles, especially with the `long`
body length option. This check catches the problem before the user commits.

## Possible downsides

- The 72-char limit doesn't apply equally to all projects; should be configurable.
- `gitmoji` format messages have slightly different length constraints due to the emoji.
