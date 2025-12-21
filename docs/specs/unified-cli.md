# Unified CLI Implementation Plan

**Status**: Implemented
**Created**: 2025-12-20

## Overview

Replace the four standalone scripts (`today`, `study`, `drill`, `read`) with a single CLI entry point. This consolidates the interface, cleans up the project root, and provides a discoverable, extensible command structure.

---

## Current State

### Scripts in Project Root

| Script | Purpose | Complexity |
|--------|---------|------------|
| `./today` | CLI dashboard (domain, due cards, next task) | Simple - print only |
| `./study` | TUI dashboard + `--today`, `--progress` flags | Medium - TUI + CLI modes |
| `./drill` | TUI drill queue | Simple - TUI only |
| `./read` | TUI reader + `--extract`, `--list`, `--clear`, `--test-llm` | Complex - TUI + multiple CLI modes |

### Problems

1. **Root clutter**: Four executable scripts pollute the project root
2. **Redundancy**: `./today` duplicates `./study --today`
3. **Inconsistent interfaces**: `read` uses argparse, others use manual parsing
4. **Shebang complexity**: Required `#!/usr/bin/env -S uv run python3` workaround
5. **Discoverability**: New users must read docs to find commands

---

## Proposed Design

### Command Structure

```
knos <command> [options]
```

| Command | Description | Maps to |
|---------|-------------|---------|
| `knos` | Launch main TUI (default) | `./study` |
| `knos today` | Print CLI dashboard | `./today` |
| `knos study` | Launch study TUI | `./study` |
| `knos drill` | Launch drill TUI | `./drill` |
| `knos read` | Launch reader TUI | `./read` |
| `knos read extract <id>` | Extract material chapters | `./read --extract` |
| `knos read list` | List registered materials | `./read --list` |
| `knos read clear <id> [ch]` | Clear session data | `./read --clear` |
| `knos read test` | Test LLM provider | `./read --test-llm` |
| `knos progress` | Generate progress report | `./study --progress` |

### Default Behavior

Running `knos` with no arguments launches the main study TUI (most common action).

### Help Output

```
$ knos --help

Knowledge OS - Study system for self-directed learning

Usage: knos [command] [options]

Commands:
  (default)    Launch the study TUI
  today        Show today's study plan (CLI)
  study        Launch the study TUI
  drill        Launch the drill TUI
  read         Launch the reader TUI
  progress     Generate PROGRESS.md report

Reader subcommands:
  read extract <id>       Extract chapters from a material
  read list               List registered materials
  read clear <id> [ch]    Clear session data
  read test               Test LLM provider

Options:
  -h, --help     Show this help message
  -v, --version  Show version

Examples:
  knos                    # Start studying (TUI)
  knos today              # Quick status check
  knos read               # Start a reading session
  knos read extract foo   # Extract material "foo"
```

---

## Implementation

### Technology Choice: Typer

