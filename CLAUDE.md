# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Knowledge Operating System: spaced-repetition drilling + LLM-powered reading companion for self-study. Two core systems:

- **Reviewer**: Leitner-box spaced repetition. Cards are markdown files with fenced code blocks revealed line-by-line. 100% accuracy advances the box; any failure resets to box 0.
- **Reader**: LLM-powered reading companion modeled on St. John's College (Annapolis/Santa Fe) seminars—the LLM acts as a tutor and fellow inquirer, not a lecturer.

## Commands

```bash
# Primary interfaces
uv run knos              # TUI dashboard (default)
uv run knos drill        # Drill due cards TUI
uv run knos read         # Reading companion TUI
uv run knos today        # CLI daily orientation
uv run knos progress     # Generate PROGRESS.md

# Reader subcommands
uv run knos read list              # List registered materials
uv run knos read clear <id> [ch]   # Clear session data
uv run knos read test              # Verify LLM configuration

# Reviewer query modes (for scripting)
uv run python3 -m knos.reviewer.reviewer --due          # Due cards list
uv run python3 -m knos.reviewer.reviewer --due-json     # JSON for scripts
uv run python3 -m knos.reviewer.reviewer --summary      # Mastery status
```

## Architecture

```
knos/                     # Unified package
├── cli.py                # Typer CLI entry point (knos command)
├── commands/             # CLI command implementations
│   └── today.py, study.py, drill.py, read.py, progress.py
├── reviewer/
│   ├── core.py           # Business logic: parsing, Leitner scheduling, state
│   └── reviewer.py       # Query-only CLI (--due, --due-json, --summary)
├── tui/
│   ├── app.py            # Textual app entry points
│   ├── screens/          # TUI screens: dashboard, drill, drill_queue, browse
│   └── widgets/          # Reusable TUI components
└── reader/               # LLM reading companion
    ├── llm.py            # LLM provider (Gemini)
    ├── content.py        # PDF/EPUB extraction, chapter/article loading
    ├── prompts.py        # Jinja2 prompt template loader
    ├── session.py        # Dialogue session state
    ├── types.py          # Shared type definitions (ContentId)
    ├── cuda_utils.py     # CUDA detection and library preloading
    ├── voice.py          # Voice input (faster-whisper)
    ├── tts.py            # Text-to-speech (Kokoro)
    ├── screens/          # Reader TUI screens
    ├── prompts/          # Dialogue mode prompts (base.md, socratic.md, etc.)
    ├── classics/         # Bundled classics (Aristotle, Cervantes, Dostoevsky)
    └── articles/         # Bundled articles (single-unit PDFs, no chapters)

solutions/                # Drill cards (user content, gitignored)
├── focus/                # Active cards for drilling
└── examples/             # Sample cards demonstrating format

plan/                     # Study configuration (gitignored except examples)
├── schedule.json         # Leitner box state
├── study_config.yaml     # Domain rotation, phases, priority shifts
└── todo.md               # Sprint tasks
```

### Key Design Patterns

- **Filesystem as database**: All state in markdown + JSON. No external services.
- **Separation of content and engine**: Engine (`knos/`) is versioned; content (`solutions/`, `plan/` state) is gitignored.
- **Leitner intervals**: Box 0=1hr, Box 1=4hr, Box 2+=1d→3d→7d→14d→30d

### Core Data Flow

1. `core.py` parses markdown files, extracts fenced code blocks as drill targets
2. Blocks preceded by `<!-- INFO -->` (within 50 chars) are excluded from drilling
3. `schedule.json` tracks box level and next_due datetime per card
4. Perfect score advances box; imperfect resets to box 0
5. `history.jsonl` logs all session results

## Card Format

Cards are markdown in `solutions/`. Every fenced code block is a drill target unless preceded by `<!-- INFO -->`.

```markdown
# Topic Name

## How It Works
Context visible during practice.

## Implementation
```python
def algorithm():
    pass
```
```

**Rules:**
- Every fenced block is a target (unless prefixed with `<!-- INFO -->`)
- No trailing blank lines inside code blocks
- One concept per file (2-15 lines per block)

## Configuration Files

| File | Purpose |
|------|---------|
| `plan/study_config.yaml` | Domain rotation, current phase, priority shifts |
| `plan/schedule.json` | Leitner box state (auto-managed) |
| `knos/reader/config.yaml` | LLM API keys and model selection |
| `knos/reader/content_registry.yaml` | PDF/EPUB/article registration (classics in `knos/reader/classics/`, articles in `knos/reader/articles/`) |

Copy `.example` versions to get started.

## Dependencies

Uses `uv` for package management:
```bash
uv sync              # Install core dependencies
uv sync --extra voice  # Include voice input/TTS (requires PyTorch)
uv run knos          # Run with dependencies
```

Core: `textual`, `rich`, `typer`, `google-genai`, `pymupdf`, `ebooklib`
Voice (optional): `faster-whisper`, `kokoro`, `sounddevice`, `torch`

Note: Voice features require PyTorch which only supports Linux, macOS ARM64, and Windows.

## Development Notes

- Engine code tracked in git: `knos/` (includes `knos/reader/classics/`, `knos/reader/articles/`)
- User content gitignored: `solutions/`, `plan/` state files, `knos/reader/sources/`
- The CLI entry point is `knos/cli.py` → `knos.cli:main`
- TUI built on Textual; CLI tools use Rich
