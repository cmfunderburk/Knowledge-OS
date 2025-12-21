"""
Content extraction and management for the reader module.

Uses pymupdf4llm for improved extraction of formatted text including:
- Bold/italic preservation
- Better layout detection
- Improved handling of mathematical notation

Falls back to raw pymupdf extraction for pages with many images
(e.g., figure-heavy pages with embedded sprites).
"""
from pathlib import Path
from typing import TypeAlias

import pymupdf
import pymupdf4llm

from reader.config import get_material, READER_DIR


SOURCES_DIR = READER_DIR / "sources"

# Pages with more than this many images use fallback extraction
MAX_IMAGES_PER_PAGE = 20

# Content identifier: integer for chapters (1, 2, 3), string for appendices ("A", "B")
ContentId: TypeAlias = int | str


def get_content_info(material_id: str, content_id: ContentId) -> dict | None:
    """
    Look up content (chapter or appendix) by ID.

    Args:
        material_id: The material identifier
        content_id: Chapter number (int) or appendix ID (str like "A", "B")

    Returns:
        Dict with 'title' and 'pages' keys, or None if not found
    """
    material = get_material(material_id)
    structure = material.get("structure", {})

    if isinstance(content_id, int):
        # Look up chapter by number
        chapters = structure.get("chapters", [])
        for ch in chapters:
            if ch["num"] == content_id:
                return {"title": ch["title"], "pages": ch["pages"]}
    else:
        # Look up appendix by ID
        appendices = structure.get("appendices", [])
        for app in appendices:
            if app["id"] == content_id:
                return {"title": app["title"], "pages": app["pages"]}

    return None


def format_content_id(content_id: ContentId) -> str:
    """Format a content ID for display (e.g., 'Chapter 1' or 'Appendix A')."""
    if isinstance(content_id, int):
        return f"Chapter {content_id}"
    else:
        return f"Appendix {content_id}"


def get_source_path(material_id: str) -> Path:
    """
    Get the full path to the source file for a material.

    Uses the source field from the registry.

    Args:
        material_id: The material identifier

    Returns:
        Path to the source file (PDF or EPUB)
    """
    material = get_material(material_id)
    # Source paths in registry are relative to repo root
    return READER_DIR.parent / material["source"]


def get_source_format(material_id: str) -> str:
    """
    Return 'pdf' or 'epub' based on source file extension.

    Args:
        material_id: The material identifier

    Returns:
        'pdf' or 'epub'
    """
    source_path = get_source_path(material_id)
    return "pdf" if source_path.suffix.lower() == ".pdf" else "epub"


def get_chapter_pdf(material_id: str, content_id: ContentId) -> bytes:
    """
    Extract content page range as PDF bytes (for PDF sources only).

    Args:
        material_id: The material identifier
        content_id: Chapter number (int) or appendix ID (str)

    Returns:
        PDF bytes for the content page range

    Raises:
        ValueError: If source PDF not found or content not found
    """
    source_path = get_source_path(material_id)

    if not source_path.exists():
        raise ValueError(f"Source PDF not found: {source_path}")

    content_info = get_content_info(material_id, content_id)
    if not content_info:
        raise ValueError(f"{format_content_id(content_id)} not found in material '{material_id}'")

    start, end = content_info["pages"]

    doc = pymupdf.open(source_path)
    new_doc = pymupdf.open()
    # insert_pdf uses 0-indexed pages, end is inclusive
    new_doc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
    pdf_bytes = new_doc.tobytes()
    doc.close()
    new_doc.close()
    return pdf_bytes


def _find_problematic_pages(doc: pymupdf.Document, pages: list[int]) -> set[int]:
    """Find pages that have too many images for pymupdf4llm."""
    problematic = set()
    for page_num in pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        if len(page.get_images()) > MAX_IMAGES_PER_PAGE:
            problematic.add(page_num)
    return problematic


def _extract_pages_raw(doc: pymupdf.Document, pages: list[int]) -> str:
    """Fallback extraction using raw pymupdf."""
    parts = []
    for page_num in pages:
        if page_num >= len(doc):
            continue
        text = doc[page_num].get_text()
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def extract_pages(source_path: Path, page_range: list[int]) -> str:
    """
    Extract text from a PDF page range.

    Uses pymupdf4llm for batches of safe pages, with fallback to raw extraction
    for pages that have many embedded images (which cause pymupdf4llm to hang).

    Args:
        source_path: Path to the PDF file
        page_range: [start_page, end_page] (1-indexed, inclusive)

    Returns:
        Extracted text as markdown-formatted string
    """
    start_page, end_page = page_range
    # Convert to 0-indexed
    all_pages = list(range(start_page - 1, end_page))

    doc = pymupdf.open(source_path)
    source_str = str(source_path)

    # Find which pages are problematic
    problematic = _find_problematic_pages(doc, all_pages)

    # Process in order, batching safe pages together
    parts = []
    safe_batch = []

    def flush_safe_batch():
        if safe_batch:
            text = pymupdf4llm.to_markdown(source_str, pages=safe_batch)
            if text.strip():
                parts.append(text)
            safe_batch.clear()

    for page_num in all_pages:
        if page_num >= len(doc):
            break

        if page_num in problematic:
            # Flush any pending safe pages first
            flush_safe_batch()
            # Extract this page with fallback
            text = doc[page_num].get_text()
            if text.strip():
                parts.append(text)
        else:
            safe_batch.append(page_num)

    # Flush remaining safe pages
    flush_safe_batch()

    doc.close()
    return "\n\n".join(parts)


