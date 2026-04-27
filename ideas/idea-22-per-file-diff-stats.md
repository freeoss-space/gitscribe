# Idea 22 — Per-file diff stats table

**Confidence: 85%**

## What it is

Replace the current single-line `+N -N (M lines changed)` summary with a Rich `Table`
that lists each changed file with its individual addition/deletion counts, similar to
`git diff --stat` output:

```
┌─────────────────────────────────┬──────────┬──────────┐
│ File                            │    +     │    -     │
├─────────────────────────────────┼──────────┼──────────┤
│ gitscribe/ai_backend.py         │   15     │    3     │
│ gitscribe/models.py             │    8     │    1     │
│ tests/test_ai_backend.py        │   24     │    0     │
└─────────────────────────────────┴──────────┴──────────┘
```

Parse the diff with a simple per-file scanner (split on `diff --git` headers, count
`+`/`-` lines per section). Lock files that were filtered out (Idea 9) are shown
with a `[muted](excluded)[/muted]` annotation.

## Why it is a good improvement

When running on a multi-file diff, the current summary gives no indication of *which*
files changed or *how much*, making it hard to sanity-check that the right files were
staged. The table provides this at a glance.

## Possible downsides

- Very large diffs produce very long tables; cap the display at 20 files with a
  "and N more..." row.
