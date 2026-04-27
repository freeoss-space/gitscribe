# Idea 2 — Diff size limiting and chunking

**Confidence: 92%**

## What it is

Add a `max_diff_bytes` config option (default: `40000` bytes ≈ 10 k tokens).
In `GitOperations`, after fetching a diff, apply a truncation/summarisation step:

1. Parse the diff into per-file hunks.
2. Exclude files that match a blocklist (see Idea 9).
3. If the total size still exceeds `max_diff_bytes`, truncate each remaining file's
   diff to its first N lines and append a `[... truncated ...]` marker.
4. If the diff is still over the limit after truncation, include only file-level stat
   lines (`git diff --stat`) and note that the full diff was too large.

```python
# git_operations.py
def get_staged_diff(self, max_bytes: int = 40_000) -> str:
    raw = self._run_git(["git", "diff", "--cached"])
    return _truncate_diff(raw, max_bytes)

def _truncate_diff(diff: str, max_bytes: int) -> str:
    if len(diff.encode()) <= max_bytes:
        return diff
    # ... split on "diff --git" headers and trim per-file
```

The UI shows a warning when truncation occurs:
`[warning]Diff truncated to 40 kB — some files omitted.[/warning]`

## Why it is a good improvement

Large diffs (e.g., adding a new library) silently cause API errors or nonsense output.
This makes failures visible and predictable.

## Possible downsides

- Truncation loses context; the commit message may miss some changes.
- The "right" limit varies by model; should be configurable.
