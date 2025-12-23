"""
Reader commands - TUI and CLI utilities.

Provides the reader TUI and various utility commands for managing
reading materials and sessions.
"""
import shutil
import sys
from typing import Optional


def run_read_tui() -> None:
    """Launch the reader TUI."""
    try:
        from knos.tui.app import ReaderApp
        app = ReaderApp()
        app.run()
    except ImportError as e:
        print(f"Error starting reader TUI: {e}")
        print("Try running: uv run knos read")
        sys.exit(1)


def run_list(json_output: bool = False) -> None:
    """List all registered materials."""
    import json
    from knos.reader.config import load_registry, get_material_type
    from knos.reader.content import list_all_content

    registry = load_registry()
    if not registry.get("materials"):
        if json_output:
            print(json.dumps({"materials": []}))
        else:
            print("No materials registered. Run 'knos init' or add materials to config/content.yaml")
        return

    if json_output:
        materials = []
        for material_id, info in registry["materials"].items():
            material_type = get_material_type(material_id)
            entry = {
                "id": material_id,
                "title": info.get("title", material_id),
                "author": info.get("author", "Unknown"),
                "type": material_type,
                "source": info.get("source", ""),
            }
            if material_type != "article":
                chapters, appendices = list_all_content(material_id)
                entry["chapter_count"] = len(chapters)
                entry["appendix_count"] = len(appendices)
            materials.append(entry)
        print(json.dumps({"materials": materials}, indent=2))
        return

    print("\nRegistered Materials:\n")
    for material_id, info in registry["materials"].items():
        title = info.get("title", material_id)
        author = info.get("author", "Unknown")
        material_type = get_material_type(material_id)

        print(f"  {material_id}")
        print(f"    {title} ({author})")

        if material_type == "article":
            print("    article")
        else:
            # Get chapter count from actual content (works for both PDF and EPUB)
            chapters, appendices = list_all_content(material_id)
            chapter_count = len(chapters)
            print(f"    {chapter_count} chapters")
        print()


def run_info(material_id: str, json_output: bool = False) -> None:
    """Show detailed info about a material."""
    import json
    from knos.reader.config import load_registry, get_material_type
    from knos.reader.content import list_all_content, get_source_path

    registry = load_registry()
    materials = registry.get("materials", {})

    if material_id not in materials:
        if json_output:
            print(json.dumps({"error": f"Material '{material_id}' not found"}))
        else:
            print(f"Error: Material '{material_id}' not found in registry")
        sys.exit(1)

    info = materials[material_id]
    material_type = get_material_type(material_id)
    source_path = get_source_path(material_id)
    source_exists = source_path.exists()

    if json_output:
        result = {
            "id": material_id,
            "title": info.get("title", material_id),
            "author": info.get("author", "Unknown"),
            "type": material_type,
            "source": info.get("source", ""),
            "source_exists": source_exists,
        }
        if material_type != "article":
            chapters, appendices = list_all_content(material_id)
            result["chapters"] = chapters
            result["appendices"] = appendices
        print(json.dumps(result, indent=2))
        return

    # Human-readable output
    title = info.get("title", material_id)
    author = info.get("author", "Unknown")

    print(f"\n{title}")
    print(f"  Author: {author}")
    print(f"  ID: {material_id}")
    print(f"  Type: {material_type}")
    print(f"  Source: {info.get('source', 'N/A')}")
    print(f"  Source exists: {'Yes' if source_exists else 'No'}")

    if material_type != "article":
        chapters, appendices = list_all_content(material_id)
        print(f"\n  Chapters ({len(chapters)}):")
        for ch in chapters:
            print(f"    {ch['num']}. {ch['title']}")
        if appendices:
            print(f"\n  Appendices ({len(appendices)}):")
            for app in appendices:
                print(f"    {app['id']}. {app['title']}")
    print()


