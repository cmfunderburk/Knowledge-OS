"""Shared utilities for generating Knowledge-OS drill cards."""

from pathlib import Path
from textwrap import dedent

# Default output directory for generated cards
DEFAULT_OUTPUT_DIR = Path("/home/cmf/Dropbox/Apps/KnOS/solutions/wip")


def generate_card(
    filename: str,
    title: str,
    source: str,
    context: str,
    code: str,
    code_lang: str = "python",
    key_details: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """Generate a Knowledge-OS drill card.

    Args:
        filename: Output filename (e.g., "algorithm_regex_pattern.md")
        title: Card title (e.g., "Tokenization Regex Pattern")
        source: Source attribution (e.g., "Build a LLM from Scratch, Chapter 2.2")
        context: Explanation shown during drill (visible context)
        code: The code block to drill (must be typed 100% accurately)
        code_lang: Language for syntax highlighting (default: python)
        key_details: Optional bullet points about key implementation details
        output_dir: Where to write the card

    Returns:
        Path to the generated card file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Build the card content
    lines = [
        f"# {title}",
        "",
        f"**Source:** {source}",
        "",
        "## Context",
        context.strip(),
        "",
        "## Implementation",
        f"```{code_lang}",
        code.rstrip(),  # No trailing whitespace in code blocks
        "```",
    ]

    if key_details:
        lines.extend([
            "",
            "## Key Details",
            key_details.strip(),
        ])

    # Ensure file ends with single newline
    content = "\n".join(lines) + "\n"

    output_path.write_text(content)
    return output_path


def print_card_generated(path: Path) -> None:
    """Print confirmation that a card was generated."""
    print(f"  -> Generated: {path.name}")


def print_section(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)
