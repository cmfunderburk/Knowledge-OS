# Knowledge OS

A study system built on dialogue.

## Why Dialogue?

At [St. John's College](https://www.sjc.edu/), students spend four years reading primary sources—Homer to Einstein—not through lectures, but through seminar discussion. Understanding emerges through articulation: defending interpretations, responding to challenges, returning to the text when claims don't hold up.

Knowledge OS brings this approach to self-study. The Reader module pairs you with an LLM tutor who engages with the same material you're reading. It asks questions rather than lectures. It treats the text as the authority. When you claim to understand something, it probes.

## The Loop

```
Read → Discuss with tutor → (optionally) Generate drill cards
              ↑                              │
              └────── revisit as needed ─────┘
```

The dialogue is the core. Card generation is there when you identify concepts worth drilling—definitions, procedures, distinctions you want to retain long-term.

## Quick Start

```bash
uv sync                     # Install dependencies
uv sync --extra voice       # Optionally install Kokoro TTS + Voice Input
uv run knos init            # Create config (prompts for API key)
uv run knos read            # Start the Reader
```

Three classics and five foundational articles work immediately. See [Getting Started](docs/GETTING_STARTED.md) for prerequisites, adding your own content, and the full workflow.

## The Reader

A dialogue interface for working through texts with an LLM tutor.

| Mode | Behavior |
|------|----------|
| **Socratic** | Probing questions, rarely gives answers (default) |
| **Clarify** | Direct explanations when stuck |
| **Challenge** | Devil's advocate, stress-tests claims |
| **Teach** | You explain to a "confused student" |
| **Quiz** | Rapid-fire recall check |
| **Technical** | Step-by-step guidance for formulas and procedures |

Press `Ctrl+G` during a session to generate drill cards from the conversation.

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

For concepts that benefit from long-term retention, Knowledge OS includes a spaced repetition system. Cards are markdown files revealed line-by-line during drill. The Leitner-box scheduler enforces mastery at the edge of recall.

```bash
uv run knos drill    # Drill due cards
uv run knos          # TUI dashboard
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Getting Started](docs/GETTING_STARTED.md) | Prerequisites, installation, first session |
| [Usage Guide](docs/USAGE.md) | Commands, workflows, keybindings |
| [Pedagogy](docs/PEDAGOGY.md) | Learning science behind the Reader |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [Card Format](solutions/examples/README.md) | Creating drill cards |

## License

MIT
