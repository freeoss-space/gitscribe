# gitscribe — Improvement Ideas

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

---

### Idea 1 — Stream AI responses token-by-token

**What it is**

Instead of waiting for the full response from the API, use HTTP Server-Sent Events (SSE)
streaming so that each token appears in the terminal as soon as the model produces it.
The `AiBackend.generate` interface gains a `stream()` async-generator sibling (or an
optional `streaming: bool` parameter). The `ApiBackend` switches the request to
`"stream": true` and yields each chunk as it arrives. The UI shows an animated live-render
panel that updates in place using `rich.live.Live`.

```python
# ai_backend.py — ApiBackend addition
async def stream(self, prompt: str) -> AsyncIterator[str]:
    async with aiohttp.ClientSession(timeout=...) as session:
        async with session.post(
            f"{self._config.url}/chat/completions",
            headers={...},
            json={"model": self._config.model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": self._config.temperature,
                  "stream": True},
        ) as response:
            response.raise_for_status()
            async for line in response.content:
                text = line.decode().strip()
                if text.startswith("data: ") and text != "data: [DONE]":
                    data = json.loads(text[6:])
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
```

```python
# commit_command.py — use Live panel
from rich.live import Live
async def _stream_generate(self, prompt: str) -> str:
    buffer = ""
    with Live(console=self._console, refresh_per_second=15) as live:
        async for chunk in self._ai.stream(prompt):
            buffer += chunk
            live.update(Panel(buffer, title="Generating..."))
    return buffer
```

The `CliBackend` does not stream (process stdout is line-buffered anyway) and
falls back to the current blocking approach.

**Why it is a good improvement**

The current UX shows a spinner that can sit for 10-30 seconds with no feedback.
Streaming reduces *perceived* latency to near-zero and lets the user abort early if
the direction is clearly wrong.

**Possible downsides**

- Some self-hosted or proxy API endpoints do not correctly implement SSE; needs a
  graceful fallback.
- Adds modest complexity to the `AiBackend` interface.
- `CliBackend` does not benefit.

**Confidence: 88%**

---

### Idea 2 — Diff size limiting and chunking

**What it is**

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

**Why it is a good improvement**

Large diffs (e.g., adding a new library) silently cause API errors or nonsense output.
This makes failures visible and predictable.

**Possible downsides**

- Truncation loses context; the commit message may miss some changes.
- The "right" limit varies by model; should be configurable.

**Confidence: 92%**

---

### Idea 3 — `gitscribe amend` command

**What it is**

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

**Why it is a good improvement**

"Oops, my commit message was auto-generated garbage" is a common situation.
A dedicated `amend` command handles the full regenerate-review-amend cycle, which
currently requires manual `git commit --amend` and re-typing.

**Possible downsides**

- Must check that HEAD exists (not an empty repo).
- Amending pushed commits is dangerous; the tool should warn if the commit has been
  pushed (`git log --oneline origin/HEAD..HEAD` is empty).

**Confidence: 85%**

---

### Idea 5 — `gitscribe hooks install` command

**What it is**

A new subcommand that installs a `prepare-commit-msg` git hook in the current
repository. The hook calls `gitscribe commit --output-only` and writes the result
into the commit message file that git passes as `$1`. The user still gets the normal
git editor to review/edit before the commit lands.

```bash
#!/usr/bin/env bash
# .git/hooks/prepare-commit-msg (generated by gitscribe hooks install)
SOURCE="$2"
if [ -z "$SOURCE" ] || [ "$SOURCE" = "message" ]; then
    gitscribe commit --output-only > "$1" 2>/dev/null || true
fi
```

The `hooks` command group:

```python
hooks_app = typer.Typer(name="hooks")
app.add_typer(hooks_app)

@hooks_app.command(name="install")
def hooks_install():
    """Install gitscribe prepare-commit-msg hook in the current repo."""
    ...

@hooks_app.command(name="uninstall")
def hooks_uninstall():
    """Remove the gitscribe hook from the current repo."""
    ...
```

