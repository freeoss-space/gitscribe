# gitscribe — Improvement Ideas

> Each passing idea has a dedicated file in the [`ideas/`](ideas/) directory.

## Step 1 — Raw List of 30 Ideas

1. Stream AI responses token-by-token so the user sees output arriving in real time.
2. Limit / chunk large diffs before sending to the AI to avoid silent token-limit failures.
3. Add a `gitscribe amend` command to regenerate the last commit's message.
4. Add a `gitscribe tag` command to generate annotated tag messages.
5. Add a `gitscribe hooks install` command to set up `prepare-commit-msg` hooks.
6. Race multiple AI backends in parallel and use whichever responds first.
7. Allow custom prompt templates in config so users can tune AI instructions.
8. Add a `gitscribe config show` subcommand to print current config without opening the editor.
9. Filter lockfiles and generated files out of the diff before sending to the AI.
10. Estimate token count and warn when a diff is likely to exceed the model's context window.
11. Keep a local history/log of all previously generated messages.
12. Add a `gitscribe completions` command (shell tab-completion for bash/zsh/fish).
13. Add a `--dry-run` flag that prints the prompt that *would* be sent to the AI.
14. Add a configurable system-prompt / persona field for API backends.
15. Retry API calls with exponential back-off on transient network/rate-limit errors.
16. Add a `gitscribe config validate` subcommand to check config correctness.
17. Add a `gitscribe init` guided-setup wizard for first-time configuration.
18. Support named config profiles (e.g., `work`, `personal`).
19. Support environment-variable overrides for every config value.
20. Add a `gitscribe changelog` command to draft changelog entries from recent commits.
21. Add format options to the `pr` command to match the `commit` command's `--format` flag.
22. Show a per-file diff stats table (file path, additions, deletions) before generation.
23. Replace `asyncio.run` with proper async scaffolding and Ctrl-C cancellation.
24. Surface actionable error messages that tell the user exactly how to fix the problem.
25. Add a `gitscribe config set <key> <value>` subcommand for scripted config edits.
26. Support a project-level `.gitscribe.json` config file that overrides the user config.
27. Expose `temperature` and `max_tokens` as configurable API options.
28. Validate commit message title length post-generation and warn if it exceeds 72 chars.
29. Add a JSON / Markdown / plain output-format option for `--output-only` pipeline use.
30. Add a `--context` flag to attach extra context (ticket ID, notes) to the prompt.

---

## Step 2 — Critical Evaluation

| # | Verdict | Reason |
|---|---------|--------|
| 1 | ✅ Keep | Real UX improvement; aiohttp already supports SSE streaming. |
| 2 | ✅ Keep | Prevents silent, confusing failures on large repos. |
| 3 | ✅ Keep | Common workflow; one extra subcommand with minimal new code. |
| 4 | ❌ Reject | Niche; annotated tags are rarely long-form prose. |
| 5 | ✅ Keep | Deepens git integration; high discoverability for teams. |
| 6 | ❌ Reject | Over-engineered; adds cost and complexity for marginal gain. |
| 7 | ✅ Keep | High power-user value; config already supports per-command overrides. |
| 8 | ✅ Keep | Useful for debugging and scripting; trivial to implement. |
| 9 | ✅ Keep | Cuts noise and token waste; improves generated message quality. |
| 10 | ✅ Keep | A rough heuristic (chars ÷ 4) is enough for a useful warning. |
| 11 | ❌ Reject | Adds local I/O complexity and privacy concerns for modest benefit. |
| 12 | ❌ Reject | Typer provides `--install-completion` out of the box; already covered. |
| 13 | ✅ Keep | Invaluable debug tool; one flag, zero new dependencies. |
| 14 | ✅ Keep | Separating system instructions from user content improves output quality. |
| 15 | ✅ Keep | Essential robustness; transient 429/5xx errors are common with AI APIs. |
| 16 | ✅ Keep | Reduces support questions; fast to implement with clear user benefit. |
| 17 | ✅ Keep | First-time onboarding is the biggest friction point for new users. |
| 18 | ❌ Reject | Platform overrides in config already cover the main use case. |
| 19 | ✅ Keep | Critical for CI/CD; keeps secrets out of config files. |
| 20 | ❌ Reject | Changelog generation is a distinct tool domain; out of scope. |
| 21 | ✅ Keep | Parity with the `commit` command; low effort, high consistency. |
| 22 | ✅ Keep | Much more informative than the current single-line "+N -N" count. |
| 23 | ❌ Reject | `asyncio.run` is fine here; Ctrl-C already works at OS level. |
| 24 | ✅ Keep | Dramatically reduces confusion for misconfigured users. |
| 25 | ✅ Keep | Enables CI/CD scripted onboarding; small implementation surface. |
| 26 | ✅ Keep | Lets teams share a repo-level config; mirrors many popular CLI tools. |
| 27 | ✅ Keep | Direct impact on output quality/cost; two fields in `ApiConfig`. |
| 28 | ✅ Keep | Simple validation that catches a common AI output quirk. |
| 29 | ✅ Keep | Makes `--output-only` usable in shell pipelines (e.g., JSON for CI). |
| 30 | ✅ Keep | Zero-friction way to attach ticket IDs / PR context to the prompt. |

