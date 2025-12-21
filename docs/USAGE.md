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
| **[docs/manual/architecture.md](manual/architecture.md)** | **System**: Architecture, Directory Tree, Data Logic |
| **[docs/manual/workflow.md](manual/workflow.md)** | **Process**: Reading prompts & Study workflow |
| **[docs/specs/roadmap.md](specs/roadmap.md)** | **Future**: Enhancement plans |
| **[AGENTS.md](../AGENTS.md)** | **AI**: Context for coding assistants |
| **[reader/OVERVIEW.md](../reader/OVERVIEW.md)** | **Reader**: Seminar-style LLM dialogue companion |

## Commands Reference

| Command | Description |
|---------|-------------|
| `knos` | Launch study TUI (default) |
| `knos today` | Print CLI dashboard |
| `knos study` | Launch study TUI |
| `knos drill` | Launch drill TUI |
| `knos read` | Launch reading companion TUI |
| `knos progress` | Generate PROGRESS.md |

### Reader CLI

**Workflow:**
1. Register material in `reader/content_registry.yaml` (source path + chapter structure)
2. Extract: `knos read extract <material-id>`
3. Read: `knos read` → select material → select chapter

| Command | Description |
|---------|-------------|
| `knos read` | Launch TUI (material → chapter → dialogue) |
| `knos read list` | List registered materials |
| `knos read extract <id>` | Extract/copy material to `reader/extracted/` |
| `knos read clear <id> [chapter]` | Clear session data |
| `knos read test` | Verify LLM configuration |
| `knos read --help` | Show usage and workflow |

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
