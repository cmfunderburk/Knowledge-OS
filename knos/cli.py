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
    help="""Reading companion - seminar-style dialogue with texts.

Setup:
  1. Place PDF in reader/sources/<material-id>/source.pdf
  2. Register in reader/content_registry.yaml with chapter page ranges
  3. Run: knos read → select material → select chapter

Registration can be done manually or with AI tools (e.g. Claude Code).
Chapter page numbers are 1-indexed PDF pages, not book page numbers.

Example registry entry:
  materials:
    my-book:
      title: "Book Title"
      author: "Author Name"
      source: "reader/sources/my-book/source.pdf"
      structure:
        chapters:
          - { num: 1, title: "Introduction", pages: [1, 20] }
""",
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


@read_app.command("list")
def read_list(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List registered materials."""
    from knos.commands.read import run_list
    run_list(json_output=json_output)


@read_app.command("info")
def read_info(
    material_id: str = typer.Argument(..., help="Material ID to get info for"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show detailed info about a material."""
    from knos.commands.read import run_info
    run_info(material_id, json_output=json_output)


@read_app.command("clear")
def read_clear(
    material_id: str = typer.Argument(..., help="Material ID (or 'ALL' for all materials)"),
    content: Optional[str] = typer.Argument(None, help="Chapter number (e.g., '1') or appendix ID (e.g., 'A')"),
) -> None:
    """Clear session data for a material."""
    from knos.commands.read import run_clear
    run_clear(material_id, content)


@read_app.command("test")
def read_test() -> None:
    """Test LLM provider configuration."""
    from knos.commands.read import run_test_llm
    run_test_llm()


@read_app.command("export")
def read_export(
    material_id: str = typer.Argument(..., help="Material ID to export"),
    content: Optional[str] = typer.Argument(None, help="Chapter number (e.g., '1') or appendix ID (e.g., 'A')"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file (default: stdout)"),
) -> None:
    """Export a session transcript to markdown."""
    from knos.commands.read import run_export
    run_export(material_id, content, output)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