**Why it is a good improvement**

Reduces the workflow to zero extra steps: just `git commit` and the message is
pre-filled by AI, ready for the user to review in their editor. This is the
highest-leverage DX improvement possible.

**Possible downsides**

- Hooks are local to the clone; team members must each run `gitscribe hooks install`.
- If the AI backend is slow, it delays `git commit` noticeably.
- Requires detecting the git repo root; fails outside a git repo.

**Confidence: 87%**

---

### Idea 7 — Custom prompt templates in config

**What it is**

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

**Why it is a good improvement**

Different teams have wildly different commit-message conventions. A finance team may
want ticket IDs prepended; an open-source project may want DCO sign-offs mentioned.
Custom templates make gitscribe adaptable without code changes.

**Possible downsides**

- Bad templates (missing placeholders, syntax errors) produce confusing AI output.
- Needs basic template validation on load (check `str.format_map` with dummy values).

**Confidence: 82%**

---

### Idea 8 — `gitscribe config show`

**What it is**

A subcommand of `config` (or a standalone command `gitscribe config show`) that
pretty-prints the resolved config as JSON to stdout, with sensitive fields (API token)
redacted.

```python
@config_app.command(name="show")
def config_show():
    config_mgr = ConfigManager()
    config = config_mgr.load()
    data = config_mgr._serialize_config(config)
    # redact token
    data.setdefault("ai", {}).setdefault("api", {})["token"] = "***" if data["ai"]["api"]["token"] else ""
    typer.echo(json.dumps(data, indent=2))
```

**Why it is a good improvement**

Debugging "why is gitscribe using model X?" is currently only possible by opening the
config file manually. `config show` is scriptable, CI-friendly, and surfaces the
platform-merged effective config (not just the raw file).

**Possible downsides**

- Minimal. The only risk is accidentally printing a real token if the redaction logic
  has a bug; use an allowlist approach instead.

**Confidence: 90%**

---

### Idea 9 — Filter lockfiles and generated files from the diff

**What it is**

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

**Why it is a good improvement**

Lock file changes dominate most diffs but carry zero semantic information for the commit
message. Filtering them reduces token usage by 30–90% on typical dependency-update commits
and dramatically improves message quality.

**Possible downsides**

- Over-aggressive defaults could hide intentional generated-file changes. The config
  override addresses this.
- Parsing unified diff format has edge cases (binary files, rename hunks).

**Confidence: 93%**

---

### Idea 10 — Token count estimation and warning

**What it is**

Before calling the AI, compute a rough token estimate using the heuristic
`tokens ≈ len(text) / 4` (widely accepted for English-heavy code). If the estimate
exceeds a configurable threshold (default: `8000` tokens), print a warning and offer
the user a chance to abort or truncate.

```python
# In CommitCommand.run / PrCommand.run
APPROX_TOKEN_WARNING = 8_000

estimated_tokens = len(prompt.encode()) // 4
if estimated_tokens > APPROX_TOKEN_WARNING:
    self._ui.show_warning(
        f"Estimated prompt size: ~{estimated_tokens:,} tokens. "
        "This may exceed your model's context window or cost more than expected."
    )
    if not self._ui.confirm("Continue anyway?"):
        return
```

**Why it is a good improvement**

Without this, large diffs cause silent API failures (HTTP 400 / context length exceeded)
with no guidance. The warning is non-blocking by default and requires zero new dependencies.

**Possible downsides**

- The heuristic is inaccurate for non-Latin code (CJK, Arabic); could be off by 2–3×.
- Adds an interactive pause that could be annoying for `--output-only` mode (should be
  skipped in that mode).

**Confidence: 80%**

---

### Idea 13 — `--dry-run` flag

**What it is**

A `--dry-run` flag on both `commit` and `pr` commands that prints the exact prompt
that *would* be sent to the AI backend and exits without making any API call.

