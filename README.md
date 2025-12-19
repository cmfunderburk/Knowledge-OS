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

The system works out of the box with example drill cards in `solutions/examples/`. Run `./study` or `./drill` immediately after installing to try it.

## Customization

To build your own study system, copy and edit the example configuration files.

### Study Configuration

```bash
# Copy examples to create your config files
cp plan/study_config.yaml.example plan/study_config.yaml
cp plan/schedule.json.example plan/schedule.json
```

Edit `plan/study_config.yaml` to configure:
- **Domain rotation**: Which subjects to study on which days
- **Current phase**: Track your progress through a curriculum
- **Priority shifts**: Temporary focus overrides for exam prep

### Planning Files (optional)

These help organize your workflow but aren't required:

```bash
cp plan/todo.md.example plan/todo.md          # Sprint tasks and daily goals
cp plan/syllabus.md.example plan/syllabus.md  # High-level study plan
cp plan/checklist.md.example plan/checklist.md # Chapter progress tracking
```

### Your Own Drill Cards

Create markdown files in `solutions/focus/` (or any subdirectory). Every fenced code block becomes a drill target. See [solutions/examples/README.md](solutions/examples/README.md) for the card format guide.

### Reader Setup (optional)

The Reader provides LLM-powered dialogue with textbook content. Requires a Gemini or Anthropic API key.

```bash
cp reader/config.yaml.example reader/config.yaml
# Edit reader/config.yaml with your API key

cp reader/content_registry.yaml.example reader/content_registry.yaml
# Edit to register your own PDFs
```

The example registry uses free OpenStax textbooks (CC BY 4.0). To use them:

1. Download PDFs from [OpenStax](https://openstax.org/):
   - [Psychology 2e](https://openstax.org/details/books/psychology-2e) (84 MB)
   - [Principles of Economics 3e](https://openstax.org/details/books/principles-economics-3e) (63 MB)
   - [College Algebra 2e](https://openstax.org/details/books/college-algebra-2e) (80 MB)

2. Place PDFs in `reader/extracted/<material-id>/source.pdf`

3. Extract chapters: `./read --extract psychology-2e`

4. Start dialogue: `./read`

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
