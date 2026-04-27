# Idea 3 — `gitscribe amend` command

**Confidence: 85%**

## What it is

A new top-level command that generates a commit message for the *current HEAD commit*
and runs `git commit --amend` with it. The diff source is `git diff HEAD~1..HEAD`
(or `git show HEAD` for the initial commit).

```python
@app.command(name="amend", help="Regenerate the last commit message.")
def amend_cmd(style, fmt, body_length, output_only):
    ...
    diff = deps.git_ops.get_last_commit_diff()
    ...
    # after user accepts: git_ops.amend(message)
```

```python
# git_operations.py
def get_last_commit_diff(self) -> str:
    result = subprocess.run(
        ["git", "show", "--format=", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout

def amend(self, message: str) -> None:
    subprocess.run(
        ["git", "commit", "--amend", "-m", message],
        check=True,
    )
```

The interaction loop is identical to `CommitCommand` except the final action runs
`amend` instead of `commit`. The current staged index is preserved.

## Why it is a good improvement

"Oops, my commit message was auto-generated garbage" is a common situation.
A dedicated `amend` command handles the full regenerate-review-amend cycle, which
currently requires manual `git commit --amend` and re-typing.

## Possible downsides

- Must check that HEAD exists (not an empty repo).
- Amending pushed commits is dangerous; the tool should warn if the commit has been
  pushed (`git log --oneline origin/HEAD..HEAD` is empty).
