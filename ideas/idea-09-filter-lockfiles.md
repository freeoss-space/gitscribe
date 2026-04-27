# Idea 9 — Filter lockfiles and generated files from the diff

**Confidence: 93%**

## What it is

Before sending the diff to the AI, strip hunks from files that match a blocklist of
patterns. The default blocklist includes the most common noise-generating files:

```python
DEFAULT_EXCLUDE_PATTERNS = [
    "*.lock",         # package-lock.json, Cargo.lock, uv.lock, poetry.lock
    "yarn.lock",
    "pnpm-lock.yaml",
    "*.min.js",
    "*.min.css",
    "dist/**",
    "build/**",
    "__pycache__/**",
    "*.pb.go",        # protobuf generated
    "*.generated.*",
]
```

Users can extend or override the list in config:

```json
{
  "diff": {
    "exclude_patterns": ["docs/generated/**", "vendor/**"]
  }
}
```

The implementation parses `diff --git a/<path> b/<path>` headers and drops entire
file hunks whose path matches any pattern (using `fnmatch`).

## Why it is a good improvement

Lock file changes dominate most diffs but carry zero semantic information for the commit
message. Filtering them reduces token usage by 30–90% on typical dependency-update commits
and dramatically improves message quality.

## Possible downsides

- Over-aggressive defaults could hide intentional generated-file changes. The config
  override addresses this.
- Parsing unified diff format has edge cases (binary files, rename hunks).
