# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Knowledge Operating System: spaced-repetition drilling + LLM-powered reading companion for self-study. Two core systems:

- **Reviewer**: Leitner-box spaced repetition. Cards are markdown files with fenced code blocks revealed line-by-line. 100% accuracy advances the box; any failure resets to box 0.
- **Reader**: LLM-powered reading companion modeled on St. John's College (Annapolis/Santa Fe) seminars—the LLM acts as a tutor and fellow inquirer, not a lecturer. Includes dialogue modes (Socratic, Clarify, Challenge, Teach, Technical), plus study tools (Quiz for recall testing, Review for cross-chapter synthesis).

## Commands

```bash
# Setup
uv run knos init         # Initialize config files (interactive)

# Primary interfaces
uv run knos              # TUI dashboard (default)
uv run knos drill        # Drill due cards TUI
uv run knos read         # Reading companion TUI
uv run knos today        # CLI daily orientation
uv run knos progress     # Generate PROGRESS.md

# Reader subcommands
uv run knos read list              # List registered materials
uv run knos read list --json       # List as JSON (for scripting/agents)
uv run knos read info <id>         # Show material details + chapters
uv run knos read info <id> --json  # Material info as JSON
uv run knos read clear <id> [ch]   # Clear session data
uv run knos read export <id> [ch]  # Export session to markdown
uv run knos read test              # Verify LLM configuration

# Reviewer query modes (for scripting)
uv run python3 -m knos.reviewer.reviewer --due          # Due cards list
uv run python3 -m knos.reviewer.reviewer --due-json     # JSON for scripts
uv run python3 -m knos.reviewer.reviewer --summary      # Mastery status
```

## Architecture

```
config/                   # User configuration (gitignored except .example)
├── study.yaml            # Domain rotation, phases, priority shifts
├── reader.yaml           # LLM API keys, voice/TTS settings
└── content.yaml          # PDF/EPUB/article registration

knos/                     # Unified package
├── cli.py                # Typer CLI entry point (knos command)
├── commands/             # CLI command implementations
│   └── today.py, study.py, drill.py, read.py, progress.py, init.py
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
    ├── session.py        # Dialogue session state (regular, quiz, review)
    ├── types.py          # Shared type definitions (ContentId)
    ├── cuda_utils.py     # CUDA detection and library preloading
    ├── voice.py          # Voice input (faster-whisper)
    ├── tts.py            # Text-to-speech (Kokoro)
    ├── screens/          # Reader TUI screens
    ├── prompts/          # Dialogue mode prompts (base.md, socratic.md, quiz.md, review.md, etc.)
    ├── sessions/         # Dialogue transcripts (gitignored, per-material subdirs)
    ├── classics/         # Bundled classics (Aristotle, Cervantes, Dostoevsky)
    └── articles/         # Bundled articles (single-unit PDFs, no chapters)

solutions/                # Drill cards (user content, gitignored)
├── focus/                # Active cards for drilling
└── examples/             # Sample cards demonstrating format

plan/                     # Study state (gitignored)
├── schedule.json         # Leitner box state
└── todo.md               # Sprint tasks
```

### Key Design Patterns

- **Filesystem as database**: All state in markdown + JSON. No external services.
- **Separation of content and engine**: Engine (`knos/`) is versioned; content (`solutions/`, `plan/` state) is gitignored.
- **Leitner intervals**: Box 0=1hr, Box 1=4hr, Box 2+=1d→3d→7d→14d→30d

### Core Data Flow

1. `core.py` parses markdown files, extracts fenced code blocks as drill targets
2. Blocks preceded by `<!-- INFO -->` (within 50 chars) are excluded from drilling
3. Blocks with language `slots` use prompt-answer format (prompts visible, answers hidden)
4. `schedule.json` tracks box level and next_due datetime per card
5. Code blocks require 100% to advance; slots blocks require 80%
6. `history.jsonl` logs all session results

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

### Slots Format (Conceptual Cards)

