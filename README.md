# knowledge

A knowledge operating system: spaced-repetition drilling + LLM-powered reading companion for self-study.

## What This Is

A personal autodidact toolkit built around active recall and spaced repetition. Two core systems:

- **Reviewer**: Leitner-box spaced repetition. Cards contain fenced code blocks revealed line-by-line — you reconstruct the content, then self-assess. 100% accuracy advances; any failure resets to box 0. This enforces mastery at the edge of recall.

- **Reader**: LLM-powered reading companion. Structured dialogue with textbook chapters — Socratic questioning, challenge mode, quiz, teach-back. Surfaces gaps in understanding before they calcify.

Built for daily use. Open-sourced as proof-of-concept.

## Quick Start

```bash
uv sync        # Install dependencies
./study        # TUI dashboard (main entry point)
./drill        # Drill due cards
./read         # Reading companion (requires LLM API)
```

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Copy required configuration

```bash
# Core study configuration (domain rotation, intervals, phases)
cp plan/study_config.yaml.example plan/study_config.yaml

# Example scheduler state (shows card format)
cp plan/schedule.json.example plan/schedule.json
```

### 3. Copy optional planning files

These files help organize your study workflow but aren't required to run the system:

```bash
# Sprint tasks and daily goals
cp plan/todo.md.example plan/todo.md

# High-level study plan overview
cp plan/syllabus.md.example plan/syllabus.md

# Chapter progress tracking (Read/Exercises/Cards checkboxes)
cp plan/checklist.md.example plan/checklist.md

# Temporary focus override for exam prep sprints
cp plan/priority_shift.md.example plan/priority_shift.md
```

### 4. Try the example drill cards

```bash
# Copy examples to your solutions folder
cp -r solutions/examples/* solutions/focus/

# Start the TUI dashboard
./study

# Or drill directly
./drill
```

### 5. Set up the Reader (optional)

The Reader provides LLM-powered dialogue with textbook content. Requires a Gemini or Anthropic API key.

```bash
# LLM configuration
cp reader/config.yaml.example reader/config.yaml
# Edit reader/config.yaml with your API key

# Content registry (book → chapter mappings)
cp reader/content_registry.yaml.example reader/content_registry.yaml
```

The example registry uses free OpenStax textbooks (CC BY 4.0):

```bash
mkdir -p reader/extracted/{psychology-2e,economics-3e,college-algebra-2e}

# Psychology 2e (84 MB)
# https://openstax.org/details/books/psychology-2e
# Download PDF → reader/extracted/psychology-2e/source.pdf

# Economics 3e (63 MB)
# https://openstax.org/details/books/principles-economics-3e
# Download PDF → reader/extracted/economics-3e/source.pdf

# College Algebra 2e (80 MB)
# https://openstax.org/details/books/college-algebra-2e
# Download PDF → reader/extracted/college-algebra-2e/source.pdf
```

Then extract chapters for dialogue:

```bash
./read --extract psychology-2e
./read
```

## Core Components

| Component | Description |
|-----------|-------------|
| `reviewer/` | Leitner-box spaced repetition engine (boxes 0–6, intervals from 1hr to 30 days) |
| `tui/` | Textual-based TUI for daily study orientation |
| `reader/` | Seminar-style reading companion with LLM dialogue |
| `solutions/` | Drill cards — code, proofs, definitions, models |
| `docs/` | Architecture, workflow guides, and design specs |

## Documentation

- [docs/knowledge-os-manifesto.md](docs/knowledge-os-manifesto.md) — Vision and principles
- [docs/USAGE.md](docs/USAGE.md) — Command reference
- [docs/specs/roadmap.md](docs/specs/roadmap.md) — Feature roadmap and future plans
- [docs/prompts.md](docs/prompts.md) — LLM prompt library for study workflows
- [solutions/examples/README.md](solutions/examples/README.md) — Card format guide
- [AGENTS.md](AGENTS.md) — Technical documentation for AI assistants

## License

MIT
