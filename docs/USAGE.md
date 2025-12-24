# Knowledge OS

Reference for the self-study TUI and spaced-repetition tooling.

## Quick Start

```bash
knos                 # Launch study TUI (default)
knos today           # CLI dashboard
knos read            # Reading companion
```

## Documentation Index

| Resource | Purpose |
|----------|---------|
| **[plan/syllabus.md](../plan/syllabus.md)** | **Content**: Master study plan |
| **[docs/manual/workflow.md](manual/workflow.md)** | **Process**: Reading prompts & Study workflow |
| **[docs/specs/roadmap.md](specs/roadmap.md)** | **Future**: Enhancement plans |
| **[AGENTS.md](../AGENTS.md)** | **AI**: Context for coding assistants |
| **[knos/reader/OVERVIEW.md](../knos/reader/OVERVIEW.md)** | **Reader**: Seminar-style LLM dialogue companion |

## Commands Reference

| Command | Description |
|---------|-------------|
| `knos` | Launch study TUI (default) |
| `knos init` | Initialize config files |
| `knos today` | Print CLI dashboard |
| `knos study` | Launch study TUI |
| `knos drill` | Launch drill TUI |
| `knos read` | Launch reading companion TUI |
| `knos progress` | Generate PROGRESS.md |

### Reader CLI

**Setup:**
1. Run `knos init` to create config files
2. Place PDF in `knos/reader/books/<material-id>/source.pdf`
3. Register in `config/content.yaml` with chapter page ranges
4. Run: `knos read` → select material → select chapter

Registration can be done manually or with AI tools (e.g. Claude Code to extract TOC).

| Command | Description |
|---------|-------------|
| `knos read` | Launch TUI (material → chapter → dialogue) |
| `knos read list` | List registered materials |
| `knos read clear <id> [chapter]` | Clear session data |
| `knos read export <id> [chapter] [-o file]` | Export session to markdown |
| `knos read test` | Verify LLM configuration |
| `knos read --help` | Show setup instructions |

### Reviewer CLI (Direct)

```bash
uv run python3 -m reviewer.reviewer              # Interactive select
uv run python3 -m reviewer.reviewer --focus      # All cards, random order
uv run python3 -m reviewer.reviewer --summary    # Mastery status
uv run python3 -m reviewer.reviewer --due        # Show due cards
uv run python3 -m reviewer.reviewer --drill-due  # Drill due only
```

## Creating Solutions (Cheat Sheet)

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
