# Knowledge OS

A study system built on dialogue.

## Why Dialogue?

At St. John's College, students spend four years reading primary sources—Homer to Einstein—not through lectures, but through seminar discussion. Understanding emerges through articulation: defending interpretations, responding to challenges, returning to the text when claims don't hold up. I've been drawn to this model for years, and Knowledge OS is my attempt to bring something like it to self-study.

The Reader module pairs you with an LLM tutor who engages with the same material you're reading. It asks questions rather than lectures. It treats the text as the authority. When you claim to understand something, it probes. Whether this actually works—whether the dynamics that make St. John's seminars effective transfer to human-LLM dialogue—is something I'm still figuring out. But I've found it more productive than reading alone.

Stringfellow Barr's ["Notes on Dialogue"](knos/reader/articles/notes-on-dialogue.pdf) (1968) articulates the philosophy behind this approach better than I can. The [Introduction](docs/Introduction-to-this-Project.md) orients newcomers to the system and its documentation, while the [Pedagogy](docs/PEDAGOGY.md) document records my exploration of how to prompt LLMs for learning—part design journal, part hypothesis log.

## The Loop

The core workflow is simple: read something, discuss it with the tutor, and (when concepts seem worth retaining long-term) generate drill cards from the conversation. The dialogue is primary. Card generation is there when you identify definitions, procedures, or distinctions you want to keep.

```
Read → Discuss with tutor → (optionally) Generate drill cards
              ↑                              │
              └────── revisit as needed ─────┘
```

## Quick Start

```bash
uv sync                     # Install dependencies
uv sync --extra voice       # Optional: Kokoro TTS + voice input
uv run knos init            # Create config (prompts for API key)
uv run knos read            # Start the Reader
```

Three classics (Aristotle, Cervantes, Dostoevsky) and six foundational articles work immediately—no setup beyond the API key. See [Getting Started](docs/GETTING_STARTED.md) for prerequisites, adding your own content, and the full workflow.

## The Reader

The Reader is a dialogue interface for working through texts with an LLM tutor. It defaults to Socratic mode—probing questions, rarely giving direct answers—which I've found most productive for developing understanding, though it can be frustrating when you're genuinely stuck.

Other modes serve different purposes. Clarify provides direct explanations when Socratic questioning isn't helping. Challenge plays devil's advocate and stress-tests your claims (useful when you're confident, perhaps overconfident, about an interpretation). Teach reverses roles: you explain to a simulated confused student, which reveals gaps in your understanding surprisingly well. Quiz runs rapid-fire recall checks. Technical walks through formulas and procedures step by step.

You can switch modes mid-conversation with `Ctrl+M`, and generate drill cards from the discussion with `Ctrl+G`.

<details>
<summary><strong>Demo: Discussing Aristotle's Nicomachean Ethics</strong></summary>

<video src="https://github.com/user-attachments/assets/af95aa25-b736-4930-b359-58511d21f574" controls width="600"></video>

</details>

<details>
<summary><strong>Demo: Opening question for Don Quixote</strong></summary>

<video src="https://github.com/user-attachments/assets/e16ac913-b0a3-41b5-85b4-beb6520e5c4e" controls width="600"></video>

</details>

<details>
<summary><strong>Demo: Discussing Einstein's Photoelectric Effect paper</strong></summary>

<video src="https://github.com/user-attachments/assets/1bb29977-dcf3-4375-a962-3f9cc40df5d1" controls width="600"></video>

</details>

## The Reviewer

For concepts that benefit from long-term retention, Knowledge OS includes a spaced repetition system. Cards are markdown files revealed line-by-line during drill. The Leitner-box scheduler enforces mastery at the edge of recall—any failure resets a card to box zero, which sounds harsh but seems to work.

```bash
uv run knos drill    # Drill due cards
uv run knos          # TUI dashboard
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Introduction](docs/Introduction-to-this-Project.md) | What this is, who it's for, documentation map |
| [Getting Started](docs/GETTING_STARTED.md) | Prerequisites, installation, first session |
| [Usage Guide](docs/USAGE.md) | Commands, workflows, keybindings |
| [Pedagogy](docs/PEDAGOGY.md) | Design journal on LLM-assisted learning |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [Card Format](solutions/examples/README.md) | Creating drill cards |

## License

MIT