For conceptual knowledge (definitions, distinctions, processes), use `slots` blocks instead of code blocks. Slots show prompts during drill while hiding answers.

```markdown
## Definition

```slots
Definition :: Output at step t becomes input for step t+1
Process step 1 :: Predict next token based on context
Process step 2 :: Append predicted token to context
```
```

**Format:**
- Use `slots` as the block language
- Each drillable line: `Prompt :: Answer`
- Lines without `::` are headers (displayed but not drilled)
- Empty lines and `# Header` lines organize content

**Scoring:**
- Code blocks require 100% accuracy to advance
- Slots blocks require 80% accuracy to advance

**When to use each:**
- **Code blocks**: Executable code, algorithms, formulas you need to reproduce exactly
- **Slots blocks**: Definitions, distinctions, processes, conceptual relationships

## Configuration Files

Run `uv run knos init` to create config files interactively, or copy `.example` versions manually.

| File | Purpose |
|------|---------|
| `config/study.yaml` | Domain rotation, current phase, priority shifts |
| `config/reader.yaml` | LLM API keys, voice/TTS settings |
| `config/content.yaml` | PDF/EPUB/article registration |
| `plan/schedule.json` | Leitner box state (auto-managed) |

## Common Tasks

### Add a PDF Book to Reader

1. Create directory and place PDF:
   ```bash
   mkdir -p knos/reader/books/<material-id>
   cp /path/to/book.pdf knos/reader/books/<material-id>/source.pdf
   ```

2. Open PDF and note chapter page ranges (1-indexed PDF pages, not book page numbers)

3. Add entry to `config/content.yaml`:
   ```yaml
   material-id:
     title: "Book Title"
     author: "Author Name"
     source: "knos/reader/books/material-id/source.pdf"
     structure:
       type: chapters
       chapters:
         - { num: 1, title: "Introduction", pages: [15, 42] }
         - { num: 2, title: "Chapter Two", pages: [43, 78] }
   ```

4. Verify: `uv run knos read list`

### Add an EPUB Book to Reader

1. Place EPUB file:
   ```bash
   cp /path/to/book.epub knos/reader/books/<material-id>/source.epub
   ```

2. Add entry to `config/content.yaml` (no structure needed—extracted from EPUB TOC):
   ```yaml
   material-id:
     title: "Book Title"
     author: "Author Name"
     source: "knos/reader/books/material-id/source.epub"
   ```

3. Verify: `uv run knos read list`

### Add an Article (Single-Unit PDF)

1. Place PDF in articles directory:
   ```bash
   cp /path/to/paper.pdf knos/reader/articles/<name>.pdf
   ```

2. Add entry to `config/content.yaml`:
   ```yaml
   article-name:
     title: "Paper Title"
     author: "Author et al."
     source: "knos/reader/articles/article-name.pdf"
     structure:
       type: article
   ```

3. Verify: `uv run knos read list`

### Create a Drill Card

1. Create file in `solutions/focus/<domain>/<concept>.md`:
   ```markdown
   # Concept Name

   ## Context
   Explanatory text visible during drilling.

   ## Implementation
   ```python
   def example():
       # This block will be drilled line-by-line
       return "solution"
   ```
   ```

2. Every fenced code block becomes a drill target unless preceded by `<!-- INFO -->`:
   ```markdown
   <!-- INFO -->
   ```python
   # This block is informational only, not drilled
   ```
   ```

3. Card appears in next drill session automatically

### Reset a Card's Progress

Edit `plan/schedule.json` and set the card's box to 0:
```json
"focus/domain/card.md": {
  "box": 0,
  "next_due": "2025-01-01T00:00"
}
```

Or delete the entry entirely—it will be recreated on next drill.

## Content Registry Schema

### PDF with Chapters
```yaml
material-id:
  title: "string"           # Display title
  author: "string"          # Display author
  source: "knos/reader/books/material-id/source.pdf"  # Path relative to repo root
  structure:
    type: chapters
    chapters:
      - { num: 1, title: "Chapter Title", pages: [start, end] }  # 1-indexed PDF pages
    appendices:  # Optional
      - { id: "A", title: "Appendix Title", pages: [start, end] }
```