```python
# cli.py — commit_cmd
@app.command(name="commit")
def commit_cmd(
    ...,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the AI prompt and exit")] = False,
):
    ...
    if dry_run:
        prompt = PromptBuilder.commit(diff=diff, style=resolved_style, ...)
        typer.echo(prompt)
        return
```

**Why it is a good improvement**

Prompt engineering and debugging are the most common pain points when gitscribe produces
bad output. `--dry-run` gives users full visibility into what the model receives, enabling
fast iteration on custom templates (Idea 7) and config tuning.

**Possible downsides**

- None significant. Purely additive.

**Confidence: 95%**

---

### Idea 14 — Configurable system prompt / persona for API backend

**What it is**

The OpenAI chat-completions API supports a `"system"` role message that sets the
model's persona and standing instructions. Expose this as `ai.api.system_prompt` in
config. The `ApiBackend` prepends it to the messages list:

```python
# models.py
@dataclass(frozen=True)
class ApiConfig:
    url: str = ""
    token: str = ""
    model: str = ""
    system_prompt: str = "You are an expert software engineer who writes clear, concise git commit messages."
    temperature: float = 0.7
```

```python
# ai_backend.py — ApiBackend.generate
messages = []
if self._config.system_prompt:
    messages.append({"role": "system", "content": self._config.system_prompt})
messages.append({"role": "user", "content": prompt})
```

**Why it is a good improvement**