**22 ideas passed.**

---

## Step 3 — Detailed Plans for Each Passing Idea

Each passing idea has its own file in the [`ideas/`](ideas/) directory.

| # | Idea | File | Confidence |
|---|------|------|------------|
| 1 | Stream AI responses token-by-token | [idea-01-stream-ai-responses.md](ideas/idea-01-stream-ai-responses.md) | 88% |
| 2 | Diff size limiting and chunking | [idea-02-diff-size-limiting.md](ideas/idea-02-diff-size-limiting.md) | 92% |
| 3 | `gitscribe amend` command | [idea-03-amend-command.md](ideas/idea-03-amend-command.md) | 85% |
| 5 | `gitscribe hooks install` command | [idea-05-hooks-install.md](ideas/idea-05-hooks-install.md) | 87% |
| 7 | Custom prompt templates in config | [idea-07-custom-prompt-templates.md](ideas/idea-07-custom-prompt-templates.md) | 82% |
| 8 | `gitscribe config show` subcommand | [idea-08-config-show.md](ideas/idea-08-config-show.md) | 90% |
| 9 | Filter lockfiles and generated files | [idea-09-filter-lockfiles.md](ideas/idea-09-filter-lockfiles.md) | 93% |
| 10 | Token count estimation and warning | [idea-10-token-count-warning.md](ideas/idea-10-token-count-warning.md) | 80% |
| 13 | `--dry-run` flag | [idea-13-dry-run-flag.md](ideas/idea-13-dry-run-flag.md) | 95% |
| 14 | Configurable system prompt / persona | [idea-14-system-prompt.md](ideas/idea-14-system-prompt.md) | 84% |
| 15 | Retry with exponential back-off | [idea-15-retry-backoff.md](ideas/idea-15-retry-backoff.md) | 91% |
| 16 | `gitscribe config validate` | [idea-16-config-validate.md](ideas/idea-16-config-validate.md) | 88% |
| 17 | `gitscribe init` guided-setup wizard | [idea-17-init-wizard.md](ideas/idea-17-init-wizard.md) | 86% |
| 19 | Environment-variable overrides | [idea-19-env-overrides.md](ideas/idea-19-env-overrides.md) | 92% |
| 21 | Format options for `pr` command | [idea-21-pr-format-options.md](ideas/idea-21-pr-format-options.md) | 78% |
| 22 | Per-file diff stats table | [idea-22-per-file-diff-stats.md](ideas/idea-22-per-file-diff-stats.md) | 85% |
| 24 | Actionable error messages | [idea-24-actionable-errors.md](ideas/idea-24-actionable-errors.md) | 90% |
| 25 | `gitscribe config set <key> <value>` | [idea-25-config-set.md](ideas/idea-25-config-set.md) | 88% |
| 26 | Project-level `.gitscribe.json` config | [idea-26-project-level-config.md](ideas/idea-26-project-level-config.md) | 87% |
| 27 | Expose `temperature` and `max_tokens` | [idea-27-temperature-max-tokens.md](ideas/idea-27-temperature-max-tokens.md) | 83% |
| 28 | Commit title length validation | [idea-28-title-length-validation.md](ideas/idea-28-title-length-validation.md) | 82% |
| 29 | Structured output formats for `--output-only` | [idea-29-structured-output.md](ideas/idea-29-structured-output.md) | 86% |
| 30 | `--context` flag for extra prompt context | [idea-30-context-flag.md](ideas/idea-30-context-flag.md) | 88% |
