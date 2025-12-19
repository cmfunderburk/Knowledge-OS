# System Architecture & Design

## Overview

This repository hosts a knowledge operating system with a **Textual-based TUI** as the primary interface. The system supports configurable study domains and spaced-repetition drilling.

The system is designed to facilitate a workflow of **Read → Practice → Memorize → Review**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ./study (TUI Entry Point)                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                   │
│  │ Dashboard │  │   Drill   │  │  Browse   │                   │
│  │  Screen   │  │  Screen   │  │  Screen   │                   │
│  └───────────┘  └───────────┘  └───────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│   ./today (CLI)      │              │   ./drill (TUI)      │
└──────────────────────┘              └──────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    reviewer/core.py (Library)                   │
│  - Schedule management    - Markdown parsing                    │
│  - Leitner box logic      - Progress tracking                   │
│  - History logging        - Domain rotation                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                              │
│  - plan/schedule.json     - solutions/**/*.md                   │
│  - history.jsonl          - plan/todo.md                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ./read (Reader TUI)                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                   │
│  │  Select   │  │  Select   │  │ Dialogue  │                   │
│  │ Material  │→│  Chapter  │→│  Screen   │                   │
│  └───────────┘  └───────────┘  └───────────┘                   │
├─────────────────────────────────────────────────────────────────┤
│  reader/llm.py      — LLM providers (Gemini, Anthropic)         │
│  reader/content.py  — PDF extraction, chapter loading           │
│  reader/prompts.py  — Jinja2 prompt templates                   │
├─────────────────────────────────────────────────────────────────┤
│  reader/extracted/  — Pre-extracted chapter .md files           │
│  reader/content_registry.yaml — Material definitions            │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles
1. **Shared data layer**: `reviewer/core.py` is the single source of truth.
2. **TUI calls core directly**: No subprocess calls; direct library imports.
3. **Backward compatibility**: CLI remains via `reviewer/reviewer.py` when needed.
4. **Stateless screens**: Each TUI screen loads fresh data on mount.

## Directory Structure

```
knowledge/
├── study                    # TUI entry point (RECOMMENDED)
├── today                    # CLI daily dashboard
├── drill                    # Drill TUI entry point
├── read                     # Reader TUI entry point (LLM dialogue)
│
├── reviewer/                # Spaced-repetition engine
│   ├── core.py              # Business logic (shared data layer)
│   └── reviewer.py          # Legacy/CLI interface
│
├── tui/                     # Textual-based TUI
│   ├── app.py               # Textual App class (StudyApp, DrillApp, ReaderApp)
│   ├── screens/             # Dashboard, Drill, Browse screens
│   └── widgets/             # Reusable panel widgets
│
├── reader/                  # Reading companion module
│   ├── config.py            # Config and registry loading
│   ├── content.py           # PDF extraction, chapter loading
│   ├── llm.py               # LLM providers (Gemini, Anthropic)
│   ├── prompts.py           # Jinja2 template loading
│   ├── screens/             # SelectMaterial, SelectChapter, Dialogue
│   ├── prompts/             # base.md, socratic.md, clarify.md, challenge.md
│   ├── extracted/           # Pre-extracted chapter .md files (gitignored)
│   ├── content_registry.yaml  # Material definitions
│   └── config.yaml          # LLM API keys (gitignored)
│
├── solutions/               # Study content (gitignored)
│   └── focus/               # Active drill targets
│
├── plan/                    # Study planning files (gitignored except .example)
│   ├── study_config.yaml    # Domain rotation, phases, priority shifts
│   ├── schedule.json        # Leitner box schedule
│   ├── todo.md              # Active task list
│   └── syllabus.md          # Master study plan
│
├── scripts/
│   └── progress.py          # Dashboard generator
│
├── PROGRESS.md              # Auto-generated progress report
│
├── Textbooks/               # Textbook materials (gitignored)
│   └── HTPI/HTPILeanPackage/  # Lean 4 exercises
│
└── docs/                    # Documentation
    ├── manual/              # System manuals (Architecture, Workflow)
    └── specs/               # Specifications (Roadmap, Curriculum)
```

## Core Data Layer (`reviewer/core.py`)

**Key Functions:**
- `parse_markdown(text)`: Extract fenced blocks; `<!-- INFO -->` marks non-targets.
- `load_schedule() / save_schedule()`: Manage `plan/schedule.json`.
- `update_schedule(path, score)`: Leitner box advancement logic.
- `get_drill_queue()`: Priority-sorted due cards for drilling.
- `get_reviewer_summary()`: Aggregate stats (box_zero, overdue, due_now, etc.).
- `get_todays_domain()`: Domain rotation based on weekday.
- `get_next_task()`: Next unchecked item from `plan/todo.md`.
- `generate_progress_report()`: Full markdown progress dashboard.

**Spaced Repetition (Leitner Box):**
- Perfect recall (100%) → advance box (longer interval).
- Imperfect → reset to box 0.
- Intervals: 1h → 4h → 1d → 3d → 7d → 14d → 30d.
