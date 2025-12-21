"""
EPUB parsing for the reader module.

Provides on-demand chapter extraction with token-efficient text output.
"""
from pathlib import Path
from dataclasses import dataclass
import warnings

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# Suppress XML-as-HTML warning (EPUBs use XHTML which works fine with lxml)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


@dataclass
class Chapter:
    """A chapter or section from an EPUB."""
    num: int
    title: str
    href: str  # Reference to content file


@dataclass
class EpubStructure:
    """Parsed structure of an EPUB file."""
    title: str
    author: str
    chapters: list[Chapter]


def parse_epub_structure(epub_path: Path) -> EpubStructure:
    """
    Parse an EPUB file and extract its structure.

    Returns chapter/book level divisions suitable for the Reader.
    Strategy:
    1. First look for major divisions (Books, Parts, Volumes) with children
    2. If none found, look for individual CHAPTER entries (flat structure)

    Args:
        epub_path: Path to the EPUB file

    Returns:
        EpubStructure with title, author, and chapter list
    """
    book = epub.read_epub(str(epub_path))

    # Get metadata
    title = book.get_metadata('DC', 'title')
    title = title[0][0] if title else "Unknown"

    author = book.get_metadata('DC', 'creator')
    author = author[0][0] if author else "Unknown"

    chapters = []

    # Strategy 1: Look for major divisions (sections with children)
    chapter_num = 0
    for item in book.toc:
        if isinstance(item, tuple):
            section, children = item
            if _is_major_division(section.title):
                chapter_num += 1
                chapters.append(Chapter(
                    num=chapter_num,
                    title=section.title,
                    href=section.href.split('#')[0]
                ))

    # Strategy 2: If no major divisions, look for CHAPTER entries (flat ToC)
    if not chapters:
        chapters = _extract_flat_chapters(book.toc)

    return EpubStructure(title=title, author=author, chapters=chapters)


def _extract_flat_chapters(toc_items, parent_children=None) -> list[Chapter]:
    """
    Extract chapters from a flat or semi-flat ToC structure.

    Handles EPUBs like Don Quixote where chapters are listed directly
    or nested under non-content sections.
    """
    chapters = []
    chapter_num = 0

    def process_items(items):
        nonlocal chapter_num
        for item in items:
            if isinstance(item, tuple):
                section, children = item
                # Check if this section contains chapters
                process_items(children)
            elif isinstance(item, epub.Link):
                if _is_chapter_entry(item.title):
                    chapter_num += 1
                    chapters.append(Chapter(
                        num=chapter_num,
                        title=_clean_chapter_title(item.title),
                        href=item.href.split('#')[0]
                    ))

    process_items(toc_items)
    return chapters


def _is_chapter_entry(title: str) -> bool:
    """Check if a ToC entry is a chapter (not frontmatter/backmatter)."""
    title_upper = title.upper().strip()

    # Match "CHAPTER I", "CHAPTER 1", "CHAPTER ONE", etc.
    if title_upper.startswith('CHAPTER '):
        return True

    return False


def _clean_chapter_title(title: str) -> str:
    """Clean up verbose chapter titles for display."""
    # Truncate very long titles (common in Don Quixote)
    if len(title) > 80:
        # Find a good break point
        if '. ' in title[:80]:
            return title[:title.index('. ', 0, 80) + 1]
        elif ', ' in title[:80]:
            return title[:title.index(', ', 0, 80)]
        else:
            return title[:77] + "..."
    return title


def _is_major_division(title: str) -> bool:
    """
    Check if a ToC entry is a major content division (Book, Part, Volume).

    For classic literature, we want Book/Part/Volume level, not chapters.
    """
    title_upper = title.upper().strip()

    # Match patterns like "BOOK I", "PART ONE", "VOLUME 1", etc.
    major_patterns = [
        'BOOK ',
        'PART ',
        'VOLUME ',
    ]

    for pattern in major_patterns:
        if title_upper.startswith(pattern):
            return True

    return False


def _is_content_section(title: str) -> bool:
    """
    Check if a ToC entry is actual content (not frontmatter/backmatter).

    Filters out: title pages, copyright, license, notes, etc.
    """
    title_lower = title.lower()

    # Skip common non-content sections
    skip_patterns = [
        'contents', 'table of contents',
        'title', 'copyright', 'license',
        'colophon', 'imprint', 'dedication',
        'acknowledgment', 'about',
        'gutenberg', 'project gutenberg',
        'notes',  # Often endnotes we don't want as separate chapter
    ]

    for pattern in skip_patterns:
        if pattern in title_lower:
            return False

    return True


def extract_chapter_text(epub_path: Path, chapter: Chapter) -> str:
    """
    Extract clean text from a chapter.

    Produces token-efficient output:
    - Strips all HTML tags
    - Preserves paragraph structure (single blank lines)
    - Removes excessive whitespace
    - Keeps section headers as plain text

    Args:
        epub_path: Path to the EPUB file
        chapter: Chapter object with href to content

    Returns:
        Clean text content
    """
    book = epub.read_epub(str(epub_path))

    # Find the content item
    for item in book.get_items():
        if item.get_name().endswith(chapter.href) or chapter.href in item.get_name():
            html = item.get_content().decode('utf-8')
            return _html_to_clean_text(html)

    raise ValueError(f"Chapter content not found: {chapter.href}")


def extract_chapter_by_num(epub_path: Path, chapter_num: int) -> tuple[str, str]:
    """
    Extract a chapter by its number.

    Args:
        epub_path: Path to the EPUB file
        chapter_num: 1-indexed chapter number

    Returns:
        Tuple of (title, text)
    """
    structure = parse_epub_structure(epub_path)

    for chapter in structure.chapters:
        if chapter.num == chapter_num:
            text = extract_chapter_text(epub_path, chapter)
            return chapter.title, text

    raise ValueError(f"Chapter {chapter_num} not found")


def _html_to_clean_text(html: str) -> str:
    """
    Convert HTML to clean, token-efficient text.

    Strategy:
    - Use BeautifulSoup to parse
    - Extract text with paragraph preservation
    - Collapse excessive whitespace
    - Keep headers as emphasized text
    """
    soup = BeautifulSoup(html, 'lxml')

    # Remove script, style, and nav elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()

    # Process the body
    body = soup.find('body') or soup

    lines = []
    for element in body.descendants:
        if element.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            # Add headers with emphasis
            text = element.get_text(strip=True)
            if text:
                lines.append(f"\n## {text}\n")
        elif element.name == 'p':
            text = element.get_text(strip=True)
            if text:
                lines.append(text)

    # Join with single blank lines between paragraphs
    text = '\n\n'.join(lines)

    # Clean up excessive whitespace
    text = _normalize_whitespace(text)

    return text


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure."""
    import re

    # Collapse multiple blank lines to single
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces to single
    text = re.sub(r'[ \t]+', ' ', text)

    # Clean up space around newlines
    text = re.sub(r' *\n *', '\n', text)

    return text.strip()


def get_chapter_count(epub_path: Path) -> int:
    """Get the number of chapters in an EPUB."""
    structure = parse_epub_structure(epub_path)
    return len(structure.chapters)


def list_chapters(epub_path: Path) -> list[tuple[int, str]]:
    """
    List all chapters in an EPUB.

    Returns:
        List of (chapter_num, title) tuples
    """
    structure = parse_epub_structure(epub_path)
    return [(ch.num, ch.title) for ch in structure.chapters]