### EPUB (Auto-Structure)
```yaml
material-id:
  title: "string"
  author: "string"
  source: "knos/reader/books/material-id/source.epub"
  # No structure block—chapters extracted from EPUB TOC automatically
```

### Article (Single Unit)
```yaml
material-id:
  title: "string"
  author: "string"
  source: "knos/reader/articles/name.pdf"
  structure:
    type: article  # Entire PDF treated as one reading session
```

## Schedule State Schema

`plan/schedule.json` tracks Leitner box state per card:
```json
{
  "focus/domain/card.md": {
    "box": 2,                          // Leitner box (0-7)
    "next_due": "2025-01-15T10:00",    // ISO datetime when card is next due
    "last_score": 100.0,               // Percentage correct on last drill
    "last_reviewed": "2025-01-14T10:00" // ISO datetime of last review
  }
}
```

Box intervals: 0=1hr, 1=4hr, 2=1d, 3=3d, 4=7d, 5=14d, 6=30d, 7=90d

## Troubleshooting

> **Note:** For user-facing troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md). This section covers developer-focused debugging.

### Card not appearing in drill queue
- **Check location**: Must be in `solutions/focus/`, not `solutions/` root or `solutions/examples/`
- **Check format**: Must have at least one fenced code block (triple backticks)
- **Check schedule**: Run `uv run python3 -m knos.reviewer.reviewer --due-json` to see due cards
- **Check due time**: Card may not be due yet—see `plan/schedule.json` for `next_due`

### Material shows "0 chapters available" in reader
- **Check source exists**: Verify file at registered path under `knos/` directory
- **Check page ranges**: For PDFs, `structure.chapters` must be defined with valid page ranges
- **Check EPUB structure**: For EPUBs, ensure file is valid and has TOC

### LLM test fails in reader
- **Check config**: Run `uv run knos init` or ensure `config/reader.yaml` exists
- **Check API key**: Verify `GOOGLE_API_KEY` env var or key in config
- **Test directly**: `uv run knos read test`

### Card always resetting to box 0
- **Perfect score required**: Any incorrect line resets to box 0 (strict Leitner)
- **Check block content**: Ensure no trailing whitespace or blank lines in code blocks

## Dependencies

Uses `uv` for package management:
```bash
uv sync                    # Install core dependencies
uv sync --extra voice      # Voice input + Kokoro TTS (~1GB VRAM)
uv sync --extra chatterbox # Voice + Chatterbox TTS (~3-4GB VRAM)
uv run knos                # Run with dependencies
```

Core: `textual`, `rich`, `typer`, `google-genai`, `pymupdf`, `ebooklib`
Voice (optional): `faster-whisper`, `kokoro`, `sounddevice`, `torch`
Chatterbox (optional): `chatterbox-tts` (turbo model requires `huggingface-cli login`)

Note: Voice features require PyTorch which only supports Linux, macOS ARM64, and Windows.

## Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Users | Prerequisites, installation, first session |
| [docs/USAGE.md](docs/USAGE.md) | Users | Commands, workflows, keybindings |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Users | Common issues and fixes |
| [docs/PEDAGOGY.md](docs/PEDAGOGY.md) | Users | Learning science behind the Reader |
| [docs/EDUCATORS.md](docs/EDUCATORS.md) | Educators | Classroom adoption guide |
| [knos/reader/OVERVIEW.md](knos/reader/OVERVIEW.md) | Users | Reader module details |
| [solutions/examples/README.md](solutions/examples/README.md) | Users | Drill card format guide |

## Development Notes

- Engine code tracked in git: `knos/` (includes `knos/reader/classics/`, `knos/reader/articles/`)
- User content gitignored: `solutions/`, `config/` (except `.example`), `plan/` state files, `knos/reader/books/`
- The CLI entry point is `knos/cli.py` → `knos.cli:main`
- TUI built on Textual; CLI tools use Rich
