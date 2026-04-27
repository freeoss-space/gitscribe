# Idea 7 — Custom prompt templates in config

**Confidence: 82%**

## What it is

Add a `commit.prompt_template` and `pr.prompt_template` field to the config. The
template is a Python format string with named placeholders that `PromptBuilder` fills
in. Users can override the entire instruction set without forking the project.

```json
{
  "commit": {
    "prompt_template": "Write a {style} commit message in {format} format for this diff:\n{diff}"
  }
}
```

```python
# models.py
@dataclass(frozen=True)
class CommitDefaults:
    ...
    prompt_template: str = ""   # empty = use built-in

# prompt_builder.py
@staticmethod
def commit(diff, style, fmt, body_length, feedback=None, template="") -> str:
    if template:
        return template.format(
            diff=diff, style=style.value,
            format=fmt.value, body_length=body_length.value,
            feedback=feedback or "",
        )
    # existing logic
    ...
```

## Why it is a good improvement

Different teams have wildly different commit-message conventions. A finance team may
want ticket IDs prepended; an open-source project may want DCO sign-offs mentioned.
Custom templates make gitscribe adaptable without code changes.

## Possible downsides

- Bad templates (missing placeholders, syntax errors) produce confusing AI output.
- Needs basic template validation on load (check `str.format_map` with dummy values).
