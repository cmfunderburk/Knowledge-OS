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


def build_cache_prompt(
    book_title: str,
    chapter_title: str,
    prior_session_summary: str | None = None,
) -> str:
    """
    Build system prompt for the context cache (mode-agnostic).

    This prompt is cached along with the chapter content. Mode-specific
    instructions are injected into conversation messages instead.

    Args:
        book_title: Title of the book being read
        chapter_title: Title of the current chapter
        prior_session_summary: Optional summary of previous sessions

    Returns:
        System prompt string for caching
    """
    return render_prompt(
        "base",
        book_title=book_title,
        chapter_title=chapter_title,
        prior_session_summary=prior_session_summary,
    )


def get_mode_instruction(mode: str) -> str:
    """
    Get the mode instruction text to inject into conversation.

    Args:
        mode: Dialogue mode name

    Returns:
        Mode instruction text, or empty string if mode not found
    """
    try:
        return load_prompt(mode)
    except FileNotFoundError:
        return ""


# Available dialogue modes
MODES = ["socratic", "clarify", "challenge", "teach", "quiz", "technical", "review"]
