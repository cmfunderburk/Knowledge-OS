# AGENTS.md

Context for AI coding assistants working in this repository.

## What This Is

A **Knowledge Operating System**: a unified engine for acquiring, encoding, and retaining deep understanding through spaced repetition and active recall.

The atomic unit is the **drill target**: a fenced code block revealed line-by-line during practice. Content is not limited to code—proof templates, tactic sequences, logical laws, formal definitions are all valid drill targets. The Leitner-box scheduler surfaces cards at optimal intervals (1hr → 4hr → 1d → 3d → 7d → 14d → 30d).

## Core Principles

- **Single Source of Truth**: All state lives in the filesystem. Markdown files are the database. `plan/schedule.json` is scheduler state. `history.jsonl` is the audit log. No external services.
- **Separation of Content and Engine**: Engine (Python) is versioned in git. Content (solutions, schedules) is user-specific and gitignored.
- **Strict Spaced Repetition**: 100% accuracy advances the box; any failure resets to box 0. This ensures consolidation at the "tip of the tongue" state.
- **Atomic Cards**: One concept per file. Small drill targets (2-15 lines per block). The 100%-or-reset rule demands granularity.
- **Proactive System**: The TUI tells you what to do next—what's due, overdue, struggling.

## Commands

```bash
# Primary interfaces (unified CLI)
uv run knos              # TUI dashboard (default)
uv run knos drill        # Drill due cards TUI
uv run knos read         # Reading companion TUI (St. John's-style dialogue)
uv run knos today        # CLI daily orientation
uv run knos progress     # Generate PROGRESS.md

# Reader CLI
uv run knos read list              # List registered materials
uv run knos read clear <id> [ch]   # Clear session data
uv run knos read test              # Verify LLM configuration

# Reviewer query modes (for scripting)
uv run python3 -m knos.reviewer.reviewer --due          # Show due cards
uv run python3 -m knos.reviewer.reviewer --due-json     # JSON for scripts
uv run python3 -m knos.reviewer.reviewer --summary      # Mastery status
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     TUI (knos)                          │
│              Dashboard · Drill · Browse                 │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Core Library                          │
│       knos/reviewer/core.py — shared data layer         │
│    (scheduling, parsing, history, state management)     │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    Filesystem                           │
│   solutions/              history.jsonl                 │
│   plan/                   (schedule, config, todo)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  Reader (knos read)                     │
│    St. John's-style seminar dialogue with LLM tutor     │
├─────────────────────────────────────────────────────────┤
│  reader/llm.py      — LLM provider (Gemini)             │
│  reader/content.py  — PDF/EPUB extraction, chapters     │
│  reader/prompts.py  — Jinja2 prompt templates           │
├─────────────────────────────────────────────────────────┤
│  reader/classics/   — Bundled classics (Project Guten.) │
│  reader/sources/    — User-provided PDFs/EPUBs          │
│  reader/content_registry.yaml — Material definitions    │
└─────────────────────────────────────────────────────────┘
```

**Key files:**
- `knos/cli.py` — Typer CLI entry point
- `knos/reviewer/core.py` — Business logic: parsing, Leitner scheduling, progress tracking
- `knos/reviewer/reviewer.py` — Legacy CLI interface for drilling
- `knos/tui/app.py` — Textual app entry points (StudyApp, DrillApp, ReaderApp)
- `knos/tui/screens/` — TUI screens: dashboard.py, drill.py, drill_queue.py, browse.py
- `reader/screens/` — Reader TUI: select_material.py, select_chapter.py, dialogue.py
- `reader/prompts/` — Dialogue mode prompts: base.md, socratic.md, clarify.md, challenge.md
- `reader/classics/` — Bundled classics (Aristotle, Cervantes, Dostoevsky)

## Card Format

Cards are Markdown files in `solutions/`. Every fenced code block is a **drill target** unless preceded by `<!-- INFO -->` within 50 chars.

**Template:**
```markdown
# Topic Name

**Time:** O(?) | **Space:** O(?)

## How It Works

Context visible during practice.

## Implementation

```python
def algorithm():
    pass
```
```

**Rules:**
- Every fenced code block is a target (unless prefixed with `<!-- INFO -->`)
- Prefix with `<!-- INFO -->` for non-practice blocks (example output, usage)
- No trailing blank lines inside code blocks
- One concept per file (split variants into separate files)

See `solutions/examples/` for sample cards.

## Configuration

### Study Schedule (`plan/study_config.yaml`)

Configure domain rotation, phases, and priority shifts:

```yaml
domains:
  0: "Math"           # Monday
  1: "CS"             # Tuesday
  # ... etc

current_phase:
  name: "Phase 0"
  description: "Foundations"

priority_shift:
  enabled: false
  name: "Focus Sprint"
```

Copy `plan/study_config.yaml.example` to get started.

### Reader Materials (`reader/content_registry.yaml`)

Register PDFs/EPUBs for the reading companion. Three classics from Project Gutenberg are bundled in `reader/classics/` and work out of the box:

- Nicomachean Ethics (Aristotle)
- Don Quixote (Cervantes)
- The Brothers Karamazov (Dostoevsky)

```yaml
materials:
  # PDF with chapter page ranges
  my-textbook:
    title: "Introduction to X"
    author: "Author Name"
    source: "path/to/textbook.pdf"
    structure:
      type: "chapters"
      chapters:
        - { num: 1, title: "Chapter One", pages: [10, 30] }

  # EPUB (structure extracted automatically)
  nicomachean-ethics:
    title: "Nicomachean Ethics"
    author: "Aristotle"
    source: "reader/classics/nicomachean-ethics.epub"
```

Copy `reader/content_registry.yaml.example` to get started.

### LLM Configuration (`reader/config.yaml`)

Configure API keys for the reading companion:

```yaml
llm:
  provider: "gemini"
  gemini:
    api_key: "your-api-key"
    model: "gemini-2.5-flash"
```

Copy `reader/config.yaml.example` to get started.

## Dependencies

Uses `uv` for package management:

```bash
uv sync              # Install dependencies
uv run knos          # Run with dependencies
```

Key dependencies: `textual`, `rich`, `typer`, `google-genai`, `pymupdf`, `ebooklib`, `jinja2`, `pyyaml`.

## Design Constraints

- **Python + Textual**: TUI built on Textual. CLI tools use Rich. No web stack.
- **Filesystem as database**: No SQLite, no external services. Markdown + JSON + JSONL.
- **Offline-first**: Core drill system works without network. Reader module requires LLM API access.

## Development Practices

- Read existing files before proposing changes
- Prefer editing existing files to creating new ones
- Use `uv` for dependency management (`uv sync`, `uv run`)
- **Engine code:** Tracked in git (`reviewer/`, `tui/`, `reader/*.py`)
- **User content:** Gitignored (`solutions/`, `plan/` state files)

## Debugging Tips

**No solutions found:**
- Ensure `.md` files exist in `solutions/`
- Check file permissions
- Verify script paths point to repo root

**Schedule not updating:**
- Check `plan/schedule.json` for syntax errors
- Verify perfect score (100%) for box advancement
- Run `uv run python3 -m reviewer.reviewer --summary`

**Scoring issues:**
- Ensure trailing blank lines are stripped from code blocks
- Use `<!-- INFO -->` for non-target blocks
- Verify all fenced blocks are properly closed

---

*For Claude Code: This file provides context for working with this codebase. Focus on practical, rigorous development.*
