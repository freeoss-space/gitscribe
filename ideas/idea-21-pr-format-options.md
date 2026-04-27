# Idea 21 — Format options for the `pr` command

**Confidence: 78%**

## What it is

Add a `--format` / `-f` option to the `pr` command that mirrors the `commit` command's
`--format` flag, with values `markdown` (default), `conventional`, and `plain`.
Add a `pr.format` config field in `PrDefaults`.

`markdown` (current default): free-form markdown PR description.
`conventional`: title follows Conventional Commits; body uses bullet-point sections.
`plain`: no markdown formatting.

Update `PromptBuilder.pr` to pass format instructions the same way `PromptBuilder.commit`
does for `FORMAT_DESCRIPTIONS`.

## Why it is a good improvement

Teams that use Conventional Commits for commit messages usually want PR titles to follow
the same convention (e.g., for automated changelog tools). The current PR command always
generates free-form markdown with no format guarantee.

## Possible downsides

- Adds one more option to learn; docs must be updated.
- `conventional` and `markdown` formats can overlap; naming must be clear.