A system prompt that sets a domain-specific persona (e.g., "You follow the Angular
commit convention strictly") consistently improves output quality compared to weaving
instructions into the user prompt. It is the standard recommended way to use chat models.

**Possible downsides**

- Some third-party API proxies ignore the `system` role; negligible downside since it
  falls back gracefully.
- Slightly increases prompt token count.

**Confidence: 84%**

---

### Idea 15 — Retry with exponential back-off

**What it is**

Wrap `ApiBackend.generate` in a retry loop with exponential back-off for transient
errors (HTTP 429, 500, 502, 503, 504) and `aiohttp.ClientError`. Use at most 3 retries
with jitter (0.5 s, 1 s, 2 s base delays).

```python
import asyncio, random

MAX_RETRIES = 3
BASE_DELAY = 0.5

async def generate(self, prompt: str) -> str:
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await self._do_generate(prompt)
        except aiohttp.ClientResponseError as exc:
            if exc.status not in (429, 500, 502, 503, 504) or attempt == MAX_RETRIES:
                raise
        except aiohttp.ClientError:
            if attempt == MAX_RETRIES:
                raise
        delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.3)
        await asyncio.sleep(delay)
    raise RuntimeError("unreachable")
```

**Why it is a good improvement**

Rate-limit (429) and gateway errors (502/503) are extremely common with public AI APIs.
Currently these cause a hard crash with an unformatted traceback. Retries make the tool
resilient without requiring user intervention.

**Possible downsides**

- Adds latency when real errors occur (up to ~3 s for 3 retries).
- Should respect `Retry-After` headers from 429 responses for well-behaved APIs.

**Confidence: 91%**

---

### Idea 16 — `gitscribe config validate`

**What it is**

A subcommand that loads and validates the config file, printing a human-readable
report of any problems found:

```
✅  ai.backend: "api" — valid
❌  ai.api.url: empty — API backend requires a URL (e.g., https://api.openai.com/v1)
❌  ai.api.token: empty — API backend requires a token
✅  commit.style: "professional" — valid
```

Validation checks:
- If `backend == "api"`: `url` and `token` must be non-empty; `url` must look like a URL.
- If `backend == "cli"`: `command` must be non-empty and the executable must be found
  via `shutil.which`.
- Enum fields (`style`, `format`, `body_length`) must be valid enum values.
- Theme colors must be valid Rich color names.

**Why it is a good improvement**

The most common support question for any CLI tool with a config file is "why isn't it
working?" This command turns silent misconfiguration into an actionable error list.

**Possible downsides**

- Validating Rich color names requires loading the Rich color database.
- Network reachability of the API URL is out of scope for `validate`.

**Confidence: 88%**

---

### Idea 17 — `gitscribe init` guided-setup wizard

**What it is**

A new top-level command that walks the user through configuring gitscribe for the first
time via interactive prompts, then writes the config file.

```
$ gitscribe init

Welcome to gitscribe!

? AI backend [api / cli]: api
? API URL (e.g. https://api.openai.com/v1): https://api.openai.com/v1
? API token: sk-...
? Model (e.g. gpt-4o-mini): gpt-4o-mini
? Default commit style [professional / fun / casual]: professional
? Default commit format [conventional / gitmoji / none]: conventional

✅ Config written to ~/.config/gitscribe/config.json
Run `gitscribe commit` to generate your first commit message!
```

Uses `typer.prompt` / `rich.prompt.Prompt` for each question with sensible defaults.
Runs `config validate` automatically at the end.

**Why it is a good improvement**

First-time setup is the highest-friction point for new users. A wizard eliminates
the need to understand the JSON schema, remember file paths, or read documentation.

**Possible downsides**

- Overwrites existing config (should check first and ask for confirmation).
- Interactive — not usable in CI/CD (but `config set` — Idea 25 — covers that case).

**Confidence: 86%**

---

### Idea 19 — Environment-variable overrides for config values

**What it is**

Allow every significant config value to be overridden via environment variables,
following the convention `GITSCRIBE_<SECTION>_<KEY>` (all upper-case, dots become
underscores):

| Env var | Config path |
|---|---|
| `GITSCRIBE_AI_BACKEND` | `ai.backend` |
| `GITSCRIBE_AI_API_URL` | `ai.api.url` |
| `GITSCRIBE_AI_API_TOKEN` | `ai.api.token` |
| `GITSCRIBE_AI_API_MODEL` | `ai.api.model` |
| `GITSCRIBE_COMMIT_STYLE` | `commit.style` |
| `GITSCRIBE_COMMIT_FORMAT` | `commit.format` |

The `ConfigManager.load()` method applies env-var overrides as a final layer on top of
the parsed file config (higher priority than any file-based setting):

```python
import os

def _apply_env_overrides(self, config: AppConfig) -> AppConfig:
    token = os.environ.get("GITSCRIBE_AI_API_TOKEN")
    if token:
        new_api = dataclasses.replace(config.ai.api, token=token)
        new_ai = dataclasses.replace(config.ai, api=new_api)
        config = dataclasses.replace(config, ai=new_ai)
    # ... repeat for other fields
    return config
```

**Why it is a good improvement**

This is table-stakes for any CLI tool used in CI/CD. It lets teams inject the API token
via secrets management (GitHub Actions `${{ secrets.OPENAI_TOKEN }}`) without storing
it in the config file.

**Possible downsides**

- Long list of env-var names to document and maintain.
- Precedence rules (env > project config > user config) must be clearly documented.

**Confidence: 92%**

---

### Idea 21 — Format options for the `pr` command

**What it is**

Add a `--format` / `-f` option to the `pr` command that mirrors the `commit` command's
`--format` flag, with values `markdown` (default), `conventional`, and `plain`.
Add a `pr.format` config field in `PrDefaults`.

`markdown` (current default): free-form markdown PR description.
`conventional`: title follows Conventional Commits; body uses bullet-point sections.
`plain`: no markdown formatting.

Update `PromptBuilder.pr` to pass format instructions the same way `PromptBuilder.commit`
does for `FORMAT_DESCRIPTIONS`.

**Why it is a good improvement**

Teams that use Conventional Commits for commit messages usually want PR titles to follow
the same convention (e.g., for automated changelog tools). The current PR command always
generates free-form markdown with no format guarantee.

**Possible downsides**

- Adds one more option to learn; docs must be updated.
- `conventional` and `markdown` formats can overlap; naming must be clear.

**Confidence: 78%**

---

### Idea 22 — Per-file diff stats table

**What it is**

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

**Why it is a good improvement**

When running on a multi-file diff, the current summary gives no indication of *which*
files changed or *how much*, making it hard to sanity-check that the right files were
staged. The table provides this at a glance.

**Possible downsides**

- Very large diffs produce very long tables; cap the display at 20 files with a
  "and N more..." row.

**Confidence: 85%**

---

### Idea 24 — Actionable error messages

**What it is**

Wrap every call that can fail (API calls, subprocess calls, config loading, clipboard)
with structured error handling that appends a suggested fix to the error message.
Implement a central `handle_error(exc)` utility in `cli.py`:

```python
ERROR_HINTS = {
    "api.token": "Set GITSCRIBE_AI_API_TOKEN or run `gitscribe config` to add your API key.",
    "connection": "Check your internet connection and API URL (`gitscribe config show`).",
    "not a git repository": "Run `gitscribe` from inside a git repository.",
    "no staged changes": "Stage files with `git add <files>` before running `gitscribe commit`.",
    "CalledProcessError": "A git command failed. Run `git status` to check the repository state.",
}
```

For `aiohttp.ClientResponseError` with status 401: display
`"API authentication failed — check your token with gitscribe config validate"`.
For status 429: display `"Rate limit hit — reduce request frequency or upgrade your API plan"`.

**Why it is a good improvement**

The current code lets most exceptions bubble up as raw Python tracebacks. New users see
`aiohttp.ClientConnectorError` and have no idea what to do. Actionable messages turn
confusion into a clear next step.

**Possible downsides**

- Must not suppress the original exception entirely (use `--verbose` / `--debug` flag to
  re-raise for debugging).

**Confidence: 90%**

---

### Idea 25 — `gitscribe config set <key> <value>`

**What it is**

A subcommand that sets a single config value by dotted-path key without opening the editor:

```
$ gitscribe config set ai.api.token sk-abc123
$ gitscribe config set commit.style fun
$ gitscribe config set ai.api.model gpt-4o
```

Implementation: parse the dotted key into a path, load config as a raw dict, apply the
value using `functools.reduce` to walk the nested dict, then serialize and write back.

```python
@config_app.command(name="set")
def config_set(key: str, value: str):
    config_mgr = ConfigManager()
    raw = config_mgr.load_raw()          # returns dict, not AppConfig
    parts = key.split(".")
    node = raw
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    config_mgr.save_raw(raw)
    typer.echo(f"Set {key} = {value}")
```

**Why it is a good improvement**

CI/CD onboarding scripts, dotfile managers, and setup playbooks all need a scriptable
way to configure gitscribe. Opening an editor in a script is impractical.

**Possible downsides**

- Setting an invalid value (e.g., `commit.style = typo`) fails silently until the
  next `gitscribe commit`; should call `validate` after each `set`.

**Confidence: 88%**

---

### Idea 26 — Project-level `.gitscribe.json` config

**What it is**

Walk up from the current working directory to the git repo root looking for a
`.gitscribe.json` file. If found, deep-merge it on top of the user config (project
config takes precedence for non-credential fields; credentials are always taken from
the user config).

```python
# config_manager.py
def load(self) -> AppConfig:
    user_data = self._load_file(self.config_path)
    project_data = self._load_project_config()
    merged = _deep_merge(user_data, project_data) if project_data else user_data
    return self._parse_config(merged)

def _load_project_config(self) -> dict | None:
    try:
        root = GitOperations().get_repo_root()
    except subprocess.CalledProcessError:
        return None
    path = root / ".gitscribe.json"
    if path.exists():
        return json.loads(path.read_text())
    return None
```

Sensitive fields (`ai.api.token`, `ai.api.url`) are ignored in project-level config to
prevent token leakage via committed config files. Document this clearly.

**Why it is a good improvement**

Teams can share a `.gitscribe.json` that enforces the project's commit convention (e.g.,
`conventional` format, `professional` style, custom prompt template) without each
developer manually configuring their user config.

