"""
Knowledge OS - Unified CLI entry point.

Usage:
    knos              # Launch study TUI (default)
    knos today        # Print CLI dashboard
    knos study        # Launch study TUI
    knos drill        # Launch drill TUI
    knos read         # Launch reader TUI
    knos progress     # Generate progress report
"""
from typing import Optional

import typer

from knos import __version__

app = typer.Typer(
    help="Knowledge OS - Study system for self-directed learning.",
    no_args_is_help=False,
    add_completion=False,
)

# Reader subcommand group
read_app = typer.Typer(
    help="Reading companion - seminar-style dialogue with texts.",
    no_args_is_help=False,
)
app.add_typer(read_app, name="read")


def version_callback(value: bool) -> None:
    if value:
        print(f"knos {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit."
    ),
) -> None:
    """Default behavior: launch study TUI if no command given."""
    if ctx.invoked_subcommand is None:
        from knos.commands.study import run_study
        run_study()


@app.command()
def today() -> None:
    """Show today's study plan (CLI dashboard)."""
    from knos.commands.today import run_today
    run_today()


@app.command()
def study() -> None:
    """Launch the study TUI."""
    from knos.commands.study import run_study
    run_study()


@app.command()
def drill() -> None:
    """Launch the drill TUI."""
    from knos.commands.drill import run_drill
    run_drill()


@app.command()
def progress() -> None:
    """Generate PROGRESS.md report."""
    from knos.commands.progress import run_progress
    run_progress()


# --- Reader subcommands ---

@read_app.callback(invoke_without_command=True)
def read_main(ctx: typer.Context) -> None:
    """Default: launch reader TUI if no subcommand given."""
    if ctx.invoked_subcommand is None:
        from knos.commands.read import run_read_tui
        run_read_tui()


@read_app.command("extract")
def read_extract(
    material_id: str = typer.Argument(..., help="Material ID to extract"),
) -> None:
    """Extract chapters from a registered material."""
    from knos.commands.read import run_extract
    run_extract(material_id)


@read_app.command("list")
def read_list() -> None:
    """List registered materials."""
    from knos.commands.read import run_list
    run_list()


@read_app.command("clear")
def read_clear(
    material_id: str = typer.Argument(..., help="Material ID (or 'ALL' for all materials)"),
    chapter: Optional[int] = typer.Argument(None, help="Specific chapter number to clear"),
) -> None:
    """Clear session data for a material."""
    from knos.commands.read import run_clear
    run_clear(material_id, chapter)


@read_app.command("test")
def read_test() -> None:
    """Test LLM provider configuration."""
    from knos.commands.read import run_test_llm
    run_test_llm()


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
