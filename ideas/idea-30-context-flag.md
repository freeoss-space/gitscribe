# Idea 30 — `--context` flag for extra prompt context

**Confidence: 88%**

## What it is

Add a `--context` / `-c` option to both `commit` and `pr` commands that appends
free-form text to the AI prompt. This lets users include ticket IDs, branch names,
or other metadata that the diff alone doesn't convey.

```
$ gitscribe commit --context "Fixes JIRA-1234 — add null check in payment processor"
$ gitscribe pr --context "Part of the Q2 authentication refactor; see ADR-0012"
```

```python
# prompt_builder.py
@staticmethod
def commit(diff, style, fmt, body_length, feedback=None, context=None) -> str:
    ...
    if context:
        parts.append(f"\nAdditional context: {context}")
    parts.append(f"\n{diff}")
    return " ".join(parts)
```

The `--context` flag is distinct from `--feedback` (which is used interactively after
seeing the generated message). `--context` is provided upfront, before generation.

## Why it is a good improvement

Diffs alone often lack context: a one-line change in a config file might be a critical
security fix or a trivial tweak. Attaching the ticket description or a brief intent
statement dramatically improves the generated message's relevance.

## Possible downsides

- Users may paste sensitive internal information that gets sent to a third-party AI
  API; this is inherent to any AI-assisted tool.
- Increases prompt token count.