**Possible downsides**

- Must never allow `token` in the project config (accidental secret commit).
- Precedence rules need clear documentation.

**Confidence: 87%**

---

### Idea 27 — Expose `temperature` and `max_tokens` in config

**What it is**

Add `temperature: float` (default: `0.7`) and `max_tokens: int` (default: `0`, meaning
"let the API decide") to `ApiConfig`. Pass them through to the request payload.

```python
# models.py
@dataclass(frozen=True)
class ApiConfig:
    url: str = ""
    token: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 0         # 0 = omit from request

# ai_backend.py
payload = {
    "model": self._config.model,
    "messages": messages,
    "temperature": self._config.temperature,
}
if self._config.max_tokens > 0:
    payload["max_tokens"] = self._config.max_tokens
```

**Why it is a good improvement**

`temperature` directly controls creativity vs. consistency. Users generating highly
structured `conventional` commit messages want low temperature (0.1–0.3); users
choosing the `fun` style want higher temperature (0.9+). `max_tokens` lets users cap
cost/latency for short commit messages.

**Possible downsides**

- Exposing raw model parameters may confuse novice users; good defaults mitigate this.

**Confidence: 83%**

---

### Idea 28 — Commit message title length validation

**What it is**

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

**Why it is a good improvement**

AI models frequently generate overly long commit titles, especially with the `long`
body length option. This check catches the problem before the user commits.