def load_chapter(material_id: str, chapter_num: int) -> str:
    """
    Load chapter content from EPUB (on-demand extraction).

    Args:
        material_id: The material identifier
        chapter_num: The chapter number

    Returns:
        The chapter content as clean text

    Raises:
        ValueError: If EPUB or chapter not found
    """
    from reader.epub import extract_chapter_by_num

    epub_path = get_source_path(material_id)

    if not epub_path.exists():
        raise ValueError(f"EPUB not found: {epub_path}")

    title, text = extract_chapter_by_num(epub_path, chapter_num)
    return text


def get_chapter_text(material_id: str, content_id: ContentId) -> str:
    """
    Get content as text for any format (on-demand extraction).

    For EPUBs: Extracts chapter from EPUB structure
    For PDFs: Extracts text from the PDF page range

    Args:
        material_id: The material identifier
        content_id: Chapter number (int) or appendix ID (str)

    Returns:
        Content as text

    Raises:
        ValueError: If source not found
    """
    source_format = get_source_format(material_id)

    if source_format == "epub":
        if isinstance(content_id, int):
            return load_chapter(material_id, content_id)
        else:
            raise ValueError("EPUB appendices not yet supported")
    else:
        # PDF: extract text on-demand
        source_path = get_source_path(material_id)

        if not source_path.exists():
            raise ValueError(f"Source PDF not found: {source_path}")

        content_info = get_content_info(material_id, content_id)
        if not content_info:
            raise ValueError(f"{format_content_id(content_id)} not found")

        return extract_pages(source_path, content_info["pages"])


def list_extracted_chapters(material_id: str) -> list[int]:
    """
    List which chapters are available for a material.

    For PDFs: All chapters from registry if source exists
    For EPUBs: All chapters from EPUB structure if source exists

    Returns:
        List of chapter numbers that are available
    """
    source_path = get_source_path(material_id)
    if not source_path.exists():
        return []

    # PDF: all chapters from registry
    if source_path.suffix.lower() == ".pdf":
        material = get_material(material_id)
        chapters = material.get("structure", {}).get("chapters", [])
        return sorted(c["num"] for c in chapters)

    # EPUB: get chapters from EPUB structure
    if source_path.suffix.lower() == ".epub":
        from reader.epub import list_chapters
        return [num for num, title in list_chapters(source_path)]

    return []


def list_extracted_appendices(material_id: str) -> list[str]:
    """
    List which appendices are available for a material.

    For PDFs: All appendices if source exists
    For EPUBs: Not yet supported

    Returns:
        List of appendix IDs (e.g., ["A", "B", "C"])
    """
    source_path = get_source_path(material_id)
    if not source_path.exists():
        return []

    # PDF: all appendices from registry
    if source_path.suffix.lower() == ".pdf":
        material = get_material(material_id)
        appendices = material.get("structure", {}).get("appendices", [])
        return [a["id"] for a in appendices]

    # EPUB: appendices not yet supported
    return []


def list_all_content(material_id: str) -> tuple[list[dict], list[dict]]:
    """
    List all available content (chapters and appendices) for a material.

    Uses the source path from the registry to find the file.

    Returns:
        Tuple of (chapters, appendices) where each is a list of dicts
        with 'num'/'id' and 'title' keys
    """
    source_path = get_source_path(material_id)

    if not source_path.exists():
        return [], []

    # PDF: use registry structure
    if source_path.suffix.lower() == ".pdf":
        material = get_material(material_id)
        structure = material.get("structure", {})
        chapters = structure.get("chapters", [])
        appendices = structure.get("appendices", [])
        return chapters, appendices

    # EPUB: get structure from EPUB itself
    if source_path.suffix.lower() == ".epub":
        from reader.epub import list_chapters
        chapters = [{"num": num, "title": title} for num, title in list_chapters(source_path)]
        return chapters, []

    # Unknown format
    return [], []
