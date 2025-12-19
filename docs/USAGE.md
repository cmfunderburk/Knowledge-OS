# Knowledge OS

Reference for the self-study TUI and spaced-repetition tooling.

## Quick Start

```bash
./study              # Launch TUI dashboard (Primary Interface)
```

## Documentation Index

| Resource | Purpose |
|----------|---------|
| **[plan/syllabus.md](../plan/syllabus.md)** | **Content**: Master study plan |
| **[docs/manual/architecture.md](manual/architecture.md)** | **System**: Architecture, Directory Tree, Data Logic |
| **[docs/manual/workflow.md](manual/workflow.md)** | **Process**: Reading prompts & Study workflow |
| **[docs/specs/roadmap.md](specs/roadmap.md)** | **Future**: Enhancement plans |
| **[AGENTS.md](../AGENTS.md)** | **AI**: Context for coding assistants |
| **[reader/OVERVIEW.md](../reader/OVERVIEW.md)** | **Reader**: Seminar-style LLM dialogue companion |

## Commands Reference

| Command | Description |
|---------|-------------|
| `./study` | Launch TUI dashboard |
| `./study --today` | Print CLI dashboard |
| `./study --progress` | Generate PROGRESS.md |
| `./today` | CLI daily orientation |
| `./drill` | Launch drill queue (Textual TUI) |
| `./read` | Launch reading companion TUI (LLM dialogue) |

### Reader CLI

| Command | Description |
|---------|-------------|
| `./read` | Launch TUI (material → chapter → dialogue) |
| `./read --list` | List registered materials and extraction status |
| `./read --extract <id>` | Extract chapters from PDF to `reader/extracted/` |
| `./read --test-llm` | Verify LLM configuration |
| `./read --help` | Show usage information |

### Reviewer CLI (Direct)

```bash
uv run python3 -m reviewer.reviewer              # Interactive select
uv run python3 -m reviewer.reviewer --focus      # All cards, random order
uv run python3 -m reviewer.reviewer --summary    # Mastery status
uv run python3 -m reviewer.reviewer --due        # Show due cards
uv run python3 -m reviewer.reviewer --drill-due  # Drill due only
```

## Creating Solutions (Cheat Sheet)

Full details in **[docs/manual/architecture.md](manual/architecture.md)**.

```markdown
# Topic Name

**Time:** O(?)  |  **Space:** O(?)

## How It Works

Context visible during practice.

## Implementation

```python
def algorithm():
    pass
```

## When to Use

- Use case 1
```

**Rules:**
- `<!-- INFO -->` prefix excludes blocks from drill.
- One concept per file.