**Possible downsides**

- The 72-char limit doesn't apply equally to all projects; should be configurable.
- `gitmoji` format messages have slightly different length constraints due to the emoji.

**Confidence: 82%**

---

### Idea 29 — Structured output formats for `--output-only`

**What it is**

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

**Why it is a good improvement**

`--output-only` exists precisely for scripting/CI use. JSON output enables downstream
tools (GitHub Actions steps, custom hooks, PR bots) to consume title and body separately
without fragile string parsing.

**Possible downsides**

- Adds an option combination (`--output-only` + `--output-format`) that only makes
  sense together; should error if `--output-format` is used without `--output-only`.

**Confidence: 86%**

---

### Idea 30 — `--context` flag for extra prompt context

**What it is**

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

**Why it is a good improvement**

Diffs alone often lack context: a one-line change in a config file might be a critical
security fix or a trivial tweak. Attaching the ticket description or a brief intent
statement dramatically improves the generated message's relevance.

**Possible downsides**

- Users may paste sensitive internal information that gets sent to a third-party AI
  API; this is inherent to any AI-assisted tool.
- Increases prompt token count.

**Confidence: 88%**

---

## Summary Table

| # | Idea | Confidence |
|---|------|------------|
| 1 | Stream AI responses token-by-token | 88% |
| 2 | Diff size limiting and chunking | 92% |
| 3 | `gitscribe amend` command | 85% |
| 5 | `gitscribe hooks install` command | 87% |
| 7 | Custom prompt templates in config | 82% |
| 8 | `gitscribe config show` subcommand | 90% |
| 9 | Filter lockfiles and generated files | 93% |
| 10 | Token count estimation and warning | 80% |
| 13 | `--dry-run` flag | 95% |
| 14 | Configurable system prompt / persona | 84% |
| 15 | Retry with exponential back-off | 91% |
| 16 | `gitscribe config validate` | 88% |
| 17 | `gitscribe init` guided-setup wizard | 86% |
| 19 | Environment-variable overrides | 92% |
| 21 | Format options for `pr` command | 78% |
| 22 | Per-file diff stats table | 85% |
| 24 | Actionable error messages | 90% |
| 25 | `gitscribe config set <key> <value>` | 88% |
| 26 | Project-level `.gitscribe.json` config | 87% |
| 27 | Expose `temperature` and `max_tokens` | 83% |
| 28 | Commit title length validation | 82% |
| 29 | Structured output formats for `--output-only` | 86% |
| 30 | `--context` flag for extra prompt context | 88% |