Use [Typer](https://typer.tiangolo.com/) for the CLI framework.

**Why Typer:**

- Built on Click (inherits maturity and reliability)
- Type hints define arguments/options - less boilerplate
- Automatic help generation from docstrings and type annotations
- Clean, Pythonic API
- Good subcommand/command group support via `typer.Typer()` instances

### File Structure

```
knos/
├── __init__.py
├── cli.py              # Main CLI entry point
├── commands/
│   ├── __init__.py
│   ├── today.py        # 'knos today' command
│   ├── study.py        # 'knos study' command
│   ├── drill.py        # 'knos drill' command
│   ├── read.py         # 'knos read' command group
│   └── progress.py     # 'knos progress' command
└── utils.py            # Shared CLI utilities (colors, formatting)
```

### Entry Point Registration

```toml
# pyproject.toml

[project.scripts]
knos = "knos.cli:main"
```

After `uv sync`, `knos` will be available in the virtualenv and can be run via:
```bash
uv run knos
uv run knos today
uv run knos read extract foo
```

### Core Implementation

```python
# knos/cli.py
import typer
from typing import Optional

app = typer.Typer(
    help="Knowledge OS - Study system for self-directed learning.",
    no_args_is_help=False,
)

# Reader subcommand group
read_app = typer.Typer(help="Reading companion - seminar-style dialogue with texts.")
app.add_typer(read_app, name="read")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Default behavior: launch study TUI if no command given."""
    if ctx.invoked_subcommand is None:
        from knos.commands.study import run_study
        run_study()


@app.command()
def today():
    """Show today's study plan (CLI dashboard)."""
    from knos.commands.today import run_today
    run_today()


@app.command()
def study():
    """Launch the study TUI."""
    from knos.commands.study import run_study
    run_study()


@app.command()
def drill():
    """Launch the drill TUI."""
    from knos.commands.drill import run_drill
    run_drill()


@app.command()
def progress():
    """Generate PROGRESS.md report."""
    from knos.commands.progress import run_progress
    run_progress()


# --- Reader subcommands ---

@read_app.callback(invoke_without_command=True)
def read_main(ctx: typer.Context):
    """Default: launch reader TUI if no subcommand given."""
    if ctx.invoked_subcommand is None:
        from knos.commands.read import run_read_tui
        run_read_tui()


@read_app.command("extract")
def read_extract(material_id: str):
    """Extract chapters from a registered material."""
    from knos.commands.read import run_extract
    run_extract(material_id)


@read_app.command("list")
def read_list():
    """List registered materials."""
    from knos.commands.read import run_list
    run_list()


@read_app.command("clear")
def read_clear(material_id: str, chapter: Optional[int] = None):
    """Clear session data for a material."""
    from knos.commands.read import run_clear
    run_clear(material_id, chapter)


@read_app.command("test")
def read_test():
    """Test LLM provider configuration."""
    from knos.commands.read import run_test_llm
    run_test_llm()


if __name__ == "__main__":
    app()
```

### Command Implementations

Each command module is a thin wrapper that imports and calls the existing logic:

```python
# knos/commands/today.py
def run_today():
    """CLI dashboard - moved from ./today"""
    from reviewer.core import (
        get_todays_domain,
        get_next_task,
        get_reviewer_summary,
        get_overall_progress,
        collect_focus_files,
    )
    from reader.config import load_registry
    from reader.session import list_sessions, SESSIONS_DIR

    # ... existing today logic ...
```

This keeps the migration simple: we're reorganizing, not rewriting.

---

## Migration Plan

### Phase 1: Create CLI Package

1. Add Click dependency: `uv add click`
2. Create `knos/` package structure
3. Implement `cli.py` with all commands
4. Move logic from scripts into command modules
5. Register entry point in `pyproject.toml`
6. Test: `uv run knos`, `uv run knos today`, etc.

### Phase 2: Deprecate Old Scripts

1. Update old scripts to print deprecation warning + delegate to new CLI:
   ```python
   #!/usr/bin/env -S uv run python3
   import sys
   import os
   print("DEPRECATED: Use 'knos today' instead", file=sys.stderr)
   os.execvp("uv", ["uv", "run", "knos", "today"])
   ```
2. Update documentation to reference new CLI
3. Keep deprecated scripts for one release cycle

### Phase 3: Remove Old Scripts

1. Delete `today`, `study`, `drill`, `read` from project root
2. Update all docs, README, help text
3. Clean commit

---

## Open Questions

### 1. CLI Name

Options:
- `knos` - Matches project name "Knowledge OS", short
- `kos` - Even shorter, but less clear
- `study` - Descriptive but generic
- `phd` - Matches original "PHD Study" naming

**Recommendation**: `knos` - distinctive, memorable, matches repo name.

### 2. Should `knos` require `uv run`?

With entry point registration, users run: `uv run knos`

Alternative: Create a shell wrapper script that handles this:
```bash
#!/bin/bash
# ./knos (shell script in project root)
exec uv run python -m knos.cli "$@"
```

This allows `./knos` to work directly, but adds another file.

**Recommendation**: Just use `uv run knos`. It's explicit and consistent with uv-managed projects.

### 3. Alias for Common Commands?

Should we support shortcuts?
- `knos t` → `knos today`
- `knos d` → `knos drill`
- `knos r` → `knos read`

Click supports this via command aliases. Adds convenience but also complexity.

**Recommendation**: Defer. Add if usage patterns show demand.

### 4. Config Subcommand?

Future consideration: `knos config` for managing settings (LLM provider, voices, etc.)

**Recommendation**: Out of scope for initial implementation. Add when needed.

---

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "typer>=0.9.0",
]
```

Note: Typer depends on Click, so Click will be installed automatically.

---

## Testing

1. **Manual testing**: Run each command, verify output matches old scripts
2. **Help text**: Verify `--help` works at all levels
3. **Error handling**: Test with invalid arguments, missing files
4. **TUI launch**: Verify all three TUIs launch correctly

---

## Success Criteria

- [x] `uv run knos` launches study TUI
- [x] `uv run knos today` prints dashboard
- [x] `uv run knos drill` launches drill TUI
- [x] `uv run knos read` launches reader TUI
- [x] `uv run knos read extract <id>` extracts material
- [x] `uv run knos read list` lists materials
- [x] `uv run knos progress` generates report
- [x] `uv run knos --help` shows all commands
- [x] Old scripts removed from project root
- [x] Documentation updated

---

## Timeline Estimate

Not providing time estimates per project guidelines. Implementation order:

1. Add Click, create package structure
2. Implement core commands (today, study, drill)
3. Implement read command group
4. Test all paths
5. Deprecate old scripts
6. Update docs
7. Remove old scripts
