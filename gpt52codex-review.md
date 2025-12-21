• High Severity

  - Dialogue sessions are effectively blocked for Anthropic and for short chapters: DialogueScreen requires a cache to proceed, but only GeminiProvider
    implements caching and it deliberately returns None for small text (so _fetch_response errors with “Cache required”), leaving no fallback path to embed
    content directly (reader/screens/dialogue.py:211, reader/screens/dialogue.py:360, reader/llm.py:54).
  - knos read test always fails because provider.chat returns a ChatResponse but the code calls .strip() on it instead of response.text (knos/commands/
    read.py:103).

  Medium Severity

  - Card generation can crash after a successful LLM call when run outside the repo root: drafts_dir.relative_to(Path.cwd()) raises ValueError,
    interrupting the UI even though drafts were written (reader/screens/generate_cards.py:175).
  - CLI path resolution is brittle: relative solution paths are resolved under knos/reviewer/ instead of the repo root or CWD, so typical invocations like
    solutions/... fail when run from the repo (knos/reviewer/reviewer.py:480).
  - History logging is written inside the package directory (knos/reviewer/history.jsonl), which will be read‑only in installed environments and blurs the
    engine/content boundary (knos/reviewer/core.py:21, knos/reviewer/core.py:375).

  Low Severity

  Architecture & Organization Improvements

  - Split knos/reviewer/core.py into focused modules (parsing, schedule/state, progress/reporting, dashboard data); it’s currently a god‑module that
    couples unrelated concerns.
  - Centralize path resolution (e.g., a knos.paths module or env‑based root) instead of deriving REPO_ROOT from __file__, which breaks if the package is
    installed or invoked outside the repo.
  - Clarify package layout: either move reader under knos/ or explicitly treat it as a separate package with documented boundaries; update docs that still
    refer to reviewer/ and tui/ as top‑level modules.
  - Make heavy dependencies optional via extras (e.g., knos[reader], knos[voice]) and gate imports to keep the core lightweight.
  - Add a small test suite for parse_markdown, scheduling transitions, due‑queue ordering, and YAML/config parsing to catch regressions as the project
    grows.

  Open Questions

  - Should Reader operate without caching by embedding chapter content into the system/user prompt when caching is unavailable (Anthropic or small
    chapters), or is caching a hard requirement?
  - What should be the canonical base for relative paths in CLI (cwd, repo root, or a config flag)?

  No code changes made. Tests not run.

  If you want, I can follow up with fixes for the top issues. Suggested next steps:

  1. Patch Reader to support non‑cached flow + fix knos read test.
  2. Normalize path handling for history, schedule, and solution paths.
  3. Draft a refactor plan to split knos/reviewer/core.py and add tests.
