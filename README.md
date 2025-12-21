# Knowledge OS

A study system built on dialogue.

## Why Dialogue?

At [St. John's College](https://www.sjc.edu/), students spend four years reading primary sources—Homer to Einstein—not through lectures, but through seminar discussion. Understanding emerges through articulation: defending interpretations, responding to challenges, returning to the text when claims don't hold up.

Knowledge OS attempts to emulate this approach in the context of self-study. The Reader module pairs you with an LLM tutor who engages with the same material you're reading. It asks questions rather than lectures. It treats the text as the authority. When you claim to understand something, it probes.

## The Loop

```
Read → Discuss with tutor → (optionally) Generate drill cards
              ↑                              │
              └────── revisit as needed ─────┘
```

The dialogue is the core. Card generation is there when you identify concepts worth drilling—definitions, procedures, distinctions you want to retain long-term.

## Quick Start

```bash
uv sync              # Install dependencies
uv run knos read     # Start the Reader (requires LLM API key)
```

To set up the Reader:

```bash
cp reader/config.yaml.example reader/config.yaml
# Edit with your Gemini API key

cp reader/content_registry.yaml.example reader/content_registry.yaml
# Register your PDFs (see below)
```

The example registry includes free [OpenStax](https://openstax.org/) textbooks, bundled classics from Project Gutenberg, and foundational articles (the Transformer paper, Einstein 1905). Download a PDF, place it in `reader/sources/<material-id>/source.pdf`, and start a session. The classics and articles work out of the box.

## The Reader

A dialogue interface for working through texts with an LLM tutor—textbooks, philosophy, literature.

Three classics from Project Gutenberg are bundled and work out of the box:

- **Nicomachean Ethics** — Aristotle (F.H. Peters translation)
- **Don Quixote** — Cervantes (John Ormsby translation)
- **The Brothers Karamazov** — Dostoevsky (Constance Garnett translation)

Two foundational articles are also bundled:

- **Attention Is All You Need** — Vaswani et al. (the Transformer paper)
- **On a Heuristic Point of View Concerning the Production and Transformation of Light** — Einstein (1905 photoelectric effect paper)

To enable the bundled articles, copy their entries from `reader/content_registry.yaml.example` to your `reader/content_registry.yaml`. Articles skip chapter selection and open directly into dialogue.

<details>
<summary><strong>Example: Discussing Aristotle's Nicomachean Ethics</strong></summary>

<video src="https://github.com/user-attachments/assets/af95aa25-b736-4930-b359-58511d21f574" controls width="600"></video>


</details>

<details>
<summary><strong>Example: Opening question for Don Quixote</strong></summary>

<video src="https://github.com/user-attachments/assets/e16ac913-b0a3-41b5-85b4-beb6520e5c4e" controls width="600"></video>

</details>

<details>
<summary><strong>Example: Discussing Einstein's Photoelectric Effect paper</strong></summary>

<video src="https://github.com/user-attachments/assets/1bb29977-dcf3-4375-a962-3f9cc40df5d1" controls width="600"></video>

</details>

The tutor doesn't lecture—it asks questions, probes your understanding, and points you back to the text. When you begin a new chapter, it opens with a genuine question about the reading. Dialogue modes include:

| Mode | Behavior |
|------|----------|
| **Socratic** | Probing questions, rarely gives answers (default) |
| **Clarify** | Direct explanations when you're genuinely stuck |
| **Challenge** | Devil's advocate, stress-tests your claims |
| **Teach** | You explain to a "confused student" |
| **Quiz** | Rapid-fire recall check |

Press `Ctrl+G` during a session to generate drill cards from the conversation. The LLM identifies concepts worth retaining based on the dialogue—what you struggled with, what required clarification, what you explored deeply.

## The Reviewer

For concepts that benefit from long-term retention, Knowledge OS includes a spaced repetition system.

Cards are markdown files containing fenced code blocks. During drill, content is revealed line-by-line—you reconstruct it, then self-assess. The system uses Leitner-box scheduling: 100% accuracy advances the card; any mistake resets it. This enforces mastery at the edge of recall.

```bash
uv run knos drill    # Drill due cards
uv run knos          # TUI dashboard (shows what's due)
```

Cards generated from Reader sessions go to `reader/drafts/` for review before entering the drill system.

## CLI Reference

```
knos              TUI dashboard (default)
knos read         Reader TUI
knos drill        Drill TUI
knos today        Today's study plan (CLI)
knos progress     Generate PROGRESS.md

knos read list              List registered materials
knos read clear <id> [ch]   Clear session data
knos read test              Test LLM configuration
```

## Configuration

### Reader Setup

```bash
cp reader/config.yaml.example reader/config.yaml
cp reader/content_registry.yaml.example reader/content_registry.yaml
```

Edit `reader/config.yaml` with your Gemini API key. Edit `reader/content_registry.yaml` to register PDFs with chapter page ranges.

### Study Configuration (optional)

```bash
cp plan/study_config.yaml.example plan/study_config.yaml
cp plan/schedule.json.example plan/schedule.json
```

Configure domain rotation (which subjects on which days), curriculum phases, and priority shifts.

### Drill Cards

Create markdown files in `solutions/focus/`. Every fenced code block becomes a drill target. See [solutions/examples/](solutions/examples/) for the card format.

## Documentation

- [reader/OVERVIEW.md](reader/OVERVIEW.md) — Reader module design and pedagogy
- [docs/USAGE.md](docs/USAGE.md) — Command reference
- [solutions/examples/README.md](solutions/examples/README.md) — Card format guide
- [AGENTS.md](AGENTS.md) — Technical documentation for AI assistants

## License

MIT
