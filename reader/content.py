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

import pymupdf
import pymupdf4llm

from reader.config import get_material, READER_DIR


EXTRACTED_DIR = READER_DIR / "extracted"

# Pages with more than this many images use fallback extraction
MAX_IMAGES_PER_PAGE = 20


def get_source_format(material_id: str) -> str:
    """
    Return 'pdf' or 'epub' based on source file extension.

    Args:
        material_id: The material identifier

    Returns:
        'pdf' or 'epub'
    """
    material = get_material(material_id)
    source = material["source"]
    return "pdf" if source.lower().endswith(".pdf") else "epub"


def get_chapter_pdf(material_id: str, chapter_num: int) -> bytes:
    """
    Extract chapter page range as PDF bytes (for PDF sources only).

    Args:
        material_id: The material identifier
        chapter_num: The chapter number

    Returns:
        PDF bytes for the chapter page range

    Raises:
        ValueError: If source PDF not found in extracted/
    """
    material = get_material(material_id)
    source_path = EXTRACTED_DIR / material_id / "source.pdf"

    if not source_path.exists():
        raise ValueError(
            f"Source PDF not found. Run: ./read --extract {material_id}"
        )

    chapters = material.get("structure", {}).get("chapters", [])
    chapter = next((c for c in chapters if c["num"] == chapter_num), None)
    if not chapter:
        raise ValueError(f"Chapter {chapter_num} not found in material '{material_id}'")

    start, end = chapter["pages"]

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


def extract_material(material_id: str) -> None:
    """
    Extract/copy material to reader/extracted/.

    For PDFs: Copies source to extracted/<material>/source.pdf
    For EPUBs: Extracts text to extracted/<material>/ch<N>.md

    Args:
        material_id: The material identifier from content_registry.yaml
    """
    material = get_material(material_id)

    # Resolve source path relative to repo root
    repo_root = READER_DIR.parent
    source_path = repo_root / material["source"]

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    # Create output directory
    output_dir = EXTRACTED_DIR / material_id
    output_dir.mkdir(parents=True, exist_ok=True)

    source_format = get_source_format(material_id)

    if source_format == "pdf":
        # Copy PDF source for direct use
        import shutil
        dest_path = output_dir / "source.pdf"
        shutil.copy2(source_path, dest_path)
        print(f"Copied PDF to: {dest_path}")
        print("Chapters will be sliced on-demand during reading sessions.")
    else:
        # EPUB: extract text to markdown
        chapters = material.get("structure", {}).get("chapters", [])
        if not chapters:
            raise ValueError(f"No chapters defined for material '{material_id}'")

        print(f"Extracting {len(chapters)} chapters from: {source_path.name}")

        for chapter in chapters:
            chapter_num = chapter["num"]
            title = chapter["title"]
            pages = chapter["pages"]

            print(f"  Chapter {chapter_num}: {title} (pages {pages[0]}-{pages[1]})")

            content = extract_pages(source_path, pages)

            # Create markdown file with chapter header
            output_path = output_dir / f"ch{chapter_num:02d}.md"
            md_content = f"# Chapter {chapter_num}: {title}\n\n{content}"
            output_path.write_text(md_content)

        print(f"Extracted to: {output_dir}")


def load_chapter(material_id: str, chapter_num: int) -> str:
    """
    Load a pre-extracted chapter (EPUB only).

    Args:
        material_id: The material identifier
        chapter_num: The chapter number

    Returns:
        The chapter content as a string

    Raises:
        ValueError: If the chapter hasn't been extracted
    """
    path = EXTRACTED_DIR / material_id / f"ch{chapter_num:02d}.md"

    if not path.exists():
        raise ValueError(
            f"Chapter not extracted. Run: ./read --extract {material_id}"
        )

    return path.read_text()


def get_chapter_text(material_id: str, chapter_num: int) -> str:
    """
    Get chapter content as text for any format.

    For EPUBs: Returns pre-extracted markdown text
    For PDFs: Extracts text from the PDF page range on-demand

    Args:
        material_id: The material identifier
        chapter_num: The chapter number

    Returns:
        Chapter content as text

    Raises:
        ValueError: If source not found
    """
    source_format = get_source_format(material_id)

    if source_format == "epub":
        return load_chapter(material_id, chapter_num)
    else:
        # PDF: extract text on-demand
        material = get_material(material_id)
        source_path = EXTRACTED_DIR / material_id / "source.pdf"

        if not source_path.exists():
            raise ValueError(
                f"Source PDF not found. Run: ./read --extract {material_id}"
            )

        chapters = material.get("structure", {}).get("chapters", [])
        chapter = next((c for c in chapters if c["num"] == chapter_num), None)
        if not chapter:
            raise ValueError(f"Chapter {chapter_num} not found")

        return extract_pages(source_path, chapter["pages"])


def list_extracted_chapters(material_id: str) -> list[int]:
    """
    List which chapters are available for a material.

    For PDFs: All chapters if source.pdf exists
    For EPUBs: Chapters with extracted .md files

    Returns:
        List of chapter numbers that are available
    """
    material_dir = EXTRACTED_DIR / material_id
    if not material_dir.exists():
        return []

    # PDF: if source.pdf exists, all chapters are available
    if (material_dir / "source.pdf").exists():
        material = get_material(material_id)
        chapters = material.get("structure", {}).get("chapters", [])
        return sorted(c["num"] for c in chapters)

    # EPUB: check for extracted .md files
    chapters = []
    for path in material_dir.glob("ch*.md"):
        try:
            num = int(path.stem[2:])
            chapters.append(num)
        except ValueError:
            continue

    return sorted(chapters)
