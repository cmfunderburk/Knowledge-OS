"""
Prompt template loading and rendering for the reader module.
"""
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Initialize Jinja2 environment
_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_prompt(name: str) -> str:
    """
    Load a raw prompt template by name.

    Args:
        name: Template name without extension (e.g., "base", "socratic")

    Returns:
        Raw template content
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}.md")
    return path.read_text()


def render_prompt(name: str, **context: Any) -> str:
    """
    Render a prompt template with the given context.

    Args:
        name: Template name without extension (e.g., "base", "socratic")
        **context: Variables to pass to the template

    Returns:
        Rendered prompt string
    """
    template = _env.get_template(f"{name}.md")
    return template.render(**context)


def build_system_prompt(
    mode: str,
    book_title: str,
    chapter_title: str,
    session_phase: str = "dialogue",
    prior_session_summary: str | None = None,
    captured_insights: list[str] | None = None,
) -> str:
    """
    Build system prompt for a reading session.

    Chapter content is provided separately via cache - this prompt does not
    include it inline.

    Args:
        mode: Dialogue mode ("socratic", "clarify", "challenge", "teach", "quiz")
        book_title: Title of the book being read
        chapter_title: Title of the current chapter
        session_phase: Current phase ("pre_reading", "dialogue", "synthesis")
        prior_session_summary: Optional summary of previous sessions
        captured_insights: Optional list of insights captured this session

    Returns:
        System prompt string
    """
    base = render_prompt(
        "base",
        book_title=book_title,
        chapter_title=chapter_title,
        session_phase=session_phase,
        prior_session_summary=prior_session_summary,
        captured_insights=captured_insights,
    )

    try:
        mode_additions = render_prompt(mode)
    except FileNotFoundError:
        mode_additions = ""

    if mode_additions:
        return f"{base}\n\n{mode_additions}"
    return base


# Available dialogue modes
MODES = ["socratic", "clarify", "challenge", "teach", "quiz"]