def run_clear(material_id: str, content: Optional[str] = None) -> None:
    """Clear session data for a material (or all materials if 'ALL').

    Args:
        material_id: Material ID or 'ALL' to clear everything
        content: Chapter number (e.g., '1') or appendix ID (e.g., 'A')
    """
    from knos.reader.session import SESSIONS_DIR as sessions_root, _content_id_to_prefix

    if material_id.upper() == "ALL":
        # Clear everything
        if not sessions_root.exists():
            print("No sessions found.")
            return
        materials = list(sessions_root.iterdir())
        if not materials:
            print("No sessions found.")
            return
        shutil.rmtree(sessions_root)
        sessions_root.mkdir()
        print(f"Cleared all sessions ({len(materials)} materials)")
        return

    sessions_dir = sessions_root / material_id

    if not sessions_dir.exists():
        print(f"No sessions found for: {material_id}")
        return

    if content is not None:
        # Parse content ID (integer for chapters, string for appendices)
        try:
            content_id: int | str = int(content)
            label = f"chapter {content_id}"
        except ValueError:
            content_id = content.upper()
            label = f"appendix {content_id}"

        prefix = _content_id_to_prefix(content_id)
        files = [
            sessions_dir / f"{prefix}.jsonl",
            sessions_dir / f"{prefix}.meta.json",
        ]
        deleted = 0
        for f in files:
            if f.exists():
                f.unlink()
                deleted += 1
        if deleted:
            print(f"Cleared session for {material_id} {label}")
        else:
            print(f"No session found for {material_id} {label}")
    else:
        # Clear all sessions for this material
        shutil.rmtree(sessions_dir)
        print(f"Cleared all sessions for: {material_id}")


def run_test_llm() -> None:
    """Test LLM provider configuration."""
    from knos.reader.llm import get_provider

    print("Testing LLM provider...")
    try:
        provider = get_provider()
        print(f"  Provider: {provider.__class__.__name__}")
        if hasattr(provider, "model_name"):
            print(f"  Model: {provider.model_name}")
        elif hasattr(provider, "model"):
            print(f"  Model: {provider.model}")

        print("\nSending test message...")
        response = provider.chat(
            messages=[{"role": "user", "content": "Say 'Hello from Reader!' and nothing else."}]
        )
        print(f"  Response: {response.text.strip()}")
        print("\nLLM integration working!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_export(material_id: str, content: Optional[str] = None, output: Optional[str] = None) -> None:
    """Export a session transcript to markdown.

    Args:
        material_id: Material ID to export
        content: Chapter number (e.g., '1'), appendix ID (e.g., 'A'), or None for articles
        output: Output file path (default: stdout)
    """
    from knos.reader.config import load_registry, get_material_type
    from knos.reader.session import load_session, load_transcript

    registry = load_registry()
    materials = registry.get("materials", {})

    if material_id not in materials:
        print(f"Error: Material '{material_id}' not found in registry")
        sys.exit(1)

    info = materials[material_id]
    title = info.get("title", material_id)
    author = info.get("author", "Unknown")
    material_type = get_material_type(material_id)

    # Determine content ID
    if material_type == "article":
        content_id: int | str | None = None
    elif content is not None:
        try:
            content_id = int(content)
        except ValueError:
            content_id = content.upper()
    else:
        print("Error: Chapter or appendix required for non-article materials")
        print("Usage: knos read export <material-id> <chapter>")
        sys.exit(1)

    # Load session and transcript
    session = load_session(material_id, content_id)
    if not session:
        print(f"Error: No session found for {material_id}" + (f" chapter {content}" if content else ""))
        sys.exit(1)

    transcript = load_transcript(material_id, content_id)
    if not transcript:
        print(f"Error: Empty transcript for {material_id}" + (f" chapter {content}" if content else ""))
        sys.exit(1)

    # Build markdown
    lines = []
    lines.append(f"# {title}")
    if session.chapter_title and session.chapter_title != title:
        lines.append(f"## {session.chapter_title}")
    lines.append(f"*{author}*")
    lines.append("")
    lines.append(f"*Session started: {session.started.strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    for msg in transcript:
        role = msg.get("role", "unknown")
        content_text = msg.get("content", "")
        mode = msg.get("mode", "")

        if role == "user":
            lines.append("**Reader:**")
        else:
            mode_label = f" *({mode})*" if mode else ""
            lines.append(f"**Tutor{mode_label}:**")

        lines.append("")
        lines.append(content_text)
        lines.append("")

    markdown = "\n".join(lines)

    # Output
    if output:
        from pathlib import Path
        Path(output).write_text(markdown)
        print(f"Exported to: {output}")
    else:
        print(markdown)
